from app.crawler.extraction import (
    dedupe_extracted_posts,
    extract_note_id_from_url,
    extract_posts_from_html,
    normalize_extracted_post,
    stable_note_id_from_url,
)


def test_note_id_extraction_from_common_xhs_urls():
    assert (
        extract_note_id_from_url("https://www.xiaohongshu.com/explore/66abc123def")
        == "66abc123def"
    )
    assert (
        extract_note_id_from_url("https://www.xiaohongshu.com/discovery/item/77xyz")
        == "77xyz"
    )


def test_normalization_generates_stable_note_id_when_missing():
    url = "https://www.xiaohongshu.com/explore/"
    normalized = normalize_extracted_post(
        {
            "source_url": url,
            "visible_text": "Capsule closet idea\nAuthor name",
            "thumbnail_url": "https://img.example/thumb.jpg",
        }
    )

    assert normalized is not None
    assert normalized.note_id == stable_note_id_from_url(url)
    assert normalized.title == "Capsule closet idea"
    assert normalized.raw_payload["note_id_missing"] is True


def test_dedupe_extracted_posts_by_note_id_or_source_url():
    first = normalize_extracted_post(
        {"source_url": "https://www.xiaohongshu.com/explore/abc123", "title": "One"}
    )
    second = normalize_extracted_post(
        {"source_url": "https://www.xiaohongshu.com/explore/abc123", "title": "One again"}
    )
    third = normalize_extracted_post(
        {"source_url": "https://www.xiaohongshu.com/explore/def456", "title": "Two"}
    )

    deduped, duplicate_count = dedupe_extracted_posts([first, second, third])

    assert [post.note_id for post in deduped] == ["abc123", "def456"]
    assert duplicate_count == 1


def test_static_html_extraction_collects_note_cards():
    html = """
    <main>
      <a class="note-item" href="/explore/mocknote001" title="Desk routine">
        <img src="https://img.example/one.jpg" alt="Desk routine thumbnail">
        <span class="title">Desk routine</span>
        <span class="author">Operator Notes</span>
      </a>
      <a class="note-item" href="https://www.xiaohongshu.com/discovery/item/mocknote002">
        <img data-src="https://img.example/two.jpg">
        <span>Language study loop</span>
      </a>
    </main>
    """

    posts = extract_posts_from_html(html, "https://www.xiaohongshu.com/user/profile/me")

    assert len(posts) == 2
    assert posts[0].note_id == "mocknote001"
    assert posts[0].title == "Desk routine"
    assert posts[0].thumbnail_url == "https://img.example/one.jpg"
    assert posts[1].note_id == "mocknote002"
