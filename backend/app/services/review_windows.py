from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import ImportSource, Post, ReviewStatus, ReviewWindow
from app.time import utc_now


AUTOMATIC_WINDOW = timedelta(hours=24)


def baseline_utc(settings: Settings) -> datetime:
    local_timezone = ZoneInfo(settings.review_timezone)
    local_baseline = datetime.fromisoformat(settings.review_baseline_local)
    if local_baseline.tzinfo is None:
        local_baseline = local_baseline.replace(tzinfo=local_timezone)
    return local_baseline.astimezone(UTC).replace(tzinfo=None)


def automatic_review_window(settings: Settings, now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or utc_now()
    baseline = baseline_utc(settings)
    if current <= baseline:
        return baseline, baseline

    elapsed_windows = int((current - baseline) // AUTOMATIC_WINDOW)
    start = baseline + (AUTOMATIC_WINDOW * elapsed_windows)
    return start, current


def latest_manual_window(db: Session) -> ReviewWindow | None:
    return db.query(ReviewWindow).order_by(ReviewWindow.ended_at.desc(), ReviewWindow.id.desc()).first()


def create_manual_window(
    db: Session,
    settings: Settings,
    now: datetime | None = None,
    started_at: datetime | None = None,
    mode: str = "manual_update",
) -> tuple[datetime, datetime]:
    current = now or utc_now()
    start = started_at or manual_window_start(db, settings, current)
    if start > current:
        start = current

    window = ReviewWindow(started_at=start, ended_at=current, mode=mode)
    db.add(window)
    db.commit()
    db.refresh(window)
    return window.started_at, window.ended_at


def manual_window_start(db: Session, settings: Settings, now: datetime | None = None) -> datetime:
    current = now or utc_now()
    baseline = baseline_utc(settings)
    if current <= baseline:
        return baseline
    previous = latest_manual_window(db)
    return previous.ended_at if previous is not None else baseline


def posts_for_daily_queue(db: Session, limit: int) -> list[Post]:
    """Every fetched-later post stays in Daily Review until the user decides.

    Posts from the initial bootstrap import live in the Library instead, and
    mock sample data never enters the review queue.
    """
    return (
        db.query(Post)
        .filter(Post.review_status == ReviewStatus.UNREVIEWED.value)
        .filter(Post.from_initial_import.is_(False))
        .filter(Post.import_source != ImportSource.MOCK.value)
        .order_by(Post.imported_at.desc(), Post.id.desc())
        .limit(limit)
        .all()
    )


def response_datetimes(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    return start.replace(tzinfo=UTC), end.replace(tzinfo=UTC)


def review_date_for(end: datetime, settings: Settings) -> date:
    aware_end = end.replace(tzinfo=UTC)
    return aware_end.astimezone(ZoneInfo(settings.review_timezone)).date()
