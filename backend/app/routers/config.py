from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.category_presets import CATEGORY_PRESETS
from app.config import SITE_MODES
from app.db import get_db
from app.models import Post
from app.schemas import (
    AppConfigRead,
    AppConfigUpdate,
    CategoryRead,
    PresetCategoryRead,
    ReclassifyResponse,
)
from app.services.ai_mock import MockAIProvider
from app.services.config_service import (
    active_categories,
    classification_defs,
    get_or_create_config,
    update_config,
)
from app.time import utc_now


router = APIRouter(tags=["config"])


def _config_read(config) -> AppConfigRead:
    site = SITE_MODES.get(config.site_mode, SITE_MODES["rednote"])
    base_url = site["base_url"].rstrip("/")
    domain = base_url.removeprefix("https://").removeprefix("http://")
    return AppConfigRead(
        site_mode=config.site_mode,
        favorites_url=config.favorites_url,
        selected_category_slugs=config.selected_category_slugs or [],
        custom_categories=config.custom_categories or [],
        onboarding_completed=config.onboarding_completed,
        locale=config.locale,
        active_site_key=site["site_key"],
        active_site_display_name=site["display_name"],
        active_explore_url=site["explore_url"],
        active_domain=domain,
    )


@router.get("/config", response_model=AppConfigRead)
def get_config(db: Session = Depends(get_db)) -> AppConfigRead:
    return _config_read(get_or_create_config(db))


@router.patch("/config", response_model=AppConfigRead)
def patch_config(payload: AppConfigUpdate, db: Session = Depends(get_db)) -> AppConfigRead:
    fields = payload.model_dump(exclude_unset=True)
    if "custom_categories" in fields and fields["custom_categories"] is not None:
        fields["custom_categories"] = [
            {"name": item["name"], "keywords": item.get("keywords", [])}
            for item in fields["custom_categories"]
        ]
    config = update_config(db, **fields)
    return _config_read(config)


@router.get("/categories", response_model=list[CategoryRead])
def list_active_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    config = get_or_create_config(db)
    return [
        CategoryRead(
            slug=category["slug"],
            label_zh=category["label_zh"],
            label_en=category["label_en"],
            is_custom=category.get("is_custom", False),
        )
        for category in active_categories(config)
    ]


@router.get("/categories/presets", response_model=list[PresetCategoryRead])
def list_category_presets() -> list[PresetCategoryRead]:
    return [
        PresetCategoryRead(
            slug=preset["slug"],
            label_zh=preset["label_zh"],
            label_en=preset["label_en"],
            keyword_count=len(preset["keywords"]),
        )
        for preset in CATEGORY_PRESETS
    ]


@router.post("/categories/reclassify", response_model=ReclassifyResponse)
def reclassify_posts(db: Session = Depends(get_db)) -> ReclassifyResponse:
    """Re-run title classification on all non-manual posts using active categories."""
    config = get_or_create_config(db)
    provider = MockAIProvider(classification_defs(config))
    posts = db.query(Post).filter(Post.category_is_manual.is_(False)).all()
    updated = 0
    now = utc_now()
    for post in posts:
        new_category = provider.summarize_and_classify({"title": post.title}).category
        if new_category != post.category:
            post.category = new_category
            post.updated_at = now
            db.add(post)
            updated += 1
    db.commit()
    return ReclassifyResponse(scanned_count=len(posts), updated_count=updated)
