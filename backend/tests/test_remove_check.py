import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.crawler.importer import CrawlerService
from app.db import Base
from app.models import BackupStatus, Post, RestoreStatus, ReviewStatus, UnfavoriteStatus
from app.routers.posts import search_backed_up_posts
from app.routers.remove_check import archive_remove_check_posts, restore_remove_check_posts
from app.schemas import BulkPostIdsRequest


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _remove_post(title="Remove me", author="June"):
    return Post(
        note_id=f"note-{title}",
        source_url="https://www.rednote.com/explore/remove-me",
        open_url="https://www.rednote.com/explore/remove-me?xsec_token=abc",
        title=title,
        author=author,
        review_status=ReviewStatus.REMOVE_FROM_XHS.value,
    )


def test_archive_remove_check_posts_creates_backup_and_archives(tmp_path):
    db = _session()
    post = _remove_post()
    db.add(post)
    db.commit()
    db.refresh(post)

    result = archive_remove_check_posts(
        BulkPostIdsRequest(post_ids=[post.id]),
        Settings(backup_root=tmp_path),
        db,
    )
    db.refresh(post)

    assert result.archived_count == 1
    assert result.backed_up_count == 1
    assert post.review_status == ReviewStatus.ARCHIVED.value
    assert post.backup_status == BackupStatus.RAW_SAVED.value
    assert post.restore_status == RestoreStatus.RESTORABLE.value
    assert post.unfavorite_status == UnfavoriteStatus.SKIPPED.value
    assert (tmp_path / "raw_html" / f"{post.note_id}.json").exists()


def test_restore_remove_check_posts_returns_to_keep():
    db = _session()
    post = _remove_post()
    db.add(post)
    db.commit()
    db.refresh(post)

    result = restore_remove_check_posts(BulkPostIdsRequest(post_ids=[post.id]), db)
    db.refresh(post)

    assert result.restored_count == 1
    assert post.review_status == ReviewStatus.KEEP.value
    assert post.unfavorite_status == UnfavoriteStatus.NOT_REQUESTED.value


def test_backup_search_fuzzy_matches_backed_up_posts():
    db = _session()
    post = _remove_post(title="Paris cafe guide", author="Avery")
    post.backup_status = BackupStatus.RAW_SAVED.value
    db.add(post)
    db.commit()

    response = search_backed_up_posts(q="cafe", db=db)

    assert response.total == 1
    assert response.posts[0].title == "Paris cafe guide"


def test_confirm_unfavorite_requires_explicit_confirmation():
    service = CrawlerService(Settings())

    result = asyncio.run(service.confirm_unfavorite_posts(_session(), [1], confirm=False))

    assert result["stopped_reason"] == "confirmation_required"
    assert result["unfavorited_count"] == 0
