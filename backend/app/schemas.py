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
    sub_category: Optional[str] = None
    key_points_json: list[str] = Field(default_factory=list)
    step_by_step_json: list[str] = Field(default_factory=list)
    products_or_items_json: list[str] = Field(default_factory=list)
    useful_for: Optional[str] = None
    tags_json: list[str] = Field(default_factory=list)
    my_notes: Optional[str] = None
    review_status: str
    xhs_favorite_status: str
    backup_status: Optional[str] = None
    restore_status: str
    unfavorite_status: str
    screenshot_paths_json: list[str] = Field(default_factory=list)
    operation_logs_json: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    total: int
    posts: list[PostRead]


class PostStatusUpdate(BaseModel):
    review_status: ReviewStatus


class PostNotesUpdate(BaseModel):
    my_notes: Optional[str] = None


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


class ImportVisibleFavoritesRequest(BaseModel):
    favorites_url: Optional[str] = None
    max_scrolls: Optional[int] = Field(default=None, ge=1, le=100)


class ImportVisibleFavoritesResponse(BaseModel):
    import_run_id: str
    scanned_count: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    stopped_reason: Optional[str] = None
    error_message: Optional[str] = None


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


class DailyReviewResponse(BaseModel):
    review_date: date
    count: int
    posts: list[PostRead]


class EvergreenExportRequest(BaseModel):
    post_ids: Optional[list[int]] = None


class ExportResponse(BaseModel):
    output_path: str
    exported_count: int
    skipped_count: int


class EnumSnapshot(BaseModel):
    categories: list[Category]
    import_sources: list[ImportSource]
    review_statuses: list[ReviewStatus]
    xhs_favorite_statuses: list[XhsFavoriteStatus]
    backup_statuses: list[BackupStatus]
    restore_statuses: list[RestoreStatus]
    unfavorite_statuses: list[UnfavoriteStatus]
