from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

from app.crawler.selectors import SITE_LINK_PATH_HINTS


DEFAULT_NOTE_DOMAINS = ("www.rednote.com", "rednote.com", "www.xiaohongshu.com", "xiaohongshu.com")


NOTE_ID_PATTERNS = [
    re.compile(r"/user/profile/[A-Za-z0-9_-]+/([A-Za-z0-9_-]+)"),
    re.compile(r"/explore/([A-Za-z0-9_-]+)"),
    re.compile(r"/discovery/item/([A-Za-z0-9_-]+)"),
    re.compile(r"/search_result/([A-Za-z0-9_-]+)"),
    re.compile(r"/notes?/([A-Za-z0-9_-]+)"),
    re.compile(r"/item/([A-Za-z0-9_-]+)"),
    re.compile(r"/post/([A-Za-z0-9_-]+)"),
    re.compile(r"[?&](?:note_id|noteId|id)=([A-Za-z0-9_-]+)"),
]


@dataclass
class ExtractedFavorite:
    source_url: str
    open_url: str | None
    note_id: str
    title: str
    author: str | None = None
    visible_text: str | None = None
    thumbnail_url: str | None = None
    raw_payload: dict = field(default_factory=dict)


def canonicalize_url(url: str, base_url: str | None = None) -> str:
    absolute = urljoin(base_url or "https://www.rednote.com/", url)
    without_fragment, _ = urldefrag(absolute)
    return without_fragment


def canonicalize_source_url(url: str, base_url: str | None = None) -> str:
    canonical = canonicalize_url(url, base_url)
    parsed = urlparse(canonical)
    return urlunparse(parsed._replace(query=""))


def extract_note_id_from_url(url: str) -> str | None:
    for pattern in NOTE_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def stable_note_id_from_url(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return f"url_{digest}"


def _host_matches(host: str, allowed_domains: tuple[str, ...]) -> bool:
    normalized_host = host.lower().split(":")[0]
    return any(
        normalized_host == domain.lower() or normalized_host.endswith(f".{domain.lower()}")
        for domain in allowed_domains
    )


def _looks_like_rednote_profile_note_path(path: str) -> bool:
    segments = [segment for segment in path.split("/") if segment]
    return len(segments) >= 4 and segments[0] == "user" and segments[1] == "profile"


def looks_like_note_url(url: str, allowed_domains: tuple[str, ...] = DEFAULT_NOTE_DOMAINS) -> bool:
    parsed = urlparse(url)
    if not _host_matches(parsed.netloc, allowed_domains):
        return False
    if _looks_like_rednote_profile_note_path(parsed.path):
        return True
    path_hints = tuple({hint for hints in SITE_LINK_PATH_HINTS.values() for hint in hints})
    return any(hint in parsed.path for hint in path_hints)


def looks_like_site_note_url(
    url: str,
    site_key: str,
    allowed_domains: tuple[str, ...] = DEFAULT_NOTE_DOMAINS,
) -> bool:
    parsed = urlparse(url)
    if not _host_matches(parsed.netloc, allowed_domains):
        return False
    if site_key == "rednote" and _looks_like_rednote_profile_note_path(parsed.path):
        return True
    path_hints = SITE_LINK_PATH_HINTS.get(site_key, SITE_LINK_PATH_HINTS["xiaohongshu"])
    return any(hint in parsed.path for hint in path_hints)


def _first_content_line(text: str | None) -> str | None:
    if not text:
        return None
    for line in (part.strip() for part in re.split(r"[\n\r]+", text)):
        if 2 <= len(line) <= 160:
            return line
    return None


def normalize_extracted_post(
    payload: dict,
    base_url: str | None = None,
    allowed_domains: tuple[str, ...] = DEFAULT_NOTE_DOMAINS,
    site_key: str | None = None,
) -> ExtractedFavorite | None:
    href = payload.get("source_url") or payload.get("href")
    if not href:
        return None
    open_href = payload.get("open_url") or payload.get("original_url") or href
    open_url = canonicalize_url(str(open_href), base_url)
    source_url = canonicalize_source_url(str(href), base_url)
    if site_key:
        is_note_url = looks_like_site_note_url(
            source_url,
            site_key=site_key,
            allowed_domains=allowed_domains,
        )
    else:
        is_note_url = looks_like_note_url(source_url, allowed_domains=allowed_domains)
    if not is_note_url:
        return None

    visible_text = (payload.get("visible_text") or payload.get("text") or "").strip()
    title = (payload.get("title") or _first_content_line(visible_text) or "").strip()
    note_id = payload.get("note_id") or extract_note_id_from_url(open_url) or extract_note_id_from_url(source_url)
    if not note_id:
        note_id = stable_note_id_from_url(source_url)
        payload = {**payload, "note_id_missing": True}

    observed_variants = [
        canonicalize_url(str(variant), base_url)
        for variant in payload.get("observed_url_variants", [])
        if variant
    ]
    for variant in [open_url, source_url]:
        if variant and variant not in observed_variants:
            observed_variants.append(variant)

    return ExtractedFavorite(
        source_url=source_url,
        open_url=open_url,
        note_id=str(note_id),
        title=title or "Untitled saved post",
        author=(payload.get("author") or None),
        visible_text=visible_text or None,
        thumbnail_url=(payload.get("thumbnail_url") or payload.get("image_url") or None),
        raw_payload={
            **payload,
            "source_url": source_url,
            "open_url": open_url,
            "observed_url_variants": observed_variants,
            "note_id": str(note_id),
        },
    )


def dedupe_extracted_posts(posts: list[ExtractedFavorite]) -> tuple[list[ExtractedFavorite], int]:
    seen_note_ids: set[str] = set()
    seen_urls: set[str] = set()
    deduped: list[ExtractedFavorite] = []
    by_note_id: dict[str, ExtractedFavorite] = {}
    by_url: dict[str, ExtractedFavorite] = {}
    duplicate_count = 0

    for post in posts:
        if post.note_id in seen_note_ids or post.source_url in seen_urls:
            duplicate_count += 1
            existing = by_note_id.get(post.note_id) or by_url.get(post.source_url)
            if existing is not None:
                merge_duplicate_post(existing, post)
            continue
        seen_note_ids.add(post.note_id)
        seen_urls.add(post.source_url)
        by_note_id[post.note_id] = post
        by_url[post.source_url] = post
        deduped.append(post)

    return deduped, duplicate_count


def merge_duplicate_post(existing: ExtractedFavorite, duplicate: ExtractedFavorite) -> None:
    if _open_url_has_query(duplicate.open_url) and not _open_url_has_query(existing.open_url):
        existing.open_url = duplicate.open_url
        existing.raw_payload["open_url"] = duplicate.open_url

    variants = list(existing.raw_payload.get("observed_url_variants") or [])
    for variant in duplicate.raw_payload.get("observed_url_variants") or []:
        if variant not in variants:
            variants.append(variant)
    existing.raw_payload["observed_url_variants"] = variants


def _open_url_has_query(url: str | None) -> bool:
    return bool(url and urlparse(url).query)


class _StaticFavoriteParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self._active: dict | None = None
        self._depth = 0
        self.raw_posts: list[dict] = []
        self.all_hrefs: list[str] = []
        self.clickable_count = 0
        self.text_block_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name: value for name, value in attrs}
        if tag == "a" and attr_map.get("href"):
            source_url = canonicalize_url(attr_map["href"] or "", self.base_url)
            self.all_hrefs.append(source_url)
            if looks_like_note_url(source_url):
                self._active = {
                    "source_url": source_url,
                    "title": attr_map.get("title") or attr_map.get("aria-label"),
                    "visible_text": "",
                    "thumbnail_url": None,
                }
                self._depth = 1
                return

        class_or_id = " ".join(
            str(attr_map.get(name) or "") for name in ["class", "id", "role", "data-id", "data-note-id"]
        ).lower()
        if tag in {"div", "section", "article", "button"} and (
            "note" in class_or_id
            or "card" in class_or_id
            or "cover" in class_or_id
            or "link" in class_or_id
            or attr_map.get("onclick")
        ):
            self.clickable_count += 1

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
            if len(text) >= 20:
                self.text_block_count += 1


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


def inspect_html_for_candidates(
    html: str,
    base_url: str,
    site_key: str,
    allowed_domains: tuple[str, ...],
) -> dict:
    parser = _StaticFavoriteParser(base_url)
    parser.feed(html)

    same_domain_hrefs = [
        href
        for href in parser.all_hrefs
        if _host_matches(urlparse(href).netloc, allowed_domains)
    ]
    candidate_links = [
        href
        for href in parser.all_hrefs
        if looks_like_site_note_url(href, site_key=site_key, allowed_domains=allowed_domains)
    ]
    normalized = [
        post
        for post in (
            normalize_extracted_post(
                payload,
                base_url=base_url,
                allowed_domains=allowed_domains,
                site_key=site_key,
            )
            for payload in parser.raw_posts
        )
        if post is not None
    ]
    deduped, _ = dedupe_extracted_posts(normalized)

    if site_key == "rednote":
        strategy_results = {
            "rednote_card_selector": len(parser.raw_posts),
            "rednote_note_link_strategy": len(candidate_links),
            "rednote_fallback_anchor_strategy": len(same_domain_hrefs),
            "rednote_clickable_card_strategy": parser.clickable_count,
            "rednote_text_block_strategy": parser.text_block_count,
        }
        strategy_results["no_strategy_succeeded"] = not any(strategy_results.values())
    else:
        strategy_results = {
            "xiaohongshu_card_selector": len(parser.raw_posts),
            "xiaohongshu_note_link_strategy": len(candidate_links),
        }
        strategy_results["no_strategy_succeeded"] = not any(strategy_results.values())

    return {
        "total_links_count": len(parser.all_hrefs),
        "all_link_href_samples": parser.all_hrefs[:50],
        "candidate_note_links": candidate_links[:50],
        "candidate_note_links_count": len(candidate_links),
        "candidate_card_count": len(deduped) or len(parser.raw_posts) or parser.clickable_count,
        "selector_strategy_results": strategy_results,
        "raw_payloads": [post.raw_payload for post in deduped],
    }
