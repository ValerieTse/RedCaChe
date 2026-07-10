from __future__ import annotations

import uuid
from datetime import UTC, timedelta
from urllib.parse import urlparse

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import Settings
from app.crawler.browser import PlaywrightUnavailableError, browser_manager
from app.crawler.extraction import (
    ExtractedFavorite,
    dedupe_extracted_posts,
    inspect_html_for_candidates,
    normalize_extracted_post,
)
from app.crawler.selectors import (
    AUTHENTICATED_SELECTOR_HINTS,
    AUTHENTICATED_TEXT_HINTS,
    AUTHOR_SELECTORS,
    CARD_SELECTORS,
    CHALLENGE_TEXT_HINTS,
    LINK_PATH_HINTS,
    LOGIN_TEXT_HINTS,
    LOGIN_OR_CHALLENGE_TEXT_HINTS,
    LOGIN_OR_CHALLENGE_URL_HINTS,
    SITE_CARD_SELECTORS,
    SITE_LINK_PATH_HINTS,
    TITLE_SELECTORS,
)
from app.models import (
    EnrichmentStatus,
    ImportRun,
    ImportSource,
    Post,
    RestoreStatus,
    ReviewStatus,
    UnfavoriteStatus,
    XhsFavoriteStatus,
)
from app.services.backup_service import backup_post_to_json
from app.services.ai_mock import MockAIProvider
from app.time import utc_now


class CrawlerService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def open_login_browser(self, login_url: str | None = None) -> dict:
        target_url = login_url or self.settings.active_explore_url
        page = await browser_manager.open_page(self.settings, target_url)
        return {
            "status": "opened",
            "message": f"Visible {self.settings.active_site_display_name} browser opened. Log in manually there; RedCache does not see or store your password.",
            "login_url": page.url,
            "profile_dir": str(self.settings.playwright_profile_dir.resolve()),
            "active_site_key": self.settings.active_site_key,
            "active_site_display_name": self.settings.active_site_display_name,
            "active_base_url": self.settings.active_base_url,
            "using_system_chrome": browser_manager.last_used_system_chrome,
            "launch_fallback_reason": browser_manager.last_launch_fallback_reason,
        }

    async def open_post_source(
        self,
        db: Session,
        post_id: int | None = None,
        url: str | None = None,
    ) -> dict:
        post = db.get(Post, post_id) if post_id is not None else None
        target_url = url or (self._best_post_open_url(post) if post is not None else None)
        if not target_url:
            return self._open_post_result(
                status="skipped",
                message="No source URL is available for this post.",
                post_id=post_id,
                requested_url=target_url,
                stopped_reason="missing_open_url",
            )

        domain_error = self._domain_validation_error(target_url)
        if domain_error:
            return self._open_post_result(
                status="failed",
                message="Source URL does not match the active site mode.",
                post_id=post_id,
                requested_url=target_url,
                stopped_reason=domain_error["stopped_reason"],
                expected_domain=domain_error["expected_domain"],
                received_url=domain_error["received_url"],
            )

        page = await browser_manager.open_page(self.settings, target_url)
        await self._wait_for_page_settle(page)
        if post is not None:
            self._remember_better_open_url(db, post, page.url)
        detected_state = await self._detect_page_state(page)
        return self._open_post_result(
            status="opened",
            message=f"Opened in the visible logged-in {self.settings.active_site_display_name} browser.",
            post_id=post_id,
            requested_url=target_url,
            current_url=page.url,
            detected_state=detected_state,
        )

    async def check_login(self, url: str | None = None) -> dict:
        target_url = url or self.settings.active_explore_url
        page = await browser_manager.open_page(self.settings, target_url)
        result = await self._inspect_login_state(page)
        browser_manager.remember_login_check(result)
        return result

    def debug_profile(self) -> dict:
        return {
            "active_site_key": self.settings.active_site_key,
            "active_site_display_name": self.settings.active_site_display_name,
            "active_base_url": self.settings.active_base_url,
            **browser_manager.profile_debug_info(self.settings),
        }

    async def enrich_posts(
        self,
        db: Session,
        post_ids: list[int] | None = None,
        import_run_id: str | None = None,
        status_filter: str | None = None,
        limit: int = 10,
        delay_seconds: float = 1.5,
    ) -> dict:
        posts = self._select_posts_for_enrichment(
            db,
            post_ids=post_ids,
            import_run_id=import_run_id,
            status_filter=status_filter,
            limit=limit,
        )
        results: list[dict] = []
        stopped_reason = None
        processed_count = 0
        enriched_count = 0
        skipped_count = 0
        failed_count = 0

        for post in posts:
            processed_count += 1
            target_url = self._best_post_open_url(post)
            if not target_url:
                skipped_count += 1
                results.append({"post_id": post.id, "status": "skipped", "reason": "missing_open_url"})
                continue

            domain_error = self._domain_validation_error(target_url)
            if domain_error:
                failed_count += 1
                results.append(
                    {
                        "post_id": post.id,
                        "status": "failed",
                        "reason": domain_error["stopped_reason"],
                        "received_url": domain_error["received_url"],
                    }
                )
                continue

            try:
                page = await browser_manager.open_page(self.settings, target_url)
                await self._wait_for_page_settle(page)
                self._remember_better_open_url(db, post, page.url)
                detected_state = await self._detect_page_state(page)
                if detected_state in {"login_required", "captcha_or_challenge"}:
                    stopped_reason = detected_state
                    failed_count += 1
                    results.append(
                        {
                            "post_id": post.id,
                            "status": "failed",
                            "reason": detected_state,
                            "current_url": page.url,
                        }
                    )
                    break

                detail = await self._extract_post_detail(page)
                detail["current_url"] = page.url or target_url
                enriched = self._apply_detail_enrichment(db, post, detail)
                if enriched:
                    enriched_count += 1
                    results.append(
                        {
                            "post_id": post.id,
                            "status": "enriched",
                            "current_url": detail["current_url"],
                            "raw_text_length": len(post.raw_text or ""),
                            "category": post.category,
                        }
                    )
                else:
                    failed_count += 1
                    results.append(
                        {
                            "post_id": post.id,
                            "status": "failed",
                            "reason": "no_detail_text_found",
                            "current_url": detail["current_url"],
                        }
                    )

                if delay_seconds > 0:
                    await page.wait_for_timeout(int(delay_seconds * 1000))
            except PlaywrightUnavailableError as exc:
                stopped_reason = "playwright_unavailable"
                failed_count += 1
                results.append({"post_id": post.id, "status": "failed", "reason": str(exc)})
                break
            except Exception as exc:
                failed_count += 1
                post.enrichment_status = EnrichmentStatus.FAILED.value
                post.updated_at = utc_now()
                db.add(post)
                db.commit()
                results.append({"post_id": post.id, "status": "failed", "reason": str(exc)})

        return {
            "processed_count": processed_count,
            "enriched_count": enriched_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "stopped_reason": stopped_reason,
            "per_post_results": results,
        }

    async def inspect_post_detail(
        self,
        db: Session,
        post_id: int | None = None,
        url: str | None = None,
    ) -> dict:
        target_url = url
        if post_id is not None:
            post = db.get(Post, post_id)
            if post is not None:
                target_url = target_url or self._best_post_open_url(post)
        if not target_url:
            return self._empty_detail_inspection_report("missing_url")

        domain_error = self._domain_validation_error(target_url)
        if domain_error:
            return self._empty_detail_inspection_report(domain_error["stopped_reason"], target_url)

        inspect_id = f"detail-{utc_now().replace(tzinfo=UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        debug_dir = self._detail_debug_dir()
        debug_dir.mkdir(parents=True, exist_ok=True)

        page = await browser_manager.open_page(self.settings, target_url)
        await self._wait_for_page_settle(page)
        detected_state = await self._detect_page_state(page)
        page_title = await self._safe_page_title(page)
        visible_text = await self._safe_body_text(page)
        detail = await self._extract_post_detail(page)

        screenshot_path = await self._save_debug_screenshot(page, debug_dir, f"{inspect_id}.png")
        debug_html_path = None
        try:
            html = await page.content()
            debug_html_path = str(debug_dir / f"{inspect_id}.html")
            (debug_dir / f"{inspect_id}.html").write_text(html, encoding="utf-8")
        except Exception:
            debug_html_path = None

        return {
            "active_site_key": self.settings.active_site_key,
            "active_base_url": self.settings.active_base_url,
            "profile_dir": str(self.settings.playwright_profile_dir.resolve()),
            "current_url": page.url or target_url,
            "detected_state": detected_state,
            "page_title": page_title,
            "visible_text_sample": visible_text[:1000],
            "extracted_title": detail["extracted_title"],
            "extracted_author": detail["extracted_author"],
            "extracted_body_text": detail["extracted_body_text"],
            "extracted_hashtags": detail["extracted_hashtags"],
            "extraction_strategy_results": detail["extraction_strategy_results"],
            "debug_screenshot_path": screenshot_path,
            "debug_html_path": debug_html_path,
        }

    async def inspect_page(
        self,
        url: str,
        max_scrolls: int = 2,
        save_debug_screenshot: bool = True,
        save_debug_html: bool = True,
    ) -> dict:
        domain_error = self._domain_validation_error(url)
        if domain_error:
            return self._empty_inspection_report(
                url=url,
                detected_state=domain_error["stopped_reason"],
            )

        inspect_id = f"inspect-{utc_now().replace(tzinfo=UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        debug_dir = self._debug_dir()
        debug_dir.mkdir(parents=True, exist_ok=True)
        screenshot_paths: list[str] = []

        page = await browser_manager.open_page(self.settings, url)
        await self._wait_for_page_settle(page)
        if save_debug_screenshot:
            screenshot_paths.append(
                await self._save_debug_screenshot(page, debug_dir, f"{inspect_id}-initial.png")
            )

        for index in range(max_scrolls):
            await self._scroll_page(page, 1)
            await self._wait_for_page_settle(page)
            if save_debug_screenshot:
                screenshot_paths.append(
                    await self._save_debug_screenshot(
                        page,
                        debug_dir,
                        f"{inspect_id}-scroll-{index + 1}.png",
                    )
                )

        page_title = await self._safe_page_title(page)
        visible_text = await self._safe_body_text(page)
        current_url = page.url or url
        try:
            cookies_count = len(await page.context.cookies(self._domain_url(current_url)))
        except Exception:
            cookies_count = None
        detected_state = self._detect_login_state(
            current_url=current_url,
            visible_text=visible_text,
            cookies_count=cookies_count,
            auth_selector_count=await self._authenticated_selector_count(page),
        )
        extraction_report = await self._inspect_visible_candidates(page)

        debug_html_path = None
        debug_text_path = None
        if save_debug_html:
            html = await page.content()
            debug_html_path = str(debug_dir / f"{inspect_id}.html")
            (debug_dir / f"{inspect_id}.html").write_text(html, encoding="utf-8")
            debug_text_path = str(debug_dir / f"{inspect_id}.txt")
            (debug_dir / f"{inspect_id}.txt").write_text(visible_text, encoding="utf-8")
            static_report = inspect_html_for_candidates(
                html=html,
                base_url=current_url,
                site_key=self.settings.active_site_key,
                allowed_domains=self.settings.active_allowed_domains,
            )
            extraction_report["selector_strategy_results"]["static_html_note_links"] = (
                static_report["candidate_note_links_count"]
            )

        return {
            "active_site_key": self.settings.active_site_key,
            "active_base_url": self.settings.active_base_url,
            "profile_dir": str(self.settings.playwright_profile_dir.resolve()),
            "current_url": current_url,
            "page_title": page_title,
            "detected_state": detected_state,
            "visible_text_sample": visible_text[:1000],
            "body_text_length": len(visible_text),
            "total_links_count": extraction_report["total_links_count"],
            "all_link_href_samples": extraction_report["all_link_href_samples"],
            "candidate_note_links": extraction_report["candidate_note_links"],
            "candidate_note_links_count": extraction_report["candidate_note_links_count"],
            "candidate_card_count": extraction_report["candidate_card_count"],
            "selector_strategy_results": extraction_report["selector_strategy_results"],
            "debug_screenshot_paths": [path for path in screenshot_paths if path],
            "debug_html_path": debug_html_path,
            "debug_text_path": debug_text_path,
        }

    async def import_visible_favorites(
        self,
        db: Session,
        favorites_url: str | None = None,
        max_scrolls: int | None = None,
        initial_review_status: ReviewStatus | None = None,
    ) -> ImportRun:
        run = ImportRun(import_run_id=f"import_{uuid.uuid4().hex[:16]}", started_at=utc_now())
        db.add(run)
        db.commit()

        try:
            target_favorites_url = favorites_url or self.settings.xhs_favorites_url
            domain_error = self._domain_validation_error(target_favorites_url)
            if domain_error:
                return self._finish_run(
                    db,
                    run,
                    status="stopped",
                    stopped_reason=domain_error["stopped_reason"],
                    expected_domain=domain_error["expected_domain"],
                    received_url=domain_error["received_url"],
                )

            login_check = await self.check_login()
            if login_check["detected_state"] != "logged_in":
                return self._finish_run(
                    db,
                    run,
                    status="stopped",
                    stopped_reason="login_not_verified",
                    error_message=f"Login check returned {login_check['detected_state']}.",
                )

            page = await browser_manager.open_page(
                self.settings,
                target_favorites_url,
            )
            stopped_reason = await self._detect_stop_reason(page)
            if stopped_reason:
                return self._finish_run(db, run, status="stopped", stopped_reason=stopped_reason)

            extracted = await self._collect_posts_while_scrolling(
                page,
                max_scrolls or self.settings.crawler_scroll_steps,
            )
            stopped_reason = await self._detect_stop_reason(page)
            if stopped_reason:
                return self._finish_run(db, run, status="stopped", stopped_reason=stopped_reason)

            if not extracted:
                return self._finish_run(
                    db,
                    run,
                    status="stopped",
                    stopped_reason="no_candidates_found",
                    scanned_count=0,
                )
            unique_posts, page_duplicate_count = dedupe_extracted_posts(extracted)
            report = self._save_posts(
                db,
                run.import_run_id,
                unique_posts,
                initial_review_status=initial_review_status or ReviewStatus.UNREVIEWED,
            )
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

    async def confirm_unfavorite_posts(
        self,
        db: Session,
        post_ids: list[int],
        confirm: bool = False,
    ) -> dict:
        if not confirm:
            return {
                "requested_count": len(post_ids),
                "backed_up_count": 0,
                "unfavorited_count": 0,
                "failed_count": 0,
                "stopped_reason": "confirmation_required",
                "backup_paths": [],
                "per_post_results": [],
            }

        posts = self._select_posts_for_unfavorite(db, post_ids)
        backup_paths: list[str] = []
        results: list[dict] = []
        backed_up_count = 0
        unfavorited_count = 0
        failed_count = 0
        stopped_reason = None

        login_check = await self.check_login()
        if login_check["detected_state"] != "logged_in":
            return {
                "requested_count": len(post_ids),
                "backed_up_count": 0,
                "unfavorited_count": 0,
                "failed_count": len(posts),
                "stopped_reason": "login_not_verified",
                "backup_paths": [],
                "per_post_results": [
                    {"post_id": post.id, "status": "failed", "reason": "login_not_verified"}
                    for post in posts
                ],
            }

        for post in posts:
            target_url = self._best_post_open_url(post)
            try:
                backup_path = backup_post_to_json(post, self.settings.backup_root)
                backup_paths.append(str(backup_path))
                backed_up_count += 1
                post.restore_status = RestoreStatus.RESTORABLE.value
                post.unfavorite_status = UnfavoriteStatus.PROCESSING.value
                post.updated_at = utc_now()
                db.add(post)
                db.commit()

                domain_error = self._domain_validation_error(target_url)
                if domain_error:
                    failed_count += 1
                    self._mark_unfavorite_failed(db, post, domain_error["stopped_reason"])
                    results.append(
                        {
                            "post_id": post.id,
                            "status": "failed",
                            "reason": domain_error["stopped_reason"],
                            "backup_path": str(backup_path),
                        }
                    )
                    continue

                page = await browser_manager.open_page(self.settings, target_url)
                await self._wait_for_page_settle(page)
                self._remember_better_open_url(db, post, page.url)
                detected_state = await self._detect_page_state(page)
                if detected_state in {"login_required", "captcha_or_challenge"}:
                    failed_count += 1
                    stopped_reason = detected_state
                    self._mark_unfavorite_failed(db, post, detected_state)
                    results.append(
                        {
                            "post_id": post.id,
                            "status": "failed",
                            "reason": detected_state,
                            "current_url": page.url,
                            "backup_path": str(backup_path),
                        }
                    )
                    break

                action_result = await self._try_visible_unfavorite(page)
                self._remember_better_open_url(db, post, page.url)
                if action_result["status"] == "unfavorited":
                    unfavorited_count += 1
                    post.review_status = ReviewStatus.ARCHIVED.value
                    post.xhs_favorite_status = XhsFavoriteStatus.UNFAVORITED.value
                    post.unfavorite_status = UnfavoriteStatus.UNFAVORITED.value
                    post.restore_status = RestoreStatus.RESTORABLE.value
                    post.operation_logs_json = [
                        *post.operation_logs_json,
                        {
                            "event": "visible_unfavorite_confirmed",
                            "current_url": page.url,
                            "button_text": action_result.get("button_text"),
                            "created_at": utc_now().isoformat(),
                        },
                    ]
                    post.updated_at = utc_now()
                    db.add(post)
                    db.commit()
                    results.append(
                        {
                            "post_id": post.id,
                            "status": "unfavorited",
                            "current_url": page.url,
                            "backup_path": str(backup_path),
                            "button_text": action_result.get("button_text"),
                        }
                    )
                else:
                    failed_count += 1
                    self._mark_unfavorite_failed(db, post, action_result["reason"])
                    results.append(
                        {
                            "post_id": post.id,
                            "status": "failed",
                            "reason": action_result["reason"],
                            "current_url": page.url,
                            "backup_path": str(backup_path),
                        }
                    )
            except PlaywrightUnavailableError as exc:
                failed_count += 1
                stopped_reason = "playwright_unavailable"
                self._mark_unfavorite_failed(db, post, str(exc))
                results.append({"post_id": post.id, "status": "failed", "reason": str(exc)})
                break
            except Exception as exc:
                failed_count += 1
                self._mark_unfavorite_failed(db, post, str(exc))
                results.append({"post_id": post.id, "status": "failed", "reason": str(exc)})

        return {
            "requested_count": len(post_ids),
            "backed_up_count": backed_up_count,
            "unfavorited_count": unfavorited_count,
            "failed_count": failed_count,
            "stopped_reason": stopped_reason,
            "backup_paths": backup_paths,
            "per_post_results": results,
        }

    def _remember_better_open_url(self, db: Session, post: Post, current_url: str | None) -> None:
        if not current_url or not self._url_has_note_id(current_url, post.note_id):
            return
        existing_url = post.open_url or ""
        if existing_url == current_url:
            return
        if urlparse(current_url).query or not existing_url:
            payload = dict(post.raw_payload_json or {})
            variants = list(payload.get("observed_url_variants") or [])
            if current_url not in variants:
                variants.append(current_url)
            payload["open_url"] = current_url
            payload["observed_url_variants"] = variants
            post.open_url = current_url
            post.raw_payload_json = payload
            post.updated_at = utc_now()
            db.add(post)
            db.commit()

    def _best_post_open_url(self, post: Post) -> str:
        payload = dict(post.raw_payload_json or {})
        candidates = [
            post.open_url,
            payload.get("open_url"),
            *(payload.get("observed_url_variants") or []),
            post.source_url,
        ]
        normalized_candidates = [str(url) for url in candidates if url]
        tokenized_url = next((url for url in normalized_candidates if "xsec_token=" in url), None)
        if tokenized_url:
            return tokenized_url
        detail_url = next(
            (
                url
                for url in normalized_candidates
                if self._is_rednote_detail_url(url)
            ),
            None,
        )
        if detail_url:
            return detail_url
        if (post.import_source == "rednote" or self.settings.active_site_key == "rednote") and post.note_id:
            return f"{self.settings.active_base_url}/explore/{post.note_id}"
        return normalized_candidates[0] if normalized_candidates else ""

    def _is_rednote_detail_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        host = parsed.hostname or ""
        return host.removeprefix("www.") == "rednote.com" and (
            "/user/profile/" in parsed.path or "/explore/" in parsed.path
        )

    def _url_has_note_id(self, url: str, note_id: str) -> bool:
        try:
            return note_id in urlparse(url).path
        except Exception:
            return False

    async def _inspect_login_state(self, page) -> dict:
        current_url = page.url or ""
        page_title = ""
        visible_text = ""
        cookies_count = None
        local_storage_count = None

        page_title = await self._safe_page_title(page)
        visible_text = await self._safe_body_text(page)

        try:
            domain_url = self._domain_url(current_url)
            cookies_count = len(await page.context.cookies(domain_url))
        except Exception:
            cookies_count = None

        try:
            local_storage_count = await page.evaluate("Object.keys(window.localStorage || {}).length")
        except Exception:
            local_storage_count = None

        auth_selector_count = await self._authenticated_selector_count(page)
        detected_state = self._detect_login_state(
            current_url=current_url,
            visible_text=visible_text,
            cookies_count=cookies_count,
            auth_selector_count=auth_selector_count,
        )
        screenshot_path = await self._save_login_check_screenshot(page)
        result = {
            "current_url": current_url,
            "page_title": page_title,
            "detected_state": detected_state,
            "visible_text_sample": visible_text[:1000],
            "active_site_key": self.settings.active_site_key,
            "active_site_display_name": self.settings.active_site_display_name,
            "active_base_url": self.settings.active_base_url,
            "profile_dir": str(self.settings.playwright_profile_dir.resolve()),
            "using_system_chrome": browser_manager.last_used_system_chrome,
            "cookies_count_for_domain": cookies_count,
            "local_storage_keys_count": local_storage_count,
            "screenshot_path": screenshot_path,
        }
        return result

    async def _detect_page_state(self, page) -> str:
        current_url = page.url or ""
        visible_text = await self._safe_body_text(page)
        try:
            cookies_count = len(await page.context.cookies(self._domain_url(current_url)))
        except Exception:
            cookies_count = None
        return self._detect_login_state(
            current_url=current_url,
            visible_text=visible_text,
            cookies_count=cookies_count,
            auth_selector_count=await self._authenticated_selector_count(page),
        )

    def _detect_login_state(
        self,
        current_url: str,
        visible_text: str,
        cookies_count: int | None,
        auth_selector_count: int,
    ) -> str:
        url_lower = current_url.lower()
        text_lower = visible_text.lower()
        if any(hint.lower() in url_lower for hint in ["captcha", "verify", "security"]):
            return "captcha_or_challenge"
        if any(hint.lower() in text_lower for hint in CHALLENGE_TEXT_HINTS):
            return "captcha_or_challenge"
        if any(hint.lower() in url_lower for hint in ["login", "signin", "passport"]):
            return "login_required"
        if any(hint.lower() in text_lower for hint in LOGIN_TEXT_HINTS):
            return "login_required"

        has_session_cookie = cookies_count is not None and cookies_count > 0
        has_visible_auth_hint = auth_selector_count > 0 or any(
            hint.lower() in text_lower for hint in AUTHENTICATED_TEXT_HINTS
        )
        if has_session_cookie and has_visible_auth_hint:
            return "logged_in"
        return "unknown"

    async def _authenticated_selector_count(self, page) -> int:
        try:
            return await page.evaluate(
                """
                (selectors) => selectors.reduce(
                  (count, selector) => count + document.querySelectorAll(selector).length,
                  0
                )
                """,
                AUTHENTICATED_SELECTOR_HINTS,
            )
        except Exception:
            return 0

    async def _safe_page_title(self, page) -> str:
        try:
            return await page.title()
        except Exception:
            return ""

    async def _safe_body_text(self, page) -> str:
        try:
            return await page.locator("body").inner_text(timeout=3000)
        except Exception:
            return ""

    async def _wait_for_page_settle(self, page) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            try:
                await page.wait_for_timeout(1500)
            except Exception:
                pass

    async def _save_login_check_screenshot(self, page) -> str | None:
        try:
            screenshots_dir = self.settings.backup_root / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            timestamp = utc_now().replace(tzinfo=UTC).strftime("%Y%m%dT%H%M%SZ")
            path = screenshots_dir / f"login-check-{timestamp}.png"
            await page.screenshot(path=str(path), full_page=False)
            return str(path)
        except Exception:
            return None

    def _debug_dir(self):
        return self.settings.backup_root.parent / "debug" / self.settings.active_site_key

    def _detail_debug_dir(self):
        return self.settings.backup_root.parent / "debug" / f"{self.settings.active_site_key}-detail"

    async def _save_debug_screenshot(self, page, debug_dir, filename: str) -> str | None:
        try:
            path = debug_dir / filename
            await page.screenshot(path=str(path), full_page=False)
            return str(path)
        except Exception:
            return None

    def _empty_inspection_report(self, url: str, detected_state: str) -> dict:
        return {
            "active_site_key": self.settings.active_site_key,
            "active_base_url": self.settings.active_base_url,
            "profile_dir": str(self.settings.playwright_profile_dir.resolve()),
            "current_url": url,
            "page_title": "",
            "detected_state": detected_state,
            "visible_text_sample": "",
            "body_text_length": 0,
            "total_links_count": 0,
            "all_link_href_samples": [],
            "candidate_note_links": [],
            "candidate_note_links_count": 0,
            "candidate_card_count": 0,
            "selector_strategy_results": {"no_strategy_succeeded": True},
            "debug_screenshot_paths": [],
            "debug_html_path": None,
            "debug_text_path": None,
        }

    def _empty_detail_inspection_report(self, detected_state: str, url: str = "") -> dict:
        return {
            "active_site_key": self.settings.active_site_key,
            "active_base_url": self.settings.active_base_url,
            "profile_dir": str(self.settings.playwright_profile_dir.resolve()),
            "current_url": url,
            "detected_state": detected_state,
            "page_title": "",
            "visible_text_sample": "",
            "extracted_title": "",
            "extracted_author": None,
            "extracted_body_text": "",
            "extracted_hashtags": [],
            "extraction_strategy_results": {"no_strategy_succeeded": True},
            "debug_screenshot_path": None,
            "debug_html_path": None,
        }

    def _open_post_result(
        self,
        *,
        status: str,
        message: str,
        post_id: int | None = None,
        requested_url: str | None = None,
        current_url: str | None = None,
        detected_state: str | None = None,
        stopped_reason: str | None = None,
        expected_domain: str | None = None,
        received_url: str | None = None,
    ) -> dict:
        return {
            "status": status,
            "message": message,
            "post_id": post_id,
            "requested_url": requested_url,
            "current_url": current_url,
            "detected_state": detected_state,
            "profile_dir": str(self.settings.playwright_profile_dir.resolve()),
            "active_site_key": self.settings.active_site_key,
            "active_site_display_name": self.settings.active_site_display_name,
            "active_base_url": self.settings.active_base_url,
            "using_system_chrome": browser_manager.last_used_system_chrome,
            "stopped_reason": stopped_reason,
            "expected_domain": expected_domain,
            "received_url": received_url,
            "launch_fallback_reason": browser_manager.last_launch_fallback_reason,
        }

    def _domain_url(self, current_url: str) -> str:
        parsed = urlparse(current_url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return self.settings.active_base_url

    def _domain_validation_error(self, url: str | None) -> dict | None:
        if not url:
            return {
                "stopped_reason": "missing_favorites_url",
                "expected_domain": self.settings.active_domain,
                "received_url": None,
            }
        parsed = urlparse(url)
        host = parsed.netloc.lower().split(":")[0]
        if host and any(
            host == domain.lower() or host.endswith(f".{domain.lower()}")
            for domain in self.settings.active_allowed_domains
        ):
            return None
        return {
            "stopped_reason": "domain_mismatch",
            "expected_domain": self.settings.active_domain,
            "received_url": url,
        }

    def _select_posts_for_unfavorite(self, db: Session, post_ids: list[int]) -> list[Post]:
        query = db.query(Post).filter(Post.review_status == ReviewStatus.REMOVE_FROM_XHS.value)
        if post_ids:
            query = query.filter(Post.id.in_(post_ids))
        return query.order_by(Post.imported_at.desc(), Post.id.desc()).all()

    def _mark_unfavorite_failed(self, db: Session, post: Post, reason: str) -> None:
        post.unfavorite_status = UnfavoriteStatus.FAILED.value
        post.operation_logs_json = [
            *post.operation_logs_json,
            {
                "event": "visible_unfavorite_failed",
                "reason": reason,
                "created_at": utc_now().isoformat(),
            },
        ]
        post.updated_at = utc_now()
        db.add(post)
        db.commit()

    async def _try_visible_unfavorite(self, page) -> dict:
        selectors = "button, [role='button']"
        count = await page.locator(selectors).count()
        positive_hints = (
            "已收藏",
            "取消收藏",
            "saved",
            "favorited",
            "remove from favorites",
            "remove from saved",
            "unsave",
        )
        negative_hints = ("like", "follow", "share", "comment", "download")
        for index in range(min(count, 80)):
            candidate = page.locator(selectors).nth(index)
            try:
                text = " ".join(
                    part.strip()
                    for part in [
                        await candidate.inner_text(timeout=700),
                        await candidate.get_attribute("aria-label", timeout=700) or "",
                        await candidate.get_attribute("title", timeout=700) or "",
                    ]
                    if part and part.strip()
                )
            except Exception:
                continue
            lowered = text.lower()
            if not lowered:
                continue
            if any(hint in lowered for hint in negative_hints):
                continue
            if any(hint in lowered for hint in positive_hints):
                await candidate.click(timeout=3000)
                await page.wait_for_timeout(1200)
                return {"status": "unfavorited", "button_text": text[:200]}
        if self.settings.active_site_key == "rednote":
            fallback_result = await self._try_rednote_collected_count_unfavorite(page)
            if fallback_result["status"] == "unfavorited":
                return fallback_result
            return fallback_result
        return {"status": "failed", "reason": "favorite_button_not_found"}

    async def _try_rednote_collected_count_unfavorite(self, page) -> dict:
        await self._wait_for_rednote_interact_state(page)
        state = await self._read_rednote_collect_state(page)

        if state.get("collected") is False:
            return {
                "status": "unfavorited",
                "button_text": "already_not_collected",
                "strategy": "rednote_already_not_collected",
            }
        if state.get("collected") is not True:
            source = state.get("source") or "unknown"
            reason = state.get("reason") or "missing_interact_state"
            return {"status": "failed", "reason": f"rednote_collect_state_unavailable:{source}:{reason}"}
        if not state.get("collectedCount"):
            return {"status": "failed", "reason": "rednote_collect_count_unavailable"}

        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(500)
            click_result = await page.evaluate(
                """
                ({ collectedCount }) => {
                  const isVisible = (node) => {
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
                  };
                  const normalize = (value) => String(value || "").replace(/\\s+/g, " ").trim();
                  const clickableFor = (node) => (
                    node.closest("button,[role='button'],[class*='interact'],[class*='collect'],[class*='bottom'],[class*='action'],[class*='engage']")
                    || node
                  );
                  const textNodes = [];
                  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                  let node = walker.nextNode();
                  while (node) {
                    if (normalize(node.textContent) === collectedCount) textNodes.push(node);
                    node = walker.nextNode();
                  }
                  const candidates = textNodes
                    .map((textNode) => clickableFor(textNode.parentElement))
                    .filter(Boolean)
                    .filter((candidate, index, list) => list.indexOf(candidate) === index)
                    .filter(isVisible);
                  for (const candidate of candidates) {
                    const text = normalize(candidate.innerText || candidate.textContent);
                    if (!text.includes(collectedCount)) continue;
                    candidate.scrollIntoView({ block: "center", inline: "center" });
                    candidate.click();
                    return {
                      clicked: true,
                      text: text.slice(0, 200),
                      className: String(candidate.className || "").slice(0, 200),
                      rect: candidate.getBoundingClientRect().toJSON?.() || null,
                    };
                  }
                  return { clicked: false, reason: "collected_count_click_target_not_found" };
                }
                """,
                {"collectedCount": state["collectedCount"]},
            )
        except Exception as exc:
            return {"status": "failed", "reason": f"rednote_count_click_failed: {exc}"}

        if not click_result.get("clicked"):
            return {"status": "failed", "reason": click_result.get("reason", "rednote_count_click_failed")}

        await page.wait_for_timeout(1500)
        verified_state = await self._read_rednote_collect_state(page, static_fallback=False)
        if verified_state.get("collected") is True:
            return {"status": "failed", "reason": "rednote_collect_state_still_true"}
        if verified_state.get("collected") is None:
            count_changed = await self._rednote_visible_count_changed(page, state["collectedCount"])
            if not count_changed:
                return {"status": "failed", "reason": "rednote_collect_count_did_not_change"}
        return {
            "status": "unfavorited",
            "button_text": click_result.get("text") or state["collectedCount"],
            "strategy": "rednote_collected_count_click",
        }

    async def _wait_for_rednote_interact_state(self, page) -> None:
        try:
            await page.wait_for_function(
                """
                () => {
                  const noteId = location.pathname.match(/[0-9a-f]{24}/i)?.[0] || "";
                  const root = window.__INITIAL_STATE__ || {};
                  const detailMap = root.note?.noteDetailMap || {};
                  const currentNoteId = root.note?.currentNoteId || root.note?.firstNoteId || noteId;
                  const runtimeDetail = detailMap[currentNoteId] || (noteId ? detailMap[noteId] : null);
                  if (runtimeDetail?.note?.interactInfo) return true;
                  const scriptText = Array.from(document.scripts)
                    .map((script) => script.textContent || "")
                    .join("\\n");
                  return Boolean(
                    noteId
                    && scriptText.includes(noteId)
                    && scriptText.includes('"interactInfo"')
                    && scriptText.includes('"collected"')
                  );
                }
                """,
                timeout=6000,
            )
        except Exception:
            pass

    async def _read_rednote_collect_state(self, page, static_fallback: bool = True) -> dict:
        try:
            return await page.evaluate(
                """
                ({ staticFallback }) => {
                  const normalize = (value) => String(value || "").trim();
                  const fromInteract = (interact, noteId, source) => ({
                    collected: interact?.collected === true ? true : interact?.collected === false ? false : null,
                    collectedCount: normalize(interact?.collectedCount),
                    noteId: String(noteId || ""),
                    source: String(source || ""),
                  });

                  const root = window.__INITIAL_STATE__ || {};
                  const currentNoteId = root.note?.currentNoteId || root.note?.firstNoteId || "";
                  const detailMap = root.note?.noteDetailMap || {};
                  const detail = detailMap[currentNoteId] || Object.values(detailMap)[0] || {};
                  const runtimeState = fromInteract(detail.note?.interactInfo || {}, currentNoteId, "runtime");
                  if (runtimeState.collected !== null && runtimeState.collectedCount) return runtimeState;
                  if (!staticFallback) return runtimeState;

                  const urlNoteId = location.pathname.match(/[0-9a-f]{24}/i)?.[0] || "";
                  const sources = [
                    ["script_text", Array.from(document.scripts).map((script) => script.textContent || "").join("\\n")],
                    ["html", document.documentElement.innerHTML || ""],
                  ];
                  for (const [sourceName, sourceText] of sources) {
                    const noteIndex = urlNoteId ? sourceText.indexOf(urlNoteId) : -1;
                    const scanArea = noteIndex >= 0
                      ? sourceText.slice(Math.max(0, noteIndex - 20000), noteIndex + 180000)
                      : sourceText;
                    const interactMatches = Array.from(scanArea.matchAll(/"interactInfo":\\{([^{}]*)\\}/g));
                    for (const match of interactMatches) {
                      const raw = match[1] || "";
                      const collectedMatch = raw.match(/"collected":(true|false)/);
                      const countMatch = raw.match(/"collectedCount":"([^"]*)"/);
                      if (!collectedMatch || !countMatch) continue;
                      return {
                        collected: collectedMatch[1] === "true",
                        collectedCount: normalize(countMatch[1]),
                        noteId: urlNoteId,
                        source: sourceName,
                      };
                    }
                  }
                  return { collected: null, collectedCount: "", noteId: urlNoteId, source: "unavailable" };
                }
                """,
                {"staticFallback": static_fallback},
            )
        except Exception as exc:
            return {
                "collected": None,
                "collectedCount": "",
                "noteId": "",
                "source": "error",
                "reason": str(exc),
            }

    async def _rednote_visible_count_changed(self, page, collected_count: str) -> bool:
        try:
            return await page.evaluate(
                """
                ({ collectedCount }) => {
                  const normalize = (value) => String(value || "").replace(/\\s+/g, " ").trim();
                  const bodyText = normalize(document.body?.innerText || "");
                  const exactPattern = new RegExp(`(^|\\\\s)${collectedCount.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")}(\\\\s|$)`);
                  if (!exactPattern.test(bodyText)) return true;
                  const numericCount = Number(collectedCount.replace(/,/g, ""));
                  if (!Number.isFinite(numericCount) || numericCount <= 0) return false;
                  const decremented = String(numericCount - 1);
                  const decrementedPattern = new RegExp(`(^|\\\\s)${decremented}(\\\\s|$)`);
                  return decrementedPattern.test(bodyText);
                }
                """,
                {"collectedCount": collected_count},
            )
        except Exception:
            return False

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
            await self._scroll_favorites_page_once(page)
            await page.wait_for_timeout(self.settings.crawler_scroll_pause_ms)

    async def _collect_posts_while_scrolling(self, page, max_scrolls: int) -> list[ExtractedFavorite]:
        collected: list[ExtractedFavorite] = []
        seen_note_ids: set[str] = set()
        seen_source_urls: set[str] = set()
        idle_scrolls = 0
        previous_position = None

        for scroll_index in range(max_scrolls + 1):
            visible_posts = await self._extract_visible_posts(page)
            added_this_pass = 0
            for post in visible_posts:
                if post.note_id in seen_note_ids or post.source_url in seen_source_urls:
                    continue
                seen_note_ids.add(post.note_id)
                seen_source_urls.add(post.source_url)
                collected.append(post)
                added_this_pass += 1

            if scroll_index >= max_scrolls:
                break

            position = await self._scroll_favorites_page_once(page)
            if position == previous_position and added_this_pass == 0:
                idle_scrolls += 1
            else:
                idle_scrolls = 0
            previous_position = position
            if idle_scrolls >= 6:
                break
            await page.wait_for_timeout(self.settings.crawler_scroll_pause_ms)

        return collected

    async def _scroll_favorites_page_once(self, page) -> dict:
        return await page.evaluate(
            """
            () => {
              const scrollables = Array.from(document.querySelectorAll("*"))
                .filter((element) => {
                  const style = window.getComputedStyle(element);
                  if (!/(auto|scroll)/.test(`${style.overflowY} ${style.overflow}`)) return false;
                  return element.scrollHeight > element.clientHeight + 80;
                })
                .sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));
              const documentTarget = document.scrollingElement || document.documentElement;
              const documentRange = Math.max(0, documentTarget.scrollHeight - documentTarget.clientHeight);
              const innerTarget = scrollables[0] || null;
              const innerRange = innerTarget ? Math.max(0, innerTarget.scrollHeight - innerTarget.clientHeight) : 0;
              const target = innerRange > documentRange ? innerTarget : documentTarget;
              const delta = Math.max(window.innerHeight * 0.55, 360);
              const before = target.scrollTop || window.scrollY || 0;
              if (target === document.body || target === document.documentElement || target === document.scrollingElement) {
                window.scrollBy(0, delta);
              } else {
                target.scrollTop += delta;
              }
              const after = target.scrollTop || window.scrollY || 0;
              return {
                y: Math.round(window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0),
                height: Math.round(document.documentElement.scrollHeight || document.body.scrollHeight || 0),
                target: String(target.tagName || "window"),
                before: Math.round(before),
                after: Math.round(after),
                targetHeight: Math.round(target.scrollHeight || document.documentElement.scrollHeight || 0),
              };
            }
            """
        )

    async def _extract_visible_posts(self, page) -> list[ExtractedFavorite]:
        extraction_report = await self._inspect_visible_candidates(page)
        raw_payloads = extraction_report["raw_payloads"]
        posts = [
            post
            for post in (
                normalize_extracted_post(
                    payload,
                    base_url=page.url,
                    allowed_domains=self.settings.active_allowed_domains,
                    site_key=self.settings.active_site_key,
                )
                for payload in raw_payloads
            )
            if post is not None
        ]
        return posts

    async def _inspect_visible_candidates(self, page) -> dict:
        return await page.evaluate(
            """
            ({ siteKey, cardSelectors, titleSelectors, authorSelectors, linkPathHints, allowedDomains }) => {
              const hostMatches = (host, domains) => domains.some((domain) => (
                host === domain || host.endsWith(`.${domain}`)
              ));

              const normalizeHref = (href) => {
                if (!href) return false;
                try {
                  return new URL(href, window.location.href).href.split("#")[0];
                } catch {
                  return "";
                }
              };

              const rednoteProfileNoteMatches = (url) => {
                const segments = url.pathname.split("/").filter(Boolean);
                return segments.length >= 4 && segments[0] === "user" && segments[1] === "profile";
              };

              const linkMatches = (href) => {
                const normalized = normalizeHref(href);
                if (!normalized) return false;
                const url = new URL(normalized);
                if (!hostMatches(url.hostname.toLowerCase(), allowedDomains)) return false;
                if (siteKey === "rednote" && rednoteProfileNoteMatches(url)) return true;
                return linkPathHints.some((hint) => url.pathname.includes(hint));
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
              const anchors = Array.from(document.querySelectorAll("a[href]"));
              const allHrefs = anchors.map((link) => normalizeHref(link.getAttribute("href"))).filter(Boolean);
              const candidateLinks = [];
              for (const link of anchors) {
                const href = normalizeHref(link.getAttribute("href"));
                if (!linkMatches(href) || seen.has(href)) continue;
                seen.add(href);
                candidateLinks.push(href);
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
                  strategy: siteKey === "rednote" ? "rednote_note_link_strategy" : "xiaohongshu_note_link_strategy",
                });
              }

              const cardSelectorMatches = cardSelectors.reduce(
                (count, selector) => count + document.querySelectorAll(selector).length,
                0
              );
              const clickableCards = Array.from(document.querySelectorAll(
                "[role='link'], [onclick], [data-id], [data-note-id], div[class*='card'], div[class*='note'], section[class*='note']"
              ));
              const clickableCardCount = clickableCards.length;
              const textBlockCount = Array.from(document.querySelectorAll("div, section, article"))
                .filter((node) => {
                  const text = node.innerText?.trim() || "";
                  return text.length > 80 && text.length < 1200;
                }).length;

              const sameDomainAnchorCount = allHrefs.filter((href) => {
                try {
                  const url = new URL(href);
                  return hostMatches(url.hostname.toLowerCase(), allowedDomains);
                } catch {
                  return false;
                }
              }).length;

              const strategyResults = siteKey === "rednote" ? {
                rednote_card_selector: cardSelectorMatches,
                rednote_note_link_strategy: candidateLinks.length,
                rednote_fallback_anchor_strategy: sameDomainAnchorCount,
                rednote_clickable_card_strategy: clickableCardCount,
                rednote_text_block_strategy: textBlockCount,
              } : {
                xiaohongshu_card_selector: cardSelectorMatches,
                xiaohongshu_note_link_strategy: candidateLinks.length,
              };
              strategyResults.no_strategy_succeeded = !Object.values(strategyResults).some(Boolean);

              return {
                total_links_count: allHrefs.length,
                all_link_href_samples: allHrefs.slice(0, 50),
                candidate_note_links: candidateLinks.slice(0, 50),
                candidate_note_links_count: candidateLinks.length,
                candidate_card_count: posts.length || cardSelectorMatches || clickableCardCount,
                selector_strategy_results: strategyResults,
                raw_payloads: posts,
              };
            }
            """,
            {
                "siteKey": self.settings.active_site_key,
                "cardSelectors": SITE_CARD_SELECTORS.get(self.settings.active_site_key, CARD_SELECTORS),
                "titleSelectors": TITLE_SELECTORS,
                "authorSelectors": AUTHOR_SELECTORS,
                "linkPathHints": SITE_LINK_PATH_HINTS.get(self.settings.active_site_key, LINK_PATH_HINTS),
                "allowedDomains": self.settings.active_allowed_domains,
            },
        )

    def _select_posts_for_enrichment(
        self,
        db: Session,
        post_ids: list[int] | None,
        import_run_id: str | None,
        status_filter: str | None,
        limit: int,
    ) -> list[Post]:
        query = db.query(Post).filter(Post.import_source == ImportSource.REDNOTE.value)
        if post_ids:
            query = query.filter(Post.id.in_(post_ids))
        if import_run_id:
            query = query.filter(Post.import_run_id == import_run_id)
        if status_filter:
            query = query.filter(Post.enrichment_status == status_filter)
        return query.order_by(Post.imported_at.desc()).limit(limit).all()

    async def _extract_post_detail(self, page) -> dict:
        return await page.evaluate(
            """
            ({ titleSelectors, authorSelectors }) => {
              const textFrom = (root, selector) => {
                const node = root.querySelector(selector);
                return node?.innerText?.trim() || node?.textContent?.trim() || "";
              };
              const firstText = (selectors) => {
                for (const selector of selectors) {
                  const text = textFrom(document, selector);
                  if (text) return text;
                }
                return "";
              };
              const collectTexts = (selectors) => {
                const values = [];
                for (const selector of selectors) {
                  for (const node of Array.from(document.querySelectorAll(selector)).slice(0, 20)) {
                    const text = node?.innerText?.trim() || node?.textContent?.trim() || "";
                    if (text && text.length >= 8 && !values.includes(text)) values.push(text);
                  }
                }
                return values;
              };
              const visibleText = document.body?.innerText?.trim() || "";
              const title =
                firstText(["h1", "h2", ...titleSelectors])
                || document.querySelector("meta[property='og:title']")?.getAttribute("content")
                || document.title
                || "";
              const author = firstText(authorSelectors);
              const bodyCandidates = collectTexts([
                "[class*='desc']",
                "[class*='content']",
                "[class*='note-content']",
                "[class*='noteContent']",
                "[class*='detail'] [class*='text']",
                "article",
              ]);
              const noise = new Set([
                "Explore", "Post", "Notifications", "Me", "About rednote", "Terms of Service",
                "Privacy Policy", "Privacy preferences", "More", "Save", "Like", "Share",
                "Notes", "Boards", "Files", "No posts yet",
              ]);
              const fallbackLines = visibleText
                .split(/\\n+/)
                .map((line) => line.trim())
                .filter((line) => line.length >= 8 && line.length <= 500 && !noise.has(line))
                .filter((line) => !/^\\d+(\\.\\d+)?[Kk万]?$/.test(line));
              const bodyText = (
                bodyCandidates.sort((a, b) => b.length - a.length)[0]
                || fallbackLines.slice(0, 80).join("\\n")
                || ""
              ).slice(0, 8000);
              let hashtags = [];
              try {
                hashtags = Array.from(new Set((visibleText.match(/#[\\p{L}\\p{N}_-]+/gu) || []))).slice(0, 20);
              } catch {
                hashtags = Array.from(new Set((visibleText.match(/#[^\\s#]+/g) || []))).slice(0, 20);
              }
              const imageAltText = Array.from(document.querySelectorAll("img"))
                .map((img) => img.getAttribute("alt") || img.getAttribute("title") || "")
                .map((text) => text.trim())
                .filter((text) => text.length >= 4)
                .slice(0, 20);
              const strategyResults = {
                title_selector: title ? 1 : 0,
                author_selector: author ? 1 : 0,
                body_selector_candidates: bodyCandidates.length,
                fallback_visible_lines: fallbackLines.length,
                hashtag_count: hashtags.length,
                image_alt_count: imageAltText.length,
              };
              strategyResults.no_strategy_succeeded = !Object.values(strategyResults).some(Boolean);
              return {
                extracted_title: title.trim(),
                extracted_author: author.trim() || null,
                extracted_body_text: bodyText.trim(),
                extracted_hashtags: hashtags,
                image_alt_text: imageAltText,
                visible_text_sample: visibleText.slice(0, 2000),
                extraction_strategy_results: strategyResults,
              };
            }
            """,
            {
                "titleSelectors": TITLE_SELECTORS,
                "authorSelectors": AUTHOR_SELECTORS,
            },
        )

    def _apply_detail_enrichment(self, db: Session, post: Post, detail: dict) -> bool:
        detail_text = (detail.get("extracted_body_text") or detail.get("visible_text_sample") or "").strip()
        if len(detail_text) < 12:
            post.enrichment_status = EnrichmentStatus.FAILED.value
            post.updated_at = utc_now()
            db.add(post)
            db.commit()
            return False

        now = utc_now()
        raw_payload = dict(post.raw_payload_json or {})
        detail_payload = {
            "current_url": detail.get("current_url"),
            "title": detail.get("extracted_title"),
            "author": detail.get("extracted_author"),
            "body_text": detail.get("extracted_body_text"),
            "hashtags": detail.get("extracted_hashtags") or [],
            "image_alt_text": detail.get("image_alt_text") or [],
            "strategy_results": detail.get("extraction_strategy_results") or {},
        }
        raw_payload["detail_enrichment"] = detail_payload

        if detail.get("current_url") and "open_url" not in raw_payload:
            raw_payload["open_url"] = post.open_url or detail["current_url"]

        extracted_title = (detail.get("extracted_title") or "").strip()
        if extracted_title and extracted_title.lower() != "rednote" and len(extracted_title) >= 2:
            post.title = extracted_title[:512]

        extracted_author = (detail.get("extracted_author") or "").strip()
        if extracted_author:
            post.author = extracted_author[:256]

        if len(detail_text) >= len(post.raw_text or ""):
            post.raw_text = detail_text
        post.raw_payload_json = raw_payload
        post.last_seen_at = now
        post.enriched_at = now
        post.enrichment_status = EnrichmentStatus.ENRICHED.value

        ai = MockAIProvider().summarize_and_classify(
            {
                "title": post.title,
                "raw_text": post.raw_text or post.title,
                "ocr_text": "",
            }
        )
        post.ai_summary = ai.ai_summary
        if not post.category_is_manual:
            post.category = ai.category or "Uncategorized"
            post.sub_category = ai.sub_category
        post.key_points_json = ai.key_points
        post.step_by_step_json = ai.step_by_step
        post.products_or_items_json = ai.products_or_items
        post.useful_for = ai.useful_for
        post.tags_json = ai.tags
        post.updated_at = now
        db.add(post)
        db.commit()
        db.refresh(post)
        return True

    def _merge_raw_payload_urls(self, existing_payload: dict | None, new_payload: dict) -> dict:
        merged = dict(existing_payload or {})
        merged_open_url = merged.get("open_url")
        new_open_url = new_payload.get("open_url")
        if new_open_url and (
            not merged_open_url
            or (
                urlparse(new_open_url).query
                and not urlparse(str(merged_open_url)).query
            )
        ):
            merged["open_url"] = new_payload["open_url"]
        if new_payload.get("source_url"):
            merged["source_url"] = new_payload["source_url"]

        variants = list(merged.get("observed_url_variants") or [])
        for variant in new_payload.get("observed_url_variants") or []:
            if variant not in variants:
                variants.append(variant)
        if variants:
            merged["observed_url_variants"] = variants
        return merged

    def _save_posts(
        self,
        db: Session,
        import_run_id: str,
        posts: list[ExtractedFavorite],
        initial_review_status: ReviewStatus = ReviewStatus.UNREVIEWED,
    ) -> dict[str, int]:
        ai_provider = MockAIProvider()
        imported_count = 0
        database_duplicate_count = 0
        failed_count = 0
        now = utc_now()

        for index, extracted in enumerate(posts):
            try:
                ordered_timestamp = now - timedelta(microseconds=index)
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
                    if extracted.open_url and (not existing.open_url or existing.open_url == existing.source_url):
                        existing.open_url = extracted.open_url
                    existing.raw_payload_json = self._merge_raw_payload_urls(
                        existing.raw_payload_json,
                        extracted.raw_payload,
                    )
                    existing.last_seen_at = now
                    existing.import_run_id = import_run_id
                    if initial_review_status == ReviewStatus.KEEP:
                        existing.imported_at = ordered_timestamp
                    if (
                        initial_review_status == ReviewStatus.KEEP
                        and existing.review_status == ReviewStatus.UNREVIEWED.value
                    ):
                        existing.review_status = ReviewStatus.KEEP.value
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
                    open_url=extracted.open_url or extracted.source_url,
                    import_source=self.settings.active_site_key,
                    import_run_id=import_run_id,
                    thumbnail_url=extracted.thumbnail_url,
                    raw_payload_json=extracted.raw_payload,
                    title=extracted.title,
                    author=extracted.author,
                    imported_at=ordered_timestamp,
                    last_seen_at=now,
                    raw_text=extracted.visible_text,
                    ai_summary=ai.ai_summary,
                    category=ai.category or "Uncategorized",
                    sub_category=ai.sub_category,
                    key_points_json=ai.key_points,
                    step_by_step_json=ai.step_by_step,
                    products_or_items_json=ai.products_or_items,
                    useful_for=ai.useful_for,
                    tags_json=ai.tags,
                    review_status=initial_review_status.value,
                    xhs_favorite_status=XhsFavoriteStatus.FAVORITED.value,
                    enrichment_status=EnrichmentStatus.NOT_ENRICHED.value,
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
        expected_domain: str | None = None,
        received_url: str | None = None,
    ) -> ImportRun:
        run.status = status
        run.finished_at = utc_now()
        run.scanned_count = scanned_count
        run.imported_count = imported_count
        run.duplicate_count = duplicate_count
        run.failed_count = failed_count
        run.stopped_reason = stopped_reason
        run.error_message = error_message
        run.expected_domain = expected_domain
        run.received_url = received_url
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
