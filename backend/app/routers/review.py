from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import Settings
from app.crawler.importer import CrawlerService
from app.db import get_db
from app.dependencies import get_effective_settings
from app.models import ReviewStatus, ReviewWindow
from app.schemas import DailyReviewResponse
from app.services.review_windows import (
    automatic_review_window,
    create_manual_window,
    latest_manual_window,
    manual_window_start,
    posts_for_daily_queue,
    response_datetimes,
    review_date_for,
)
from app.time import utc_now


router = APIRouter(prefix="/review", tags=["review"])


@router.get("/daily", response_model=DailyReviewResponse)
def get_daily_review(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_effective_settings),
) -> DailyReviewResponse:
    saved_window = latest_manual_window(db)
    if saved_window is not None:
        return _build_response(db, settings, saved_window, limit)

    start, end = automatic_review_window(settings)
    return _build_response(db, settings, None, limit, start=start, end=end)


def get_crawler_service(settings: Settings = Depends(get_effective_settings)) -> CrawlerService:
    return CrawlerService(settings)


@router.post("/daily/update", response_model=DailyReviewResponse)
async def update_daily_review(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_effective_settings),
    service: CrawlerService = Depends(get_crawler_service),
) -> DailyReviewResponse:
    start = manual_window_start(db, settings)
    if settings.xhs_favorites_url:
        await service.import_visible_favorites(
            db,
            favorites_url=settings.xhs_favorites_url,
            initial_review_status=ReviewStatus.UNREVIEWED,
            headless=True,
        )
    start, end = create_manual_window(db, settings, now=utc_now(), started_at=start)
    return _build_response(db, settings, None, limit, start=start, end=end, mode="manual_update")


def _build_response(
    db: Session,
    settings: Settings,
    saved_window: ReviewWindow | None,
    limit: int,
    *,
    start=None,
    end=None,
    mode: str | None = None,
) -> DailyReviewResponse:
    if saved_window is not None:
        start = saved_window.started_at
        end = saved_window.ended_at
        mode = saved_window.mode
    assert start is not None and end is not None

    # The window is fetch-history metadata only; the queue itself is
    # status-based, so unreviewed posts stay visible across updates.
    posts = posts_for_daily_queue(db, limit)
    response_start, response_end = response_datetimes(start, end)
    return DailyReviewResponse(
        review_date=review_date_for(end, settings),
        window_start=response_start,
        window_end=response_end,
        window_mode=mode or "automatic_24h",
        timezone=settings.review_timezone,
        cutoff_local=settings.review_baseline_local,
        count=len(posts),
        posts=posts,
    )
