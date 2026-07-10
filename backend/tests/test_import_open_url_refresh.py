import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.crawler.extraction import normalize_extracted_post
from app.crawler.importer import CrawlerService
from app.db import Base
from app.models import Post


BARE_URL = "https://www.rednote.com/user/profile/0123456789abcdef01234567/1111111111111111aaaaaaaa"
FRESH_TOKEN_URL = f"{BARE_URL}?xsec_token=ABfresh-token=&xsec_source=pc_collect"
STALE_TOKEN_URL = f"{BARE_URL}?xsec_token=ABstale-token=&xsec_source=pc_collect"
FAVORITES_PAGE_URL = "https://www.rednote.com/user/profile/0123456789abcdef01234567?tab=fav&subTab=note"


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


class FakeFavoritesPage:
    """Stands in for a Playwright page on the favorites grid."""

    url = FAVORITES_PAGE_URL

    def __init__(self, raw_payloads):
        self._raw_payloads = raw_payloads

    async def evaluate(self, script, arg=None):
        if isinstance(arg, dict) and "cardSelectors" in arg:
            return {"raw_payloads": self._raw_payloads}
        return {"y": 0, "height": 0, "target": "window", "before": 0, "after": 0, "targetHeight": 0}

    async def wait_for_timeout(self, ms):
        return None


def _card_payload(source_url):
    return {
        "source_url": source_url,
        "title": "会呼吸的浪",
        "author": "鹿婆婆的手工阁楼",
        "visible_text": "会呼吸的浪\n鹿婆婆的手工阁楼\n8286",
        "thumbnail_url": "",
        "strategy": "rednote_note_link_strategy",
    }


def test_collect_posts_keeps_tokenized_variant_over_bare_href():
    # The favorites grid renders each note card with a bare href first and
    # tokenized hrefs after it; the collector must merge instead of dropping.
    service = CrawlerService(get_settings())
    page = FakeFavoritesPage([_card_payload(BARE_URL), _card_payload(FRESH_TOKEN_URL)])

    collected = asyncio.run(service._collect_posts_while_scrolling(page, max_scrolls=0))

    assert len(collected) == 1
    assert collected[0].source_url == BARE_URL
    assert "xsec_token=" in (collected[0].open_url or "")
    assert collected[0].raw_payload["open_url"] == collected[0].open_url


def _extracted(open_source_url):
    extracted = normalize_extracted_post(
        _card_payload(open_source_url),
        base_url=FAVORITES_PAGE_URL,
        site_key="rednote",
    )
    assert extracted is not None
    return extracted


def test_save_posts_refreshes_stale_token_on_reimport():
    db = _session()
    service = CrawlerService(get_settings())
    service._save_posts(db, "run_old", [_extracted(STALE_TOKEN_URL)])
    assert db.query(Post).one().open_url == STALE_TOKEN_URL

    report = service._save_posts(db, "run_new", [_extracted(FRESH_TOKEN_URL)])

    assert report["database_duplicate_count"] == 1
    post = db.query(Post).one()
    assert post.open_url == FRESH_TOKEN_URL
    assert post.raw_payload_json["open_url"] == FRESH_TOKEN_URL


def test_save_posts_keeps_tokenized_open_url_when_reimport_sees_bare_href():
    db = _session()
    service = CrawlerService(get_settings())
    service._save_posts(db, "run_old", [_extracted(STALE_TOKEN_URL)])

    service._save_posts(db, "run_new", [_extracted(BARE_URL)])

    post = db.query(Post).one()
    assert post.open_url == STALE_TOKEN_URL


OTHER_NOTE_URL = (
    "https://www.rednote.com/user/profile/0123456789abcdef01234567/7000000000000000aaaaaaaa"
)


def test_first_import_is_marked_as_initial_and_later_imports_are_not():
    db = _session()
    service = CrawlerService(get_settings())

    service._save_posts(db, "bootstrap_run", [_extracted(BARE_URL)])
    service._save_posts(db, "later_run", [_extracted(OTHER_NOTE_URL)])

    bootstrap_post = db.query(Post).filter(Post.source_url == BARE_URL).one()
    later_post = db.query(Post).filter(Post.source_url == OTHER_NOTE_URL).one()
    assert bootstrap_post.from_initial_import is True
    assert later_post.from_initial_import is False
