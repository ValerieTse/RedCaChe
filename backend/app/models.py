from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.time import utc_now


class Category(str, Enum):
    BEAUTY = "Beauty"
    FASHION = "Fashion"
    FITNESS = "Fitness"
    WORK = "Work"
    STUDY = "Study"
    LIFE = "Life"
    FOOD = "Food"
    TRAVEL = "Travel"
    OTHER = "Other"


class ReviewStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    KEEP = "keep"
    REMOVE_FROM_XHS = "remove_from_xhs"
    EVERGREEN = "evergreen"
    ARCHIVED = "archived"


class XhsFavoriteStatus(str, Enum):
    FAVORITED = "favorited"
    UNFAVORITED = "unfavorited"
    UNKNOWN = "unknown"
    RESTORED = "restored"


class BackupStatus(str, Enum):
    RAW_SAVED = "raw_saved"
    SNAPSHOT_SAVED = "snapshot_saved"
    FULL_BACKUP_SAVED = "full_backup_saved"
    BACKUP_FAILED = "backup_failed"


class RestoreStatus(str, Enum):
    NOT_NEEDED = "not_needed"
    RESTORABLE = "restorable"
    RESTORED = "restored"
    UNAVAILABLE = "unavailable"


class UnfavoriteStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    QUEUED = "queued"
    PROCESSING = "processing"
    UNFAVORITED = "unfavorited"
    FAILED = "failed"
    SKIPPED = "skipped"


class ImportSource(str, Enum):
    MOCK = "mock"
    XIAOHONGSHU = "xiaohongshu"
    REDNOTE = "rednote"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    import_source: Mapped[str] = mapped_column(
        String(32), default=ImportSource.MOCK.value, nullable=False, index=True
    )
    import_run_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    author_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    collected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), default=Category.OTHER.value, nullable=False)
    sub_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    key_points_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    step_by_step_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    products_or_items_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    useful_for: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    my_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(32), default=ReviewStatus.UNREVIEWED.value, nullable=False, index=True
    )
    xhs_favorite_status: Mapped[str] = mapped_column(
        String(32), default=XhsFavoriteStatus.FAVORITED.value, nullable=False
    )
    backup_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    restore_status: Mapped[str] = mapped_column(
        String(32), default=RestoreStatus.NOT_NEEDED.value, nullable=False
    )
    unfavorite_status: Mapped[str] = mapped_column(
        String(32), default=UnfavoriteStatus.NOT_REQUESTED.value, nullable=False
    )
    screenshot_paths_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    operation_logs_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )


class ImportRun(Base):
    __tablename__ = "import_runs"

    import_run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    scanned_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stopped_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    received_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
