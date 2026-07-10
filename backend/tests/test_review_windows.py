from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import Base
from app.models import Post, ReviewStatus
from app.services.review_windows import (
    automatic_review_window,
    baseline_utc,
    create_manual_window,
    posts_for_window,
)


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _post(
    note_id: str,
    imported_at: datetime,
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED,
) -> Post:
    return Post(
        note_id=note_id,
        source_url=f"https://example.com/{note_id}",
        title=note_id,
        imported_at=imported_at,
        review_status=review_status.value,
    )


def test_baseline_uses_requested_local_time():
    settings = Settings(
        review_timezone="America/Los_Angeles",
        review_baseline_local="2026-07-09T22:30:00",
    )

    assert baseline_utc(settings) == datetime(2026, 7, 10, 5, 30)


def test_automatic_windows_are_24_hours_from_baseline():
    settings = Settings()

    start, end = automatic_review_window(settings, datetime(2026, 7, 11, 6, 0))

    assert start == datetime(2026, 7, 11, 5, 30)
    assert end == datetime(2026, 7, 11, 6, 0)


def test_posts_before_baseline_are_excluded():
    settings = Settings()
    db = _session()
    db.add_all(
        [
            _post("old", datetime(2026, 7, 10, 5, 29)),
            _post("new", datetime(2026, 7, 10, 5, 45)),
        ]
    )
    db.commit()
    start, end = automatic_review_window(settings, datetime(2026, 7, 10, 6, 0))

    posts = posts_for_window(db, start, end, limit=100)

    assert [post.note_id for post in posts] == ["new"]


def test_manual_update_uses_previous_update_as_next_start():
    settings = Settings()
    db = _session()
    db.add_all(
        [
            _post("first", datetime(2026, 7, 10, 6, 0)),
            _post("second", datetime(2026, 7, 10, 8, 0)),
        ]
    )
    db.commit()

    first_start, first_end = create_manual_window(db, settings, datetime(2026, 7, 10, 7, 0))
    second_start, second_end = create_manual_window(db, settings, datetime(2026, 7, 10, 9, 0))

    assert first_start == datetime(2026, 7, 10, 5, 30)
    assert first_end == datetime(2026, 7, 10, 7, 0)
    assert [post.note_id for post in posts_for_window(db, first_start, first_end, 100)] == ["first"]
    assert second_start == first_end
    assert second_end == datetime(2026, 7, 10, 9, 0)
    assert [post.note_id for post in posts_for_window(db, second_start, second_end, 100)] == ["second"]


def test_daily_window_only_returns_unreviewed_posts():
    db = _session()
    start = datetime(2026, 7, 10, 5, 30)
    end = datetime(2026, 7, 10, 8, 0)
    db.add_all(
        [
            _post("needs-review", datetime(2026, 7, 10, 7, 0), ReviewStatus.UNREVIEWED),
            _post("already-kept", datetime(2026, 7, 10, 7, 1), ReviewStatus.KEEP),
        ]
    )
    db.commit()

    posts = posts_for_window(db, start, end, limit=100)

    assert [post.note_id for post in posts] == ["needs-review"]
