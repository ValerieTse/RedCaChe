from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    BackupStatus,
    Category,
    ImportSource,
    RestoreStatus,
    ReviewStatus,
    UnfavoriteStatus,
    XhsFavoriteStatus,
)


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: str
    source_url: str
    open_url: Optional[str] = None
    import_source: str = ImportSource.MOCK.value
    import_run_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    raw_payload_json: dict = Field(default_factory=dict)
    title: str
    author: Optional[str] = None
    author_url: Optional[str] = None
    collected_date: Optional[date] = None
    imported_at: datetime
    last_seen_at: Optional[datetime] = None
    raw_text: Optional[str] = None
    ocr_text: Optional[str] = None
    ai_summary: Optional[str] = None
    category: str
    category_is_manual: bool = False
    sub_category: Optional[str] = None
    key_points_json: list[str] = Field(default_factory=list)
    step_by_step_json: list[str] = Field(default_factory=list)
    products_or_items_json: list[str] = Field(default_factory=list)
    useful_for: Optional[str] = None
    tags_json: list[str] = Field(default_factory=list)
    my_notes: Optional[str] = None
    review_status: str
    from_initial_import: bool = False
    xhs_favorite_status: str
    backup_status: Optional[str] = None
    restore_status: str
    unfavorite_status: str
    screenshot_paths_json: list[str] = Field(default_factory=list)
    operation_logs_json: list[dict] = Field(default_factory=list)
    enrichment_status: str = "not_enriched"
    enriched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    total: int
    posts: list[PostRead]


class PostStatusUpdate(BaseModel):
    review_status: ReviewStatus


class PostNotesUpdate(BaseModel):
    my_notes: Optional[str] = None


class PostCategoryUpdate(BaseModel):
    category: str


class BulkPostIdsRequest(BaseModel):
    post_ids: list[int] = Field(default_factory=list)


class ConfirmUnfavoriteRequest(BaseModel):
    post_ids: list[int] = Field(default_factory=list)
    confirm: bool = False


class ConfirmUnfavoriteResponse(BaseModel):
    requested_count: int
    backed_up_count: int
    unfavorited_count: int
    restored_count: int = 0
    archived_count: int = 0
    failed_count: int
    stopped_reason: Optional[str] = None
    backup_paths: list[str] = Field(default_factory=list)
    per_post_results: list[dict] = Field(default_factory=list)


class ImportMockResponse(BaseModel):
    imported_count: int
    updated_count: int
    total_in_database: int


class CrawlerOpenLoginRequest(BaseModel):
    login_url: Optional[str] = None


class CrawlerOpenLoginResponse(BaseModel):
    status: str
    message: str
    login_url: str
    profile_dir: str
    active_site_key: str
    active_site_display_name: str
    active_base_url: str
    using_system_chrome: bool = False
    launch_fallback_reason: Optional[str] = None


class CrawlerOpenPostRequest(BaseModel):
    post_id: Optional[int] = None
    url: Optional[str] = None


class CrawlerOpenPostResponse(BaseModel):
    status: str
    message: str
    post_id: Optional[int] = None
    requested_url: Optional[str] = None
    current_url: Optional[str] = None
    detected_state: Optional[str] = None
    profile_dir: str
    active_site_key: str
    active_site_display_name: str
    active_base_url: str
    using_system_chrome: bool = False
    stopped_reason: Optional[str] = None
    expected_domain: Optional[str] = None
    received_url: Optional[str] = None
    launch_fallback_reason: Optional[str] = None


class CrawlerCheckLoginRequest(BaseModel):
    url: Optional[str] = None


class CrawlerCheckLoginResponse(BaseModel):
    active_site_key: str
    active_site_display_name: str
    active_base_url: str
    current_url: str
    page_title: str
    detected_state: str
    visible_text_sample: str
    profile_dir: str
    using_system_chrome: bool
    cookies_count_for_domain: Optional[int] = None
    local_storage_keys_count: Optional[int] = None
    screenshot_path: Optional[str] = None


class CrawlerDebugProfileResponse(BaseModel):
    active_site_key: str
    active_site_display_name: str
    active_base_url: str
    profile_dir: str
    profile_dir_exists: bool
    profile_dir_size_bytes: int
    common_profile_files: dict[str, bool]
    system_chrome_enabled: bool
    using_system_chrome: bool
    system_chrome_launch_succeeded_last_time: Optional[bool] = None
    launch_fallback_reason: Optional[str] = None
    last_browser_launch_timestamp: Optional[str] = None
    last_login_check_result: Optional[dict] = None


class CrawlerInspectPageRequest(BaseModel):
    url: str
    max_scrolls: int = Field(default=2, ge=0, le=100)
    save_debug_screenshot: bool = True
    save_debug_html: bool = True


class CrawlerInspectPageResponse(BaseModel):
    active_site_key: str
    active_base_url: str
    profile_dir: str
    current_url: str
    page_title: str
    detected_state: str
    visible_text_sample: str
    body_text_length: int
    total_links_count: int
    all_link_href_samples: list[str] = Field(default_factory=list)
    candidate_note_links: list[str] = Field(default_factory=list)
    candidate_note_links_count: int
    candidate_card_count: int
    selector_strategy_results: dict
    debug_screenshot_paths: list[str] = Field(default_factory=list)
    debug_html_path: Optional[str] = None
    debug_text_path: Optional[str] = None


class CrawlerEnrichPostsRequest(BaseModel):
    post_ids: Optional[list[int]] = None
    import_run_id: Optional[str] = None
    status_filter: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    delay_seconds: float = Field(default=1.5, ge=0, le=30)


class CrawlerEnrichPostsResponse(BaseModel):
    processed_count: int
    enriched_count: int
    skipped_count: int
    failed_count: int
    stopped_reason: Optional[str] = None
    per_post_results: list[dict] = Field(default_factory=list)


class CrawlerInspectPostDetailRequest(BaseModel):
    post_id: Optional[int] = None
    url: Optional[str] = None


class CrawlerInspectPostDetailResponse(BaseModel):
    active_site_key: str
    active_base_url: str
    profile_dir: str
    current_url: str
    detected_state: str
    page_title: str
    visible_text_sample: str
    extracted_title: str
    extracted_author: Optional[str] = None
    extracted_body_text: str
    extracted_hashtags: list[str] = Field(default_factory=list)
    extraction_strategy_results: dict = Field(default_factory=dict)
    debug_screenshot_path: Optional[str] = None
    debug_html_path: Optional[str] = None


class ImportVisibleFavoritesRequest(BaseModel):
    favorites_url: Optional[str] = None
    max_scrolls: Optional[int] = Field(default=None, ge=1, le=500)
    initial_review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    headless: bool = False


class ImportVisibleFavoritesResponse(BaseModel):
    import_run_id: str
    scanned_count: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    stopped_reason: Optional[str] = None
    error_message: Optional[str] = None
    expected_domain: Optional[str] = None
    received_url: Optional[str] = None


class ImportRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    import_run_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    scanned_count: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    stopped_reason: Optional[str] = None
    error_message: Optional[str] = None
    expected_domain: Optional[str] = None
    received_url: Optional[str] = None


class DailyReviewResponse(BaseModel):
    review_date: date
    window_start: datetime
    window_end: datetime
    window_mode: str
    timezone: str
    cutoff_local: str
    count: int
    posts: list[PostRead]


class EvergreenExportRequest(BaseModel):
    post_ids: Optional[list[int]] = None


class DailyReviewExportRequest(BaseModel):
    post_ids: list[int] = Field(default_factory=list)


class ExportResponse(BaseModel):
    output_path: str
    exported_count: int
    skipped_count: int


class CustomCategoryInput(BaseModel):
    name: str
    keywords: list[str] = Field(default_factory=list)


class AppConfigUpdate(BaseModel):
    site_mode: Optional[str] = None
    favorites_url: Optional[str] = None
    selected_category_slugs: Optional[list[str]] = None
    custom_categories: Optional[list[CustomCategoryInput]] = None
    onboarding_completed: Optional[bool] = None
    locale: Optional[str] = None


class AppConfigRead(BaseModel):
    site_mode: str
    favorites_url: Optional[str] = None
    selected_category_slugs: list[str] = Field(default_factory=list)
    custom_categories: list[dict] = Field(default_factory=list)
    onboarding_completed: bool
    locale: str
    active_site_key: str
    active_site_display_name: str
    active_explore_url: str
    active_domain: str


class CategoryRead(BaseModel):
    slug: str
    label_zh: str
    label_en: str
    is_custom: bool = False


class PresetCategoryRead(BaseModel):
    slug: str
    label_zh: str
    label_en: str
    keyword_count: int


class DetectFavoritesUrlResponse(BaseModel):
    status: str
    favorites_url: Optional[str] = None
    detected_state: Optional[str] = None
    message: Optional[str] = None


class ReclassifyResponse(BaseModel):
    scanned_count: int
    updated_count: int


class EnumSnapshot(BaseModel):
    categories: list[Category]
    import_sources: list[ImportSource]
    review_statuses: list[ReviewStatus]
    xhs_favorite_statuses: list[XhsFavoriteStatus]
    backup_statuses: list[BackupStatus]
    restore_statuses: list[RestoreStatus]
    unfavorite_statuses: list[UnfavoriteStatus]
