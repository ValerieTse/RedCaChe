from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

from app.crawler.selectors import LINK_PATH_HINTS


NOTE_ID_PATTERNS = [
    re.compile(r"/explore/([A-Za-z0-9_-]+)"),
    re.compile(r"/discovery/item/([A-Za-z0-9_-]+)"),
    re.compile(r"/search_result/([A-Za-z0-9_-]+)"),
    re.compile(r"/item/([A-Za-z0-9_-]+)"),
    re.compile(r"[?&](?:note_id|noteId|id)=([A-Za-z0-9_-]+)"),
]


@dataclass
class ExtractedFavorite:
    source_url: str
    note_id: str
    title: str
    author: str | None = None
    visible_text: str | None = None
    thumbnail_url: str | None = None
    raw_payload: dict = field(default_factory=dict)


def canonicalize_url(url: str, base_url: str | None = None) -> str:
    absolute = urljoin(base_url or "https://www.xiaohongshu.com/", url)
    without_fragment, _ = urldefrag(absolute)
    return without_fragment


def extract_note_id_from_url(url: str) -> str | None:
    for pattern in NOTE_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def stable_note_id_from_url(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return f"url_{digest}"


def looks_like_note_url(url: str) -> bool:
    parsed = urlparse(url)
    if "xiaohongshu.com" not in parsed.netloc:
        return False
    return any(hint in parsed.path for hint in LINK_PATH_HINTS)


def _first_content_line(text: str | None) -> str | None:
    if not text:
        return None
    for line in (part.strip() for part in re.split(r"[\n\r]+", text)):
        if 2 <= len(line) <= 160:
            return line
    return None


def normalize_extracted_post(payload: dict, base_url: str | None = None) -> ExtractedFavorite | None:
    href = payload.get("source_url") or payload.get("href")
    if not href:
        return None
    source_url = canonicalize_url(str(href), base_url)
    if not looks_like_note_url(source_url):
        return None

    visible_text = (payload.get("visible_text") or payload.get("text") or "").strip()
    title = (payload.get("title") or _first_content_line(visible_text) or "").strip()
    note_id = payload.get("note_id") or extract_note_id_from_url(source_url)
    if not note_id:
        note_id = stable_note_id_from_url(source_url)
        payload = {**payload, "note_id_missing": True}

    return ExtractedFavorite(
        source_url=source_url,
        note_id=str(note_id),
        title=title or "Untitled Xiaohongshu saved post",
        author=(payload.get("author") or None),
        visible_text=visible_text or None,
        thumbnail_url=(payload.get("thumbnail_url") or payload.get("image_url") or None),
        raw_payload={**payload, "source_url": source_url, "note_id": str(note_id)},
    )


def dedupe_extracted_posts(posts: list[ExtractedFavorite]) -> tuple[list[ExtractedFavorite], int]:
    seen_note_ids: set[str] = set()
    seen_urls: set[str] = set()
    deduped: list[ExtractedFavorite] = []
    duplicate_count = 0

    for post in posts:
        if post.note_id in seen_note_ids or post.source_url in seen_urls:
            duplicate_count += 1
            continue
        seen_note_ids.add(post.note_id)
        seen_urls.add(post.source_url)
        deduped.append(post)

    return deduped, duplicate_count


class _StaticFavoriteParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self._active: dict | None = None
        self._depth = 0
        self.raw_posts: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name: value for name, value in attrs}
        if tag == "a" and attr_map.get("href"):
            source_url = canonicalize_url(attr_map["href"] or "", self.base_url)
            if looks_like_note_url(source_url):
                self._active = {
                    "source_url": source_url,
                    "title": attr_map.get("title") or attr_map.get("aria-label"),
                    "visible_text": "",
                    "thumbnail_url": None,
                }
                self._depth = 1
                return

        if self._active is not None:
            if tag == "img" and not self._active.get("thumbnail_url"):
                self._active["thumbnail_url"] = attr_map.get("src") or attr_map.get("data-src")
                if not self._active.get("title"):
                    self._active["title"] = attr_map.get("alt")
            if tag not in self.VOID_TAGS:
                self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._active is None:
            return
        self._depth -= 1
        if self._depth <= 0:
            self.raw_posts.append(self._active)
            self._active = None

    def handle_data(self, data: str) -> None:
        if self._active is not None:
            text = data.strip()
            if text:
                current = self._active.get("visible_text") or ""
                self._active["visible_text"] = f"{current}\n{text}".strip()


def extract_posts_from_html(html: str, base_url: str) -> list[ExtractedFavorite]:
    parser = _StaticFavoriteParser(base_url)
    parser.feed(html)
    normalized = [
        post
        for post in (normalize_extracted_post(payload, base_url=base_url) for payload in parser.raw_posts)
        if post is not None
    ]
    deduped, _ = dedupe_extracted_posts(normalized)
    return deduped
