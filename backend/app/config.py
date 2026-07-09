from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    load_dotenv(BACKEND_ROOT / ".env", override=False)
except ImportError:
    pass


SITE_MODES = {
    "xiaohongshu": {
        "site_key": "xiaohongshu",
        "display_name": "Xiaohongshu",
        "base_url": "https://www.xiaohongshu.com",
        "explore_url": "https://www.xiaohongshu.com/explore",
    },
    "rednote": {
        "site_key": "rednote",
        "display_name": "RedNote",
        "base_url": "https://www.rednote.com",
        "explore_url": "https://www.rednote.com/explore",
    },
}


def _resolve_project_path(value: str | Path, base: Path = PROJECT_ROOT) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def _bool_from_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _site_mode_from_env() -> str:
    site_mode = os.getenv("XHS_SITE_MODE", "rednote").strip().lower()
    return site_mode if site_mode in SITE_MODES else "rednote"


def _profile_root_from_env() -> Path:
    return _resolve_project_path(os.getenv("XHS_PLAYWRIGHT_PROFILE_ROOT", "data/playwright-profile"))


@dataclass(frozen=True)
class Settings:
    app_name: str = "RedCache"
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BACKEND_ROOT / 'data' / 'xhs_curator.db'}",
        )
    )
    obsidian_vault_path: Path = field(
        default_factory=lambda: _resolve_project_path(
            os.getenv("OBSIDIAN_VAULT_PATH", str(PROJECT_ROOT / "exports" / "obsidian"))
        )
    )
    backup_root: Path = field(
        default_factory=lambda: _resolve_project_path(
            os.getenv("BACKUP_ROOT", str(PROJECT_ROOT / "data" / "backups"))
        )
    )
    sample_posts_path: Path = field(
        default_factory=lambda: _resolve_project_path(
            os.getenv("SAMPLE_POSTS_PATH", str(BACKEND_ROOT / "data" / "sample_posts.json")),
            base=BACKEND_ROOT,
        )
    )
    xhs_site_mode: str = field(default_factory=_site_mode_from_env)
    xhs_use_system_chrome: bool = field(
        default_factory=lambda: _bool_from_env(os.getenv("XHS_USE_SYSTEM_CHROME"), False)
    )
    xhs_favorites_url: str = field(default_factory=lambda: os.getenv("XHS_FAVORITES_URL", ""))
    crawler_scroll_steps: int = field(default_factory=lambda: int(os.getenv("CRAWLER_SCROLL_STEPS", "8")))
    crawler_scroll_pause_ms: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_SCROLL_PAUSE_MS", "1200"))
    )
    crawler_page_load_timeout_ms: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_PAGE_LOAD_TIMEOUT_MS", "20000"))
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        )
    )
    export_daily_review_enabled: bool = field(
        default_factory=lambda: _bool_from_env(os.getenv("EXPORT_DAILY_REVIEW_ENABLED"), True)
    )
    active_site_key: str = field(init=False)
    active_site_display_name: str = field(init=False)
    active_base_url: str = field(init=False)
    active_explore_url: str = field(init=False)
    active_domain: str = field(init=False)
    active_allowed_domains: tuple[str, ...] = field(init=False)
    playwright_profile_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        site_key = self.xhs_site_mode if self.xhs_site_mode in SITE_MODES else "rednote"
        site = SITE_MODES[site_key]
        active_base_url = site["base_url"].rstrip("/")
        active_domain = active_base_url.removeprefix("https://").removeprefix("http://")
        allowed_domains = (active_domain,)
        if active_domain.startswith("www."):
            allowed_domains = (active_domain, active_domain.removeprefix("www."))

        object.__setattr__(self, "active_site_key", site["site_key"])
        object.__setattr__(self, "xhs_site_mode", site_key)
        object.__setattr__(self, "active_site_display_name", site["display_name"])
        object.__setattr__(self, "active_base_url", active_base_url)
        object.__setattr__(self, "active_explore_url", site["explore_url"])
        object.__setattr__(self, "active_domain", active_domain)
        object.__setattr__(self, "active_allowed_domains", allowed_domains)
        object.__setattr__(self, "playwright_profile_dir", _profile_root_from_env() / site["site_key"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
