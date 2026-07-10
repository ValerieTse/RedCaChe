from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import ImportSource, Post, ReviewStatus
from app.routers.config import reclassify_posts
from app.services.classifier import classify_title
from app.services.config_service import (
    active_categories,
    classification_defs,
    get_or_create_config,
    update_config,
)


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _post(note_id, title, category="Uncategorized", manual=False, source=ImportSource.REDNOTE):
    return Post(
        note_id=note_id,
        source_url=f"https://www.rednote.com/explore/{note_id}",
        title=title,
        category=category,
        category_is_manual=manual,
        import_source=source.value,
        review_status=ReviewStatus.UNREVIEWED.value,
    )


def test_config_seeds_onboarding_incomplete_for_empty_library():
    db = _session()
    config = get_or_create_config(db)
    assert config.onboarding_completed is False
    assert len(config.selected_category_slugs) > 0


def test_config_seeds_onboarding_complete_when_posts_exist():
    db = _session()
    db.add(_post("n1", "test"))
    db.commit()
    config = get_or_create_config(db)
    assert config.onboarding_completed is True


def test_active_categories_reflect_selection_and_custom():
    db = _session()
    update_config(
        db,
        selected_category_slugs=["Beauty", "Cars"],
        custom_categories=[{"name": "Aquascaping", "keywords": ["水草", "aquascape"]}],
    )
    config = get_or_create_config(db)
    slugs = [c["slug"] for c in active_categories(config)]
    assert "Beauty" in slugs
    assert "Cars" in slugs
    assert "Fashion" not in slugs
    assert "Aquascaping" in slugs
    assert slugs[-1] == "Uncategorized"


def test_custom_category_keywords_drive_classification():
    db = _session()
    update_config(
        db,
        selected_category_slugs=["Beauty"],
        custom_categories=[{"name": "Aquascaping", "keywords": ["水草", "aquascape"]}],
    )
    defs = classification_defs(get_or_create_config(db))
    assert classify_title("我的水草缸造景", defs) == "Aquascaping"
    assert classify_title("no signal here", defs) == "Uncategorized"


def test_custom_category_without_keywords_is_manual_only():
    db = _session()
    update_config(
        db,
        selected_category_slugs=[],
        custom_categories=[{"name": "Misc", "keywords": []}],
    )
    defs = classification_defs(get_or_create_config(db))
    assert all(d["name"] != "Misc" for d in defs)


def test_reclassify_updates_non_manual_and_protects_manual():
    db = _session()
    db.add_all(
        [
            _post("a", "夏季钩织教程"),  # -> Handcraft
            _post("b", "面试简历技巧"),  # -> Work
            _post("c", "手动锁定的帖子", category="Beauty", manual=True),  # protected
        ]
    )
    db.commit()

    result = reclassify_posts(db=db)

    assert result.scanned_count == 2  # manual one excluded
    assert result.updated_count == 2
    by_note = {p.note_id: p.category for p in db.query(Post).all()}
    assert by_note["a"] == "Handcraft"
    assert by_note["b"] == "Work"
    assert by_note["c"] == "Beauty"
