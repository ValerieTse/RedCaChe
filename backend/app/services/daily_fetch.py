from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.config import Settings
from app.models import ReviewStatus
from app.services.review_windows import create_manual_window, manual_window_start
from app.time import utc_now


logger = logging.getLogger(__name__)


def parse_local_fetch_time(value: str) -> time:
    hour, minute = value.strip().split(":")
    return time(hour=int(hour), minute=int(minute))


def seconds_until_next_fetch(now_utc: datetime, timezone: str, fetch_time: time) -> float:
    """Seconds from a naive-UTC now until the next local-time fetch slot."""
    zone = ZoneInfo(timezone)
    aware_now = now_utc.replace(tzinfo=UTC) if now_utc.tzinfo is None else now_utc
    local_now = aware_now.astimezone(zone)
    candidate = local_now.replace(
        hour=fetch_time.hour, minute=fetch_time.minute, second=0, microsecond=0
    )
    if candidate <= local_now:
        candidate += timedelta(days=1)
    return (candidate - local_now).total_seconds()


async def run_scheduled_fetch(settings: Settings) -> None:
    from app.crawler.importer import CrawlerService
    from app.db import SessionLocal
    from app.services.config_service import build_effective_settings

    db = SessionLocal()
    try:
        settings = build_effective_settings(db)
        if not settings.xhs_favorites_url:
            logger.info("Scheduled fetch skipped: no favorites URL configured.")
            return
        service = CrawlerService(settings)
        window_start = manual_window_start(db, settings)
        run = await service.import_visible_favorites(
            db,
            favorites_url=settings.xhs_favorites_url,
            initial_review_status=ReviewStatus.UNREVIEWED,
            headless=True,
        )
        create_manual_window(
            db,
            settings,
            now=utc_now(),
            started_at=window_start,
            mode="scheduled_fetch",
        )
        logger.info(
            "Scheduled fetch finished: status=%s scanned=%s imported=%s duplicates=%s stopped_reason=%s",
            run.status,
            run.scanned_count,
            run.imported_count,
            run.duplicate_count,
            run.stopped_reason,
        )
    finally:
        db.close()


async def daily_fetch_loop(settings: Settings) -> None:
    fetch_time = parse_local_fetch_time(settings.daily_fetch_local_time)
    while True:
        delay = seconds_until_next_fetch(utc_now(), settings.review_timezone, fetch_time)
        logger.info(
            "Next scheduled favorites fetch in %.0f seconds (daily at %s %s).",
            delay,
            settings.daily_fetch_local_time,
            settings.review_timezone,
        )
        await asyncio.sleep(delay)
        try:
            await run_scheduled_fetch(settings)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled favorites fetch failed; will retry at the next slot.")
