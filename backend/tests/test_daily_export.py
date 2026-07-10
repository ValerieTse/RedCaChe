from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Post
from app.services.obsidian_exporter import export_daily_review


def test_daily_export_uses_visible_window_post_ids(tmp_path):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    first = Post(note_id="first", source_url="https://example.com/first", title="First")
    second = Post(note_id="second", source_url="https://example.com/second", title="Second")
    db.add_all([first, second])
    db.commit()
    db.refresh(first)

    output_path, exported_count, skipped_count = export_daily_review(
        db,
        tmp_path,
        post_ids=[first.id],
    )

    content = output_path.read_text(encoding="utf-8")
    assert exported_count == 1
    assert skipped_count == 0
    assert "First" in content
    assert "Second" not in content

    _, empty_count, _ = export_daily_review(db, tmp_path, post_ids=[])
    assert empty_count == 0
