from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import Base
from app.models import ImportSource, Post, ReviewStatus
from app.services.review_windows import (
    automatic_review_window,
    baseline_utc,
    create_manual_window,
    posts_for_daily_queue,
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
    from_initial_import: bool = False,
    import_source: ImportSource = ImportSource.REDNOTE,
) -> Post:
    return Post(
        note_id=note_id,
        source_url=f"https://example.com/{note_id}",
        title=note_id,
        imported_at=imported_at,
        review_status=review_status.value,
        from_initial_import=from_initial_import,
        import_source=import_source.value,
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


def test_manual_update_uses_previous_update_as_next_start():
    settings = Settings()
    db = _session()

    first_start, first_end = create_manual_window(db, settings, datetime(2026, 7, 10, 7, 0))
    second_start, second_end = create_manual_window(db, settings, datetime(2026, 7, 10, 9, 0))

    assert first_start == datetime(2026, 7, 10, 5, 30)
    assert first_end == datetime(2026, 7, 10, 7, 0)
    assert second_start == first_end
    assert second_end == datetime(2026, 7, 10, 9, 0)


def test_scheduled_fetch_window_chains_from_manual_update():
    # A manual update before the nightly fetch simply becomes the start of
    # the scheduled window; nothing is skipped or double-counted.
    settings = Settings()
    db = _session()

    _, manual_end = create_manual_window(db, settings, datetime(2026, 7, 10, 20, 0))
    scheduled_start, scheduled_end = create_manual_window(
        db, settings, datetime(2026, 7, 11, 5, 30), mode="scheduled_fetch"
    )

    assert scheduled_start == manual_end
    assert scheduled_end == datetime(2026, 7, 11, 5, 30)


def test_daily_queue_keeps_unreviewed_posts_across_updates():
    db = _session()
    db.add_all(
        [
            _post("older-fetch", datetime(2026, 7, 10, 7, 0)),
            _post("newer-fetch", datetime(2026, 7, 12, 7, 0)),
        ]
    )
    db.commit()

    posts = posts_for_daily_queue(db, limit=100)

    assert [post.note_id for post in posts] == ["newer-fetch", "older-fetch"]


def test_daily_queue_excludes_reviewed_initial_import_and_mock_posts():
    db = _session()
    db.add_all(
        [
            _post("pending", datetime(2026, 7, 10, 7, 0)),
            _post("already-kept", datetime(2026, 7, 10, 7, 1), ReviewStatus.KEEP),
            _post(
                "bootstrap-backlog",
                datetime(2026, 7, 10, 7, 2),
                from_initial_import=True,
            ),
            _post(
                "mock-sample",
                datetime(2026, 7, 10, 7, 3),
                import_source=ImportSource.MOCK,
            ),
        ]
    )
    db.commit()

    posts = posts_for_daily_queue(db, limit=100)

    assert [post.note_id for post in posts] == ["pending"]
