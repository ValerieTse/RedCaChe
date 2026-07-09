from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

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
    started_at = datetime(2026, 1, 1)
    finished_at = datetime(2026, 1, 1)
    status = "completed"


class FakeCrawlerService:
    async def open_login_browser(self, login_url=None):
        return {
            "status": "opened",
            "message": "opened",
            "login_url": login_url or "https://www.xiaohongshu.com/",
            "profile_dir": "/tmp/redcache-profile",
        }

    async def import_visible_favorites(self, db, favorites_url=None, max_scrolls=None):
        assert favorites_url == "https://www.xiaohongshu.com/user/profile/me?tab=likes"
        assert max_scrolls == 2
        return FakeRun()


def _client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_crawler_service] = lambda: FakeCrawlerService()
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


def test_open_login_endpoint_smoke():
    client = _client()

    response = client.post("/crawler/open-login", json={"login_url": "https://www.xiaohongshu.com/"})

    assert response.status_code == 200
    assert response.json()["status"] == "opened"
    assert response.json()["profile_dir"] == "/tmp/redcache-profile"


def test_import_visible_favorites_endpoint_smoke_without_browser():
    client = _client()

    response = client.post(
        "/crawler/import-visible-favorites",
        json={
            "favorites_url": "https://www.xiaohongshu.com/user/profile/me?tab=likes",
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
    }
