from __future__ import annotations

import asyncio
from typing import Any

from app.config import Settings


class PlaywrightUnavailableError(RuntimeError):
    pass


class VisibleBrowserManager:
    """Owns one visible persistent Chromium profile for Xiaohongshu import."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._playwright: Any | None = None
        self._context: Any | None = None

    async def get_context(self, settings: Settings):
        async with self._lock:
            if self._context_is_alive():
                return self._context
            self._context = None
            await self._stop_playwright()

            try:
                from playwright.async_api import async_playwright
            except ImportError as exc:
                raise PlaywrightUnavailableError(
                    "Playwright is not installed. Run `pip install -e '.[dev]'` in backend."
                ) from exc

            settings.playwright_profile_dir.mkdir(parents=True, exist_ok=True)
            self._playwright = await async_playwright().start()
            try:
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(settings.playwright_profile_dir),
                    headless=False,
                    viewport={"width": 1440, "height": 1000},
                    args=["--disable-blink-features=AutomationControlled"],
                )
            except Exception as exc:
                await self._stop_playwright()
                raise PlaywrightUnavailableError(
                    "Could not launch visible Chromium. Run `python -m playwright install chromium`."
                ) from exc
            return self._context

    async def open_page(self, settings: Settings, url: str):
        context = await self.get_context(settings)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=settings.crawler_page_load_timeout_ms)
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


browser_manager = VisibleBrowserManager()
