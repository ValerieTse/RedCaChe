from app.crawler.extraction import (
    dedupe_extracted_posts,
    extract_note_id_from_url,
    extract_posts_from_html,
    inspect_html_for_candidates,
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
    assert extract_note_id_from_url("https://www.rednote.com/explore/red123") == "red123"
    assert (
        extract_note_id_from_url(
            "https://www.rednote.com/user/profile/0123456789abcdef01234567/abcdef0123456789abcdef01?xsec_source=pc_collect"
        )
        == "abcdef0123456789abcdef01"
    )


def test_normalization_generates_stable_note_id_when_missing():
    url = "https://www.rednote.com/explore/"
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


def test_rednote_normalization_preserves_canonical_source_and_open_url():
    original_url = (
        "https://www.rednote.com/user/profile/profile001/note001"
        "?xsec_token=abc&xsec_source=pc_collect"
    )
    normalized = normalize_extracted_post(
        {
            "source_url": original_url,
            "visible_text": "把Codex和Claude配成科研助手\nJune博士说AI",
        },
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )

    assert normalized is not None
    assert normalized.source_url == "https://www.rednote.com/user/profile/profile001/note001"
    assert normalized.open_url == original_url
    assert normalized.raw_payload["observed_url_variants"] == [
        original_url,
        "https://www.rednote.com/user/profile/profile001/note001",
    ]


def test_dedupe_prefers_query_open_url_for_rednote_duplicates():
    canonical = normalize_extracted_post(
        {
            "source_url": "https://www.rednote.com/user/profile/profile001/note001",
            "title": "Canonical first",
        },
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )
    query = normalize_extracted_post(
        {
            "source_url": "https://www.rednote.com/user/profile/profile001/note001?xsec_token=abc",
            "title": "Query second",
        },
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )

    deduped, duplicate_count = dedupe_extracted_posts([canonical, query])

    assert duplicate_count == 1
    assert len(deduped) == 1
    assert deduped[0].source_url == "https://www.rednote.com/user/profile/profile001/note001"
    assert deduped[0].open_url == "https://www.rednote.com/user/profile/profile001/note001?xsec_token=abc"


def test_static_html_extraction_collects_note_cards():
    html = """
    <main>
      <a class="note-item" href="/explore/mocknote001" title="Desk routine">
        <img src="https://img.example/one.jpg" alt="Desk routine thumbnail">
        <span class="title">Desk routine</span>
        <span class="author">Operator Notes</span>
      </a>
      <a class="note-item" href="https://www.rednote.com/discovery/item/mocknote002">
        <img data-src="https://img.example/two.jpg">
        <span>Language study loop</span>
      </a>
    </main>
    """

    posts = extract_posts_from_html(html, "https://www.rednote.com/explore")

    assert len(posts) == 2
    assert posts[0].note_id == "mocknote001"
    assert posts[0].title == "Desk routine"
    assert posts[0].thumbnail_url == "https://img.example/one.jpg"
    assert posts[1].note_id == "mocknote002"


def test_rednote_static_inspection_extracts_anchor_note_links():
    html = """
    <main>
      <a class="card" href="https://www.rednote.com/explore/rednote001">
        <span>Saved RedNote idea</span>
      </a>
      <a href="https://example.com/not-a-note">External</a>
    </main>
    """

    report = inspect_html_for_candidates(
        html,
        base_url="https://www.rednote.com/user/profile/me?tab=fav",
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )

    assert report["total_links_count"] == 2
    assert report["candidate_note_links"] == ["https://www.rednote.com/explore/rednote001"]
    assert report["candidate_note_links_count"] == 1
    assert report["selector_strategy_results"]["rednote_note_link_strategy"] == 1
    assert report["selector_strategy_results"]["no_strategy_succeeded"] is False


def test_rednote_static_inspection_extracts_profile_detail_note_links():
    html = """
    <main>
      <a class="card" href="https://www.rednote.com/user/profile/profile001/note001?xsec_source=pc_collect">
        <span>Saved RedNote profile-detail note</span>
      </a>
      <a href="https://www.rednote.com/user/profile/author001">Author profile</a>
    </main>
    """

    report = inspect_html_for_candidates(
        html,
        base_url="https://www.rednote.com/user/profile/profile001?tab=fav",
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )

    assert report["candidate_note_links"] == [
        "https://www.rednote.com/user/profile/profile001/note001?xsec_source=pc_collect"
    ]
    assert report["raw_payloads"][0]["note_id"] == "note001"
    assert report["candidate_note_links_count"] == 1


def test_rednote_static_inspection_normalizes_relative_urls():
    html = """
    <main>
      <a class="note-card" href="/note/relative001">Relative RedNote note</a>
      <a href="/user/profile/me">Profile</a>
    </main>
    """

    report = inspect_html_for_candidates(
        html,
        base_url="https://www.rednote.com/user/profile/me?tab=fav",
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )

    assert report["candidate_note_links"] == ["https://www.rednote.com/note/relative001"]
    assert report["raw_payloads"][0]["source_url"] == "https://www.rednote.com/note/relative001"
    assert report["raw_payloads"][0]["note_id"] == "relative001"


def test_rednote_static_inspection_reports_clickable_cards_without_note_links():
    html = """
    <main>
      <div class="note-card" data-note-id="hidden001">
        <span>Saved card rendered without a normal anchor href</span>
      </div>
    </main>
    """

    report = inspect_html_for_candidates(
        html,
        base_url="https://www.rednote.com/user/profile/me?tab=fav",
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )

    strategies = report["selector_strategy_results"]
    assert report["candidate_note_links_count"] == 0
    assert report["candidate_card_count"] == 1
    assert strategies["rednote_clickable_card_strategy"] == 1
    assert strategies["no_strategy_succeeded"] is False


def test_rednote_static_inspection_reports_no_strategy_when_blank():
    report = inspect_html_for_candidates(
        "<main><p>No cards here</p></main>",
        base_url="https://www.rednote.com/user/profile/me?tab=fav",
        site_key="rednote",
        allowed_domains=("www.rednote.com", "rednote.com"),
    )

    assert report["total_links_count"] == 0
    assert report["candidate_note_links_count"] == 0
    assert report["candidate_card_count"] == 0
    assert report["selector_strategy_results"]["no_strategy_succeeded"] is True
