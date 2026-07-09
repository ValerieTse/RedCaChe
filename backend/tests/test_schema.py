from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Category, ImportRun, ImportSource, Post, ReviewStatus


def test_post_schema_has_required_columns():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    columns = {column["name"] for column in inspect(engine).get_columns(Post.__tablename__)}
    expected = {
        "id",
        "note_id",
        "source_url",
        "import_source",
        "import_run_id",
        "thumbnail_url",
        "raw_payload_json",
        "title",
        "author",
        "author_url",
        "collected_date",
        "imported_at",
        "last_seen_at",
        "raw_text",
        "ocr_text",
        "ai_summary",
        "category",
        "sub_category",
        "key_points_json",
        "step_by_step_json",
        "products_or_items_json",
        "useful_for",
        "tags_json",
        "my_notes",
        "review_status",
        "xhs_favorite_status",
        "backup_status",
        "restore_status",
        "unfavorite_status",
        "screenshot_paths_json",
        "operation_logs_json",
        "created_at",
        "updated_at",
    }

    assert expected.issubset(columns)


def test_import_run_schema_has_required_columns():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    columns = {column["name"] for column in inspect(engine).get_columns(ImportRun.__tablename__)}
    expected = {
        "import_run_id",
        "started_at",
        "finished_at",
        "status",
        "scanned_count",
        "imported_count",
        "duplicate_count",
        "failed_count",
        "stopped_reason",
        "error_message",
        "expected_domain",
        "received_url",
    }

    assert expected.issubset(columns)


def test_allowed_categories_and_review_statuses_are_explicit():
    assert [source.value for source in ImportSource] == ["mock", "xiaohongshu", "rednote"]
    assert [category.value for category in Category] == [
        "Beauty",
        "Fashion",
        "Fitness",
        "Work",
        "Study",
        "Life",
        "Food",
        "Travel",
        "Other",
    ]
    assert [status.value for status in ReviewStatus] == [
        "unreviewed",
        "keep",
        "remove_from_xhs",
        "evergreen",
        "archived",
    ]
