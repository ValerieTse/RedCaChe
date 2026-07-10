from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import PROJECT_ROOT, Settings, _resolve_project_path
from app.crawler.extraction import ExtractedFavorite
from app.crawler.importer import CrawlerService
from app.db import Base
from app.models import EnrichmentStatus, ImportRun, ImportSource, Post, ReviewStatus, XhsFavoriteStatus
from app.db import get_db
from app.routers.crawler import get_crawler_service, router


class FakeRun:
    import_run_id = "import_test"
    scanned_count = 3
    imported_count = 2
    duplicate_count = 1
    failed_count = 0
    stopped_reason = None
    error_message = None
    expected_domain = None
    received_url = None
    started_at = datetime(2026, 1, 1)
    finished_at = datetime(2026, 1, 1)
    status = "completed"


class FakeCrawlerService:
    async def open_login_browser(self, login_url=None):
        return {
            "status": "opened",
            "message": "opened",
            "login_url": login_url or "https://www.rednote.com/explore",
            "profile_dir": "/tmp/redcache-profile",
            "active_site_key": "rednote",
            "active_site_display_name": "RedNote",
            "active_base_url": "https://www.rednote.com",
            "using_system_chrome": False,
            "launch_fallback_reason": None,
        }

    async def open_post_source(self, db, post_id=None, url=None):
        assert post_id == 1
        return {
            "status": "opened",
            "message": "opened",
            "post_id": post_id,
            "requested_url": "https://www.rednote.com/user/profile/me/note001",
            "current_url": "https://www.rednote.com/user/profile/me/note001?xsec_token=abc",
            "detected_state": "logged_in",
            "profile_dir": "/tmp/redcache-profile",
            "active_site_key": "rednote",
            "active_site_display_name": "RedNote",
            "active_base_url": "https://www.rednote.com",
            "using_system_chrome": False,
            "stopped_reason": None,
            "expected_domain": None,
            "received_url": None,
            "launch_fallback_reason": None,
        }

    async def import_visible_favorites(self, db, favorites_url=None, max_scrolls=None, initial_review_status=None):
        assert favorites_url == "https://www.rednote.com/user/profile/me?tab=likes"
        assert max_scrolls == 2
        assert initial_review_status == ReviewStatus.UNREVIEWED
        return FakeRun()

    async def check_login(self, url=None):
        return {
            "active_site_key": "rednote",
            "active_site_display_name": "RedNote",
            "active_base_url": "https://www.rednote.com",
            "current_url": url or "https://www.rednote.com/explore",
            "page_title": "Explore",
            "detected_state": "unknown",
            "visible_text_sample": "sample",
            "profile_dir": "/tmp/redcache-profile",
            "using_system_chrome": False,
            "cookies_count_for_domain": 0,
            "local_storage_keys_count": 0,
            "screenshot_path": "/tmp/login-check.png",
        }

    def debug_profile(self):
        return {
            "active_site_key": "rednote",
            "active_site_display_name": "RedNote",
            "active_base_url": "https://www.rednote.com",
            "profile_dir": "/tmp/redcache-profile",
            "profile_dir_exists": True,
            "profile_dir_size_bytes": 123,
            "common_profile_files": {"local_state": True},
            "system_chrome_enabled": False,
            "using_system_chrome": False,
            "system_chrome_launch_succeeded_last_time": None,
            "launch_fallback_reason": None,
            "last_browser_launch_timestamp": "2026-01-01T00:00:00",
            "last_login_check_result": None,
        }

    async def inspect_page(
        self,
        url,
        max_scrolls=2,
        save_debug_screenshot=True,
        save_debug_html=True,
    ):
        assert url == "https://www.rednote.com/user/profile/me?tab=fav"
        assert max_scrolls == 2
        assert save_debug_screenshot is True
        assert save_debug_html is True
        return {
            "active_site_key": "rednote",
            "active_base_url": "https://www.rednote.com",
            "profile_dir": "/tmp/redcache-profile",
            "current_url": url,
            "page_title": "Favorites",
            "detected_state": "logged_in",
            "visible_text_sample": "Explore Notifications Me",
            "body_text_length": 24,
            "total_links_count": 5,
            "all_link_href_samples": ["https://www.rednote.com/explore/red123"],
            "candidate_note_links": ["https://www.rednote.com/explore/red123"],
            "candidate_note_links_count": 1,
            "candidate_card_count": 1,
            "selector_strategy_results": {
                "rednote_note_link_strategy": 1,
                "no_strategy_succeeded": False,
            },
            "debug_screenshot_paths": ["/tmp/inspect-initial.png"],
            "debug_html_path": "/tmp/inspect.html",
            "debug_text_path": "/tmp/inspect.txt",
        }

    async def inspect_post_detail(self, db, post_id=None, url=None):
        assert post_id == 1 or url == "https://www.rednote.com/user/profile/me/note001?xsec_token=abc"
        return {
            "active_site_key": "rednote",
            "active_base_url": "https://www.rednote.com",
            "profile_dir": "/tmp/redcache-profile",
            "current_url": url or "https://www.rednote.com/user/profile/me/note001?xsec_token=abc",
            "detected_state": "logged_in",
            "page_title": "Detail",
            "visible_text_sample": "Detail text",
            "extracted_title": "把Codex和Claude配成科研助手",
            "extracted_author": "June博士说AI",
            "extracted_body_text": "这篇笔记介绍如何把 Codex 和 Claude Code 配成科研助手。",
            "extracted_hashtags": ["#科研"],
            "extraction_strategy_results": {"body_selector_candidates": 1, "no_strategy_succeeded": False},
            "debug_screenshot_path": "/tmp/detail.png",
            "debug_html_path": "/tmp/detail.html",
        }

    async def enrich_posts(
        self,
        db,
        post_ids=None,
        import_run_id=None,
        status_filter=None,
        limit=10,
        delay_seconds=1.5,
    ):
        assert post_ids == [1]
        assert limit == 1
        return {
            "processed_count": 1,
            "enriched_count": 1,
            "skipped_count": 0,
            "failed_count": 0,
            "stopped_reason": None,
            "per_post_results": [{"post_id": 1, "status": "enriched"}],
        }


def _client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_crawler_service] = lambda: FakeCrawlerService()
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


def test_open_login_endpoint_smoke():
    client = _client()

    response = client.post("/crawler/open-login", json={})

    assert response.status_code == 200
    assert response.json()["status"] == "opened"
    assert response.json()["profile_dir"] == "/tmp/redcache-profile"
    assert response.json()["active_site_key"] == "rednote"


def test_open_post_endpoint_smoke_without_browser():
    client = _client()

    response = client.post("/crawler/open-post", json={"post_id": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "opened"
    assert payload["post_id"] == 1
    assert payload["detected_state"] == "logged_in"
    assert payload["current_url"].endswith("xsec_token=abc")


def test_import_visible_favorites_endpoint_smoke_without_browser():
    client = _client()

    response = client.post(
        "/crawler/import-visible-favorites",
        json={
            "favorites_url": "https://www.rednote.com/user/profile/me?tab=likes",
            "max_scrolls": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "import_run_id": "import_test",
        "scanned_count": 3,
        "imported_count": 2,
        "duplicate_count": 1,
        "failed_count": 0,
        "stopped_reason": None,
        "error_message": None,
        "expected_domain": None,
        "received_url": None,
    }


def test_check_login_endpoint_smoke_without_browser():
    client = _client()

    response = client.post("/crawler/check-login", json={})

    assert response.status_code == 200
    assert response.json()["detected_state"] == "unknown"
    assert response.json()["profile_dir"] == "/tmp/redcache-profile"
    assert response.json()["current_url"] == "https://www.rednote.com/explore"


def test_debug_profile_endpoint_smoke_without_browser():
    client = _client()

    response = client.post("/crawler/debug-profile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile_dir"] == "/tmp/redcache-profile"
    assert payload["common_profile_files"] == {"local_state": True}


def test_inspect_page_endpoint_smoke_without_browser():
    client = _client()

    response = client.post(
        "/crawler/inspect-page",
        json={
            "url": "https://www.rednote.com/user/profile/me?tab=fav",
            "max_scrolls": 2,
            "save_debug_screenshot": True,
            "save_debug_html": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_site_key"] == "rednote"
    assert payload["detected_state"] == "logged_in"
    assert payload["candidate_note_links_count"] == 1
    assert payload["candidate_card_count"] == 1
    assert payload["debug_html_path"] == "/tmp/inspect.html"


def test_inspect_post_detail_endpoint_is_removed():
    client = _client()

    response = client.post("/crawler/inspect-post-detail", json={"post_id": 1})

    assert response.status_code == 404


def test_enrich_posts_endpoint_is_removed():
    client = _client()

    response = client.post(
        "/crawler/enrich-posts",
        json={"post_ids": [1], "limit": 1, "delay_seconds": 0},
    )

    assert response.status_code == 404


def test_profile_path_resolution_is_absolute_and_project_relative():
    path = _resolve_project_path("data/playwright-profile/rednote")

    assert path.is_absolute()
    assert path == (PROJECT_ROOT / "data" / "playwright-profile" / "rednote").resolve()


def test_default_site_mode_is_rednote(monkeypatch):
    monkeypatch.delenv("XHS_SITE_MODE", raising=False)
    monkeypatch.delenv("XHS_PLAYWRIGHT_PROFILE_ROOT", raising=False)
    settings = Settings()

    assert settings.active_site_key == "rednote"
    assert settings.active_site_display_name == "RedNote"
    assert settings.active_base_url == "https://www.rednote.com"
    assert settings.active_explore_url == "https://www.rednote.com/explore"
    assert settings.playwright_profile_dir == (PROJECT_ROOT / "data" / "playwright-profile" / "rednote").resolve()


def test_xiaohongshu_site_mode(monkeypatch):
    monkeypatch.setenv("XHS_SITE_MODE", "xiaohongshu")
    monkeypatch.delenv("XHS_PLAYWRIGHT_PROFILE_ROOT", raising=False)
    settings = Settings()

    assert settings.active_site_key == "xiaohongshu"
    assert settings.active_site_display_name == "Xiaohongshu"
    assert settings.active_base_url == "https://www.xiaohongshu.com"
    assert settings.active_explore_url == "https://www.xiaohongshu.com/explore"
    assert settings.playwright_profile_dir == (PROJECT_ROOT / "data" / "playwright-profile" / "xiaohongshu").resolve()


class LoginNotVerifiedService(CrawlerService):
    async def check_login(self, url=None):
        return {
            "detected_state": "login_required",
            "current_url": "https://www.xiaohongshu.com/login",
        }


def test_import_guard_stops_when_login_not_verified():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    service = LoginNotVerifiedService(Settings(xhs_site_mode="rednote"))

    import asyncio

    run = asyncio.run(
        service.import_visible_favorites(
            db,
            favorites_url="https://www.rednote.com/user/profile/me?tab=likes",
        )
    )

    assert run.status == "stopped"
    assert run.stopped_reason == "login_not_verified"
    assert db.query(ImportRun).count() == 1


class LoginVerifiedService(CrawlerService):
    async def check_login(self, url=None):
        return {
            "detected_state": "logged_in",
            "current_url": self.settings.active_explore_url,
        }


def test_import_guard_stops_on_domain_mismatch():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    service = LoginVerifiedService(Settings(xhs_site_mode="rednote"))

    import asyncio

    run = asyncio.run(
        service.import_visible_favorites(
            db,
            favorites_url="https://www.xiaohongshu.com/user/profile/me?tab=likes",
        )
    )

    assert run.status == "stopped"
    assert run.stopped_reason == "domain_mismatch"
    assert run.expected_domain == "www.rednote.com"
    assert run.received_url == "https://www.xiaohongshu.com/user/profile/me?tab=likes"


class NoCandidatesService(LoginVerifiedService):
    async def _detect_stop_reason(self, page):
        return None

    async def _collect_posts_while_scrolling(self, page, max_scrolls):
        return []


def test_import_guard_stops_when_no_candidates_found(monkeypatch):
    class FakePage:
        url = "https://www.rednote.com/user/profile/me?tab=fav"

    async def fake_open_page(settings, url):
        return FakePage()

    monkeypatch.setattr("app.crawler.importer.browser_manager.open_page", fake_open_page)

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    service = NoCandidatesService(Settings(xhs_site_mode="rednote"))

    import asyncio

    run = asyncio.run(
        service.import_visible_favorites(
            db,
            favorites_url="https://www.rednote.com/user/profile/me?tab=fav",
        )
    )

    assert run.status == "stopped"
    assert run.stopped_reason == "no_candidates_found"
    assert run.scanned_count == 0
    assert db.query(ImportRun).count() == 1


def test_save_posts_can_import_directly_to_library_status():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    service = CrawlerService(Settings(xhs_site_mode="rednote"))

    report = service._save_posts(
        db,
        "import_keep",
        [
            ExtractedFavorite(
                source_url="https://www.rednote.com/explore/note123",
                open_url="https://www.rednote.com/explore/note123?xsec_token=abc",
                note_id="note123",
                title="夏日钩织灵感",
                author="反派小早",
                visible_text="夏日钩织灵感",
            ),
            ExtractedFavorite(
                source_url="https://www.rednote.com/explore/note124",
                open_url="https://www.rednote.com/explore/note124?xsec_token=abc",
                note_id="note124",
                title="旧一点的收藏",
                author="反派小早",
                visible_text="旧一点的收藏",
            )
        ],
        initial_review_status=ReviewStatus.KEEP,
    )

    posts = db.query(Post).order_by(Post.imported_at.desc(), Post.id.desc()).all()
    assert report["imported_count"] == 2
    assert [post.note_id for post in posts] == ["note123", "note124"]
    assert {post.review_status for post in posts} == {ReviewStatus.KEEP.value}


def test_detail_enrichment_updates_title_category_without_summary():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    post = Post(
        note_id="note001",
        source_url="https://www.rednote.com/user/profile/me/note001",
        open_url="https://www.rednote.com/user/profile/me/note001?xsec_token=abc",
        import_source=ImportSource.REDNOTE.value,
        title="卡片标题",
        imported_at=datetime(2026, 1, 1),
        raw_text="卡片标题",
        ai_summary="old",
        category="Other",
        review_status=ReviewStatus.UNREVIEWED.value,
        xhs_favorite_status=XhsFavoriteStatus.FAVORITED.value,
        enrichment_status=EnrichmentStatus.NOT_ENRICHED.value,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    service = CrawlerService(Settings(xhs_site_mode="rednote"))
    enriched = service._apply_detail_enrichment(
        db,
        post,
        {
            "current_url": post.open_url,
            "extracted_title": "把Codex和Claude配成科研助手",
            "extracted_author": "June博士说AI",
            "extracted_body_text": "这篇笔记介绍如何把 Codex 和 Claude Code 配成科研助手。它强调用工具整理论文、生成实验计划，并把结果沉淀成可复用模板。",
            "extracted_hashtags": ["#科研"],
            "image_alt_text": [],
            "extraction_strategy_results": {"body_selector_candidates": 1},
        },
    )

    assert enriched is True
    assert post.enrichment_status == EnrichmentStatus.ENRICHED.value
    assert post.enriched_at is not None
    assert post.category == "Study"
    assert post.ai_summary is None
    assert post.raw_payload_json["detail_enrichment"]["hashtags"] == ["#科研"]
