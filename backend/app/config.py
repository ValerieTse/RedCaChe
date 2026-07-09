from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _bool_from_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "RedCache"
    app_env: str = os.getenv("APP_ENV", "local")
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BACKEND_ROOT / 'data' / 'xhs_curator.db'}",
    )
    obsidian_vault_path: Path = Path(
        os.getenv("OBSIDIAN_VAULT_PATH", str(PROJECT_ROOT / "exports" / "obsidian"))
    )
    backup_root: Path = Path(os.getenv("BACKUP_ROOT", str(PROJECT_ROOT / "data" / "backups")))
    sample_posts_path: Path = Path(
        os.getenv("SAMPLE_POSTS_PATH", str(BACKEND_ROOT / "data" / "sample_posts.json"))
    )
    playwright_profile_dir: Path = Path(
        os.getenv("PLAYWRIGHT_PROFILE_DIR", str(PROJECT_ROOT / "data" / "playwright-profile"))
    )
    xhs_login_url: str = os.getenv("XHS_LOGIN_URL", "https://www.xiaohongshu.com/")
    xhs_favorites_url: str = os.getenv(
        "XHS_FAVORITES_URL",
        "https://www.xiaohongshu.com/user/profile/me?tab=likes",
    )
    crawler_scroll_steps: int = int(os.getenv("CRAWLER_SCROLL_STEPS", "8"))
    crawler_scroll_pause_ms: int = int(os.getenv("CRAWLER_SCROLL_PAUSE_MS", "1200"))
    crawler_page_load_timeout_ms: int = int(os.getenv("CRAWLER_PAGE_LOAD_TIMEOUT_MS", "20000"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    )
    export_daily_review_enabled: bool = _bool_from_env(
        os.getenv("EXPORT_DAILY_REVIEW_ENABLED"), True
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
