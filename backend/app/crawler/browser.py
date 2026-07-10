from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import Settings
from app.time import utc_now


logger = logging.getLogger(__name__)


class PlaywrightUnavailableError(RuntimeError):
    pass


class VisibleBrowserManager:
    """Owns one visible persistent Chromium profile for Xiaohongshu import."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._playwright: Any | None = None
        self._context: Any | None = None
        self._profile_dir: str | None = None
        self._headless: bool = False
        self.last_launch_timestamp: str | None = None
        self.last_used_system_chrome: bool = False
        self.last_system_chrome_launch_succeeded: bool | None = None
        self.last_launch_fallback_reason: str | None = None
        self.last_login_check_result: dict | None = None

    async def get_context(self, settings: Settings, headless: bool = False):
        async with self._lock:
            requested_profile_dir = str(settings.playwright_profile_dir.resolve())
            if (
                self._context_is_alive()
                and self._profile_dir == requested_profile_dir
                and self._headless == headless
            ):
                return self._context
            self._context = None
            self._profile_dir = None
            await self._stop_playwright()

            try:
                from playwright.async_api import async_playwright
            except ImportError as exc:
                raise PlaywrightUnavailableError(
                    "Playwright is not installed. Run `pip install -e '.[dev]'` in backend."
                ) from exc

            settings.playwright_profile_dir.mkdir(parents=True, exist_ok=True)
            resolved_profile_dir = settings.playwright_profile_dir.resolve()
            logger.info(
                "Launching %s %s browser with profile: %s",
                "headless" if headless else "visible",
                settings.active_site_display_name,
                resolved_profile_dir,
            )
            self._playwright = await async_playwright().start()
            try:
                self._context = await self._launch_persistent_context(settings, headless)
            except Exception as exc:
                await self._stop_playwright()
                raise PlaywrightUnavailableError(
                    "Could not launch Chromium. Run `python -m playwright install chromium`."
                ) from exc
            self.last_launch_timestamp = utc_now().isoformat()
            self._profile_dir = requested_profile_dir
            self._headless = headless
            return self._context

    async def _launch_persistent_context(self, settings: Settings, headless: bool = False):
        launch_options = {
            "user_data_dir": str(settings.playwright_profile_dir.resolve()),
            "headless": headless,
            "viewport": {"width": 1440, "height": 1000},
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        if settings.xhs_use_system_chrome:
            try:
                context = await self._playwright.chromium.launch_persistent_context(
                    **launch_options,
                    channel="chrome",
                )
                self.last_used_system_chrome = True
                self.last_system_chrome_launch_succeeded = True
                self.last_launch_fallback_reason = None
                return context
            except Exception as exc:
                logger.warning(
                    "System Chrome launch failed; falling back to bundled Chromium: %s",
                    exc,
                )
                self.last_used_system_chrome = False
                self.last_system_chrome_launch_succeeded = False
                self.last_launch_fallback_reason = (
                    "System Chrome launch failed; using bundled Chromium instead."
                )

        context = await self._playwright.chromium.launch_persistent_context(**launch_options)
        self.last_used_system_chrome = False
        if not settings.xhs_use_system_chrome:
            self.last_system_chrome_launch_succeeded = None
            self.last_launch_fallback_reason = None
        return context

    async def open_page(self, settings: Settings, url: str, headless: bool = False):
        context = await self.get_context(settings, headless=headless)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=settings.crawler_page_load_timeout_ms)
        if not headless:
            await page.bring_to_front()
        return page

    def _context_is_alive(self) -> bool:
        if self._context is None:
            return False
        try:
            _ = self._context.pages
            return True
        except Exception:
            self._context = None
            return False

    async def _stop_playwright(self) -> None:
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        self._playwright = None
        self._profile_dir = None

    def remember_login_check(self, result: dict) -> None:
        self.last_login_check_result = result

    def profile_debug_info(self, settings: Settings) -> dict:
        profile_dir = settings.playwright_profile_dir.resolve()
        common_files = {
            "local_state": profile_dir / "Local State",
            "default_preferences": profile_dir / "Default" / "Preferences",
            "default_cookies": profile_dir / "Default" / "Cookies",
            "default_network_cookies": profile_dir / "Default" / "Network" / "Cookies",
            "default_local_storage": profile_dir / "Default" / "Local Storage",
            "default_session_storage": profile_dir / "Default" / "Session Storage",
        }
        return {
            "profile_dir": str(profile_dir),
            "profile_dir_exists": profile_dir.exists(),
            "profile_dir_size_bytes": self._directory_size(profile_dir),
            "common_profile_files": {
                name: path.exists() for name, path in common_files.items()
            },
            "system_chrome_enabled": settings.xhs_use_system_chrome,
            "using_system_chrome": self.last_used_system_chrome,
            "system_chrome_launch_succeeded_last_time": self.last_system_chrome_launch_succeeded,
            "launch_fallback_reason": self.last_launch_fallback_reason,
            "last_browser_launch_timestamp": self.last_launch_timestamp,
            "last_login_check_result": self.last_login_check_result,
        }

    def _directory_size(self, path) -> int:
        if not path.exists():
            return 0
        total = 0
        for child in path.rglob("*"):
            try:
                if child.is_file():
                    total += child.stat().st_size
            except OSError:
                continue
        return total


browser_manager = VisibleBrowserManager()
