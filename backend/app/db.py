from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _run_sqlite_additive_migrations()


def _run_sqlite_additive_migrations() -> None:
    inspector = inspect(engine)
    if "posts" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("posts")}
    additions = {
        "import_source": "ALTER TABLE posts ADD COLUMN import_source VARCHAR(32) DEFAULT 'mock' NOT NULL",
        "import_run_id": "ALTER TABLE posts ADD COLUMN import_run_id VARCHAR(64)",
        "thumbnail_url": "ALTER TABLE posts ADD COLUMN thumbnail_url VARCHAR(2048)",
        "raw_payload_json": "ALTER TABLE posts ADD COLUMN raw_payload_json JSON DEFAULT '{}' NOT NULL",
        "open_url": "ALTER TABLE posts ADD COLUMN open_url VARCHAR(2048)",
        "category_is_manual": (
            "ALTER TABLE posts ADD COLUMN category_is_manual BOOLEAN DEFAULT 0 NOT NULL"
        ),
        "enrichment_status": (
            "ALTER TABLE posts ADD COLUMN enrichment_status VARCHAR(32) DEFAULT 'not_enriched' NOT NULL"
        ),
        "enriched_at": "ALTER TABLE posts ADD COLUMN enriched_at DATETIME",
        "from_initial_import": (
            "ALTER TABLE posts ADD COLUMN from_initial_import BOOLEAN DEFAULT 0 NOT NULL"
        ),
    }
    with engine.begin() as connection:
        for column_name, statement in additions.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))

    if "import_runs" in inspector.get_table_names():
        run_columns = {column["name"] for column in inspector.get_columns("import_runs")}
        run_additions = {
            "expected_domain": "ALTER TABLE import_runs ADD COLUMN expected_domain VARCHAR(255)",
            "received_url": "ALTER TABLE import_runs ADD COLUMN received_url VARCHAR(2048)",
        }
        with engine.begin() as connection:
            for column_name, statement in run_additions.items():
                if column_name not in run_columns:
                    connection.execute(text(statement))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
