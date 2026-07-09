from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.crawler.importer import CrawlerService
from app.db import get_db
from app.schemas import (
    CrawlerOpenLoginRequest,
    CrawlerOpenLoginResponse,
    ImportVisibleFavoritesRequest,
    ImportVisibleFavoritesResponse,
)


router = APIRouter(prefix="/crawler", tags=["crawler"])


def get_crawler_service(settings: Settings = Depends(get_settings)) -> CrawlerService:
    return CrawlerService(settings)


@router.get("/settings")
def get_crawler_settings(settings: Settings = Depends(get_settings)) -> dict[str, str | int]:
    return {
        "login_url": settings.xhs_login_url,
        "favorites_url": settings.xhs_favorites_url,
        "profile_dir": str(settings.playwright_profile_dir),
        "scroll_steps": settings.crawler_scroll_steps,
        "scroll_pause_ms": settings.crawler_scroll_pause_ms,
    }


@router.post("/open-login", response_model=CrawlerOpenLoginResponse)
async def open_login_browser(
    payload: CrawlerOpenLoginRequest | None = None,
    service: CrawlerService = Depends(get_crawler_service),
) -> dict:
    return await service.open_login_browser(login_url=payload.login_url if payload else None)


@router.post("/import-visible-favorites", response_model=ImportVisibleFavoritesResponse)
async def import_visible_favorites(
    payload: ImportVisibleFavoritesRequest | None = None,
    db: Session = Depends(get_db),
    service: CrawlerService = Depends(get_crawler_service),
):
    run = await service.import_visible_favorites(
        db,
        favorites_url=payload.favorites_url if payload else None,
        max_scrolls=payload.max_scrolls if payload else None,
    )
    return ImportVisibleFavoritesResponse.model_validate(run, from_attributes=True)
