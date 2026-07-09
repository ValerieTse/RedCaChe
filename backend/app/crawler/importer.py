from __future__ import annotations

import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import Settings
from app.crawler.browser import PlaywrightUnavailableError, browser_manager
from app.crawler.extraction import (
    ExtractedFavorite,
    dedupe_extracted_posts,
    normalize_extracted_post,
)
from app.crawler.selectors import (
    AUTHOR_SELECTORS,
    CARD_SELECTORS,
    LINK_PATH_HINTS,
    LOGIN_OR_CHALLENGE_TEXT_HINTS,
    LOGIN_OR_CHALLENGE_URL_HINTS,
    TITLE_SELECTORS,
)
from app.models import ImportRun, ImportSource, Post, ReviewStatus, XhsFavoriteStatus
from app.services.ai_mock import MockAIProvider
from app.time import utc_now


class CrawlerService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def open_login_browser(self, login_url: str | None = None) -> dict:
        target_url = login_url or self.settings.xhs_login_url
        page = await browser_manager.open_page(self.settings, target_url)
        return {
            "status": "opened",
            "message": "Visible browser opened. Log in manually there; RedCache does not see or store your password.",
            "login_url": page.url,
            "profile_dir": str(self.settings.playwright_profile_dir),
        }

    async def import_visible_favorites(
        self,
        db: Session,
        favorites_url: str | None = None,
        max_scrolls: int | None = None,
    ) -> ImportRun:
        run = ImportRun(import_run_id=f"import_{uuid.uuid4().hex[:16]}", started_at=utc_now())
        db.add(run)
        db.commit()

        try:
            page = await browser_manager.open_page(
                self.settings,
                favorites_url or self.settings.xhs_favorites_url,
            )
            stopped_reason = await self._detect_stop_reason(page)
            if stopped_reason:
                return self._finish_run(db, run, status="stopped", stopped_reason=stopped_reason)

            await self._scroll_page(page, max_scrolls or self.settings.crawler_scroll_steps)
            stopped_reason = await self._detect_stop_reason(page)
            if stopped_reason:
                return self._finish_run(db, run, status="stopped", stopped_reason=stopped_reason)

            extracted = await self._extract_visible_posts(page)
            unique_posts, page_duplicate_count = dedupe_extracted_posts(extracted)
            report = self._save_posts(db, run.import_run_id, unique_posts)
            return self._finish_run(
                db,
                run,
                status="completed",
                scanned_count=len(extracted),
                imported_count=report["imported_count"],
                duplicate_count=page_duplicate_count + report["database_duplicate_count"],
                failed_count=report["failed_count"],
            )
        except PlaywrightUnavailableError as exc:
            return self._finish_run(
                db,
                run,
                status="failed",
                stopped_reason="playwright_unavailable",
                error_message=str(exc),
            )
        except Exception as exc:
            return self._finish_run(
                db,
                run,
                status="failed",
                stopped_reason="unexpected_error",
                error_message=str(exc),
                failed_count=1,
            )

    async def _detect_stop_reason(self, page) -> str | None:
        url = (page.url or "").lower()
        if any(hint in url for hint in LOGIN_OR_CHALLENGE_URL_HINTS):
            return "login_or_challenge_url_detected"

        try:
            body_text = (await page.locator("body").inner_text(timeout=3000)).lower()
        except Exception:
            return "unexpected_page_state"

        if any(hint.lower() in body_text for hint in LOGIN_OR_CHALLENGE_TEXT_HINTS):
            return "login_or_challenge_text_detected"
        return None

    async def _scroll_page(self, page, max_scrolls: int) -> None:
        for _ in range(max_scrolls):
            await page.evaluate("window.scrollBy(0, Math.max(window.innerHeight * 0.85, 600))")
            await page.wait_for_timeout(self.settings.crawler_scroll_pause_ms)

    async def _extract_visible_posts(self, page) -> list[ExtractedFavorite]:
        raw_payloads = await page.evaluate(
            """
            ({ cardSelectors, titleSelectors, authorSelectors, linkPathHints }) => {
              const linkMatches = (href) => {
                if (!href) return false;
                try {
                  const url = new URL(href, window.location.href);
                  return url.hostname.includes("xiaohongshu.com")
                    && linkPathHints.some((hint) => url.pathname.includes(hint));
                } catch {
                  return false;
                }
              };

              const firstText = (root, selectors) => {
                for (const selector of selectors) {
                  const node = root.querySelector(selector);
                  const text = node?.innerText?.trim();
                  if (text) return text;
                }
                return "";
              };

              const closestCard = (link) => {
                for (const selector of cardSelectors) {
                  const node = link.closest(selector);
                  if (node) return node;
                }
                let node = link;
                for (let i = 0; i < 4 && node?.parentElement; i += 1) {
                  node = node.parentElement;
                }
                return node || link;
              };

              const seen = new Set();
              const posts = [];
              for (const link of Array.from(document.querySelectorAll("a[href]"))) {
                const href = link.href;
                if (!linkMatches(href) || seen.has(href)) continue;
                seen.add(href);
                const card = closestCard(link);
                const image = card.querySelector("img");
                const text = card.innerText?.trim() || link.innerText?.trim() || "";
                const title =
                  link.getAttribute("title")
                  || link.getAttribute("aria-label")
                  || firstText(card, titleSelectors)
                  || text.split(/\\n+/).map((line) => line.trim()).find(Boolean)
                  || "";
                posts.push({
                  source_url: href,
                  title,
                  author: firstText(card, authorSelectors),
                  visible_text: text,
                  thumbnail_url: image?.currentSrc || image?.src || image?.getAttribute("data-src") || "",
                });
              }
              return posts;
            }
            """,
            {
                "cardSelectors": CARD_SELECTORS,
                "titleSelectors": TITLE_SELECTORS,
                "authorSelectors": AUTHOR_SELECTORS,
                "linkPathHints": LINK_PATH_HINTS,
            },
        )
        posts = [
            post
            for post in (normalize_extracted_post(payload, base_url=page.url) for payload in raw_payloads)
            if post is not None
        ]
        return posts

    def _save_posts(
        self,
        db: Session,
        import_run_id: str,
        posts: list[ExtractedFavorite],
    ) -> dict[str, int]:
        ai_provider = MockAIProvider()
        imported_count = 0
        database_duplicate_count = 0
        failed_count = 0
        now = utc_now()

        for extracted in posts:
            try:
                existing = (
                    db.query(Post)
                    .filter(
                        or_(
                            Post.note_id == extracted.note_id,
                            Post.source_url == extracted.source_url,
                        )
                    )
                    .one_or_none()
                )
                if existing is not None:
                    database_duplicate_count += 1
                    existing.last_seen_at = now
                    existing.import_run_id = import_run_id
                    existing.updated_at = now
                    continue

                ai = ai_provider.summarize_and_classify(
                    {
                        "title": extracted.title,
                        "raw_text": extracted.visible_text or extracted.title,
                        "ocr_text": "",
                    }
                )
                post = Post(
                    note_id=extracted.note_id,
                    source_url=extracted.source_url,
                    import_source=ImportSource.XIAOHONGSHU.value,
                    import_run_id=import_run_id,
                    thumbnail_url=extracted.thumbnail_url,
                    raw_payload_json=extracted.raw_payload,
                    title=extracted.title,
                    author=extracted.author,
                    imported_at=now,
                    last_seen_at=now,
                    raw_text=extracted.visible_text,
                    ai_summary=ai.ai_summary,
                    category=ai.category,
                    sub_category=ai.sub_category,
                    key_points_json=ai.key_points,
                    step_by_step_json=ai.step_by_step,
                    products_or_items_json=ai.products_or_items,
                    useful_for=ai.useful_for,
                    tags_json=ai.tags,
                    review_status=ReviewStatus.UNREVIEWED.value,
                    xhs_favorite_status=XhsFavoriteStatus.FAVORITED.value,
                    created_at=now,
                    updated_at=now,
                )
                db.add(post)
                imported_count += 1
            except Exception:
                failed_count += 1

        db.commit()
        return {
            "imported_count": imported_count,
            "database_duplicate_count": database_duplicate_count,
            "failed_count": failed_count,
        }

    def _finish_run(
        self,
        db: Session,
        run: ImportRun,
        status: str,
        scanned_count: int = 0,
        imported_count: int = 0,
        duplicate_count: int = 0,
        failed_count: int = 0,
        stopped_reason: str | None = None,
        error_message: str | None = None,
    ) -> ImportRun:
        run.status = status
        run.finished_at = utc_now()
        run.scanned_count = scanned_count
        run.imported_count = imported_count
        run.duplicate_count = duplicate_count
        run.failed_count = failed_count
        run.stopped_reason = stopped_reason
        run.error_message = error_message
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
