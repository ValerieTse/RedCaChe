import asyncio

from app.config import get_settings
from app.crawler.importer import CrawlerService


class _FakeLocator:
    def __init__(self, page):
        self._page = page

    @property
    def first(self):
        return self

    async def scroll_into_view_if_needed(self, timeout=0):
        return None

    async def click(self, timeout=0):
        self._page.click_count += 1
        if self._page.toggle_on_click:
            self._page.state["href"] = "#collect"


class _FakeCollectPage:
    """Mimics a RedNote note-detail page's collect (favorite) button."""

    def __init__(self, href="#collected", found=True, visible=True, toggle_on_click=True):
        self.state = {"found": found, "href": href, "visible": visible}
        self.toggle_on_click = toggle_on_click
        self.click_count = 0

    async def wait_for_function(self, *args, **kwargs):
        return None

    async def wait_for_timeout(self, ms):
        return None

    async def evaluate(self, script, arg=None):
        return dict(self.state)

    def locator(self, selector):
        return _FakeLocator(self)


def _run(page):
    service = CrawlerService(get_settings())
    return asyncio.run(service._try_rednote_collect_button_unfavorite(page))


def test_unfavorite_clicks_collect_button_and_confirms_toggle():
    page = _FakeCollectPage(href="#collected", toggle_on_click=True)

    result = _run(page)

    assert result["status"] == "unfavorited"
    assert page.click_count == 1
    assert page.state["href"] == "#collect"


def test_unfavorite_treats_already_uncollected_as_success_without_clicking():
    page = _FakeCollectPage(href="#collect")

    result = _run(page)

    assert result["status"] == "unfavorited"
    assert result["button_text"] == "already_not_collected"
    assert page.click_count == 0


def test_unfavorite_fails_when_collect_button_missing():
    page = _FakeCollectPage(found=False, href="")

    result = _run(page)

    assert result["status"] == "failed"
    assert result["reason"] == "collect_button_not_found"


def test_unfavorite_fails_when_state_does_not_toggle():
    page = _FakeCollectPage(href="#collected", toggle_on_click=False)

    result = _run(page)

    assert result["status"] == "failed"
    assert result["reason"] == "collect_state_did_not_toggle"
    assert page.click_count == 1
