import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.crawler import importer as importer_mod
from app.crawler.importer import CrawlerService
from app.db import Base
from app.models import ImportSource, Post


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


class _FakePage:
    url = "https://www.rednote.com/explore/a"

    async def wait_for_timeout(self, ms):
        return None


class _BackfillService(CrawlerService):
    async def _wait_for_page_settle(self, page):
        return None

    async def _detect_page_state(self, page):
        return "logged_in"


def _post(note_id, title, category="Uncategorized", manual=False):
    return Post(
        note_id=note_id,
        source_url=f"https://www.rednote.com/explore/{note_id}",
        open_url=f"https://www.rednote.com/explore/{note_id}",
        title=title,
        category=category,
        category_is_manual=manual,
        import_source=ImportSource.REDNOTE.value,
    )


def test_backfill_fills_title_and_reclassifies_untitled_only(monkeypatch):
    db = _session()
    db.add_all(
        [
            _post("a", "Untitled saved post"),
            _post("b", "已有真实标题"),  # should be left untouched
        ]
    )
    db.commit()

    async def fake_open_page(settings, url, headless=False):
        return _FakePage()

    monkeypatch.setattr(importer_mod.browser_manager, "open_page", fake_open_page)

    service = _BackfillService(get_settings())

    async def fake_title(page):
        return "夏季钩织背心教程"  # a knitting title -> Handcraft

    service._extract_note_title = fake_title  # type: ignore[assignment]

    result = asyncio.run(service.backfill_titles(db))

    assert result["updated_count"] == 1
    assert result["scanned_count"] == 1  # only the untitled post was selected
    filled = db.query(Post).filter_by(note_id="a").one()
    assert filled.title == "夏季钩织背心教程"
    assert filled.category == "Handcraft"
    untouched = db.query(Post).filter_by(note_id="b").one()
    assert untouched.title == "已有真实标题"


def test_backfill_stops_on_login_wall(monkeypatch):
    db = _session()
    db.add(_post("a", "Untitled saved post"))
    db.commit()

    async def fake_open_page(settings, url, headless=False):
        return _FakePage()

    monkeypatch.setattr(importer_mod.browser_manager, "open_page", fake_open_page)

    class _LoginWallService(_BackfillService):
        async def _detect_page_state(self, page):
            return "login_required"

    result = asyncio.run(_LoginWallService(get_settings()).backfill_titles(db))

    assert result["stopped_reason"] == "login_required"
    assert result["updated_count"] == 0
