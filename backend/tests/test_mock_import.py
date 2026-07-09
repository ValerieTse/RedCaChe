from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import ImportSource, Post, ReviewStatus
from app.services.mock_importer import import_sample_posts


SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_posts.json"


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def test_mock_import_creates_summarized_unreviewed_posts():
    db = _session()
    imported, updated = import_sample_posts(db, SAMPLE_PATH)

    assert imported == 12
    assert updated == 0
    posts = db.query(Post).all()
    assert len(posts) == 12
    assert {post.review_status for post in posts} == {ReviewStatus.UNREVIEWED.value}
    assert {post.import_source for post in posts} == {ImportSource.MOCK.value}
    assert all(post.ai_summary for post in posts)
    assert all(post.category for post in posts)
    assert all(post.key_points_json for post in posts)
    assert all(post.raw_payload_json for post in posts)


def test_mock_import_is_idempotent_by_note_id():
    db = _session()
    first = import_sample_posts(db, SAMPLE_PATH)
    second = import_sample_posts(db, SAMPLE_PATH)

    assert first == (12, 0)
    assert second == (0, 12)
    assert db.query(Post).count() == 12
