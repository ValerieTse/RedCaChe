from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import PROJECT_ROOT, Settings, _resolve_project_path
from app.db import Base
from app.models import ImportRun
from app.crawler.importer import CrawlerService
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

    async def import_visible_favorites(self, db, favorites_url=None, max_scrolls=None):
        assert favorites_url == "https://www.rednote.com/user/profile/me?tab=likes"
        assert max_scrolls == 2
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
