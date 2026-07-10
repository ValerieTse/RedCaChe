"""Runtime configuration: a single-row store the onboarding UI writes to.

User-facing choices (site mode, favorites URL, active categories, onboarding
state) live in the database instead of environment variables, so the app can be
configured entirely from the UI. Infrastructure defaults (paths, CORS, timezone)
still come from the environment via :func:`app.config.get_settings`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.category_presets import (
    ALL_PRESET_SLUGS,
    CATEGORY_PRESETS,
    PRESET_BY_SLUG,
    UNCATEGORIZED,
)
from app.config import SITE_MODES, Settings, get_settings
from app.models import AppConfig, ImportSource, Post


def get_or_create_config(db: Session) -> AppConfig:
    config = db.get(AppConfig, 1)
    if config is not None:
        return config

    env = get_settings()
    # An existing library (posts already imported) should not be forced back
    # through onboarding, so seed it as already completed with every category on.
    already_has_posts = (
        db.query(Post).filter(Post.import_source != ImportSource.MOCK.value).count() > 0
    )
    config = AppConfig(
        id=1,
        site_mode=env.xhs_site_mode,
        favorites_url=env.xhs_favorites_url or None,
        selected_category_slugs=list(ALL_PRESET_SLUGS),
        custom_categories=[],
        onboarding_completed=already_has_posts,
        locale="zh",
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_config(db: Session, **fields) -> AppConfig:
    config = get_or_create_config(db)
    allowed = {
        "site_mode",
        "favorites_url",
        "selected_category_slugs",
        "custom_categories",
        "onboarding_completed",
        "locale",
    }
    for key, value in fields.items():
        if key in allowed and value is not None:
            if key == "site_mode" and value not in SITE_MODES:
                continue
            setattr(config, key, value)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def build_effective_settings(db: Session) -> Settings:
    """Env-based infra settings overlaid with the DB site mode and favorites URL."""
    config = get_or_create_config(db)
    return Settings(
        xhs_site_mode=config.site_mode,
        xhs_favorites_url=config.favorites_url or "",
    )


def _normalize_custom(entry: dict) -> dict | None:
    name = str(entry.get("name") or entry.get("slug") or "").strip()
    if not name:
        return None
    keywords = [str(k).strip() for k in (entry.get("keywords") or []) if str(k).strip()]
    return {
        "slug": name,
        "label_zh": name,
        "label_en": name,
        "keywords": keywords,
        "is_custom": True,
    }


def active_categories(config: AppConfig) -> list[dict]:
    """Enabled presets (in catalog order) + custom categories + Uncategorized."""
    selected = set(config.selected_category_slugs or [])
    categories: list[dict] = []
    for preset in CATEGORY_PRESETS:
        if preset["slug"] in selected:
            categories.append({**preset, "is_custom": False})
    for entry in config.custom_categories or []:
        normalized = _normalize_custom(entry)
        if normalized is not None and normalized["slug"] not in PRESET_BY_SLUG:
            categories.append(normalized)
    categories.append({**UNCATEGORIZED, "keywords": [], "is_custom": False})
    return categories


def classification_defs(config: AppConfig) -> list[dict]:
    """[{name, keywords}] for active categories that carry keywords."""
    defs: list[dict] = []
    for category in active_categories(config):
        keywords = category.get("keywords") or []
        if keywords and category["slug"] != UNCATEGORIZED["slug"]:
            defs.append({"name": category["slug"], "keywords": tuple(keywords)})
    return defs


def classification_defs_for_db(db: Session) -> list[dict]:
    return classification_defs(get_or_create_config(db))
