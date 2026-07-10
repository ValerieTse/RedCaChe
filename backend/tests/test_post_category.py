from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Category, Post
from app.routers.posts import update_post_category
from app.schemas import PostCategoryUpdate


def test_manual_category_update_sets_override_flag():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    post = Post(
        note_id="manual-category",
        source_url="https://example.com/manual-category",
        title="Ambiguous title",
        category=Category.UNCATEGORIZED.value,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    updated = update_post_category(
        post.id,
        PostCategoryUpdate(category=Category.FOOD),
        db,
    )

    assert updated.category == Category.FOOD.value
    assert updated.category_is_manual is True
    assert updated.sub_category is None
