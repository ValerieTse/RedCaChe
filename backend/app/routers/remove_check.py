from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.crawler.importer import CrawlerService
from app.db import get_db
from app.models import Post, RestoreStatus, ReviewStatus, UnfavoriteStatus
from app.schemas import BulkPostIdsRequest, ConfirmUnfavoriteRequest, ConfirmUnfavoriteResponse, PostListResponse
from app.services.backup_service import backup_post_to_json
from app.time import utc_now


router = APIRouter(prefix="/remove-check", tags=["remove-check"])


def get_crawler_service(settings: Settings = Depends(get_settings)) -> CrawlerService:
    return CrawlerService(settings)


@router.get("/posts", response_model=PostListResponse)
def list_remove_check_posts(db: Session = Depends(get_db)) -> PostListResponse:
    posts = (
        db.query(Post)
        .filter(Post.review_status == ReviewStatus.REMOVE_FROM_XHS.value)
        .order_by(Post.imported_at.desc(), Post.id.desc())
        .all()
    )
    return PostListResponse(total=len(posts), posts=posts)


@router.post("/restore", response_model=ConfirmUnfavoriteResponse)
def restore_remove_check_posts(
    payload: BulkPostIdsRequest,
    db: Session = Depends(get_db),
) -> ConfirmUnfavoriteResponse:
    posts = _select_remove_posts(db, payload.post_ids)
    restored_count = 0
    results: list[dict] = []
    for post in posts:
        post.review_status = ReviewStatus.KEEP.value
        post.unfavorite_status = UnfavoriteStatus.NOT_REQUESTED.value
        post.updated_at = utc_now()
        db.add(post)
        restored_count += 1
        results.append({"post_id": post.id, "status": "restored"})
    db.commit()
    return ConfirmUnfavoriteResponse(
        requested_count=len(payload.post_ids),
        backed_up_count=0,
        unfavorited_count=0,
        restored_count=restored_count,
        failed_count=0,
        per_post_results=results,
    )


@router.post("/archive", response_model=ConfirmUnfavoriteResponse)
def archive_remove_check_posts(
    payload: BulkPostIdsRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> ConfirmUnfavoriteResponse:
    posts = _select_remove_posts(db, payload.post_ids)
    backup_paths: list[str] = []
    results: list[dict] = []
    archived_count = 0
    failed_count = 0
    for post in posts:
        try:
            backup_path = backup_post_to_json(post, settings.backup_root)
            backup_paths.append(str(backup_path))
            post.review_status = ReviewStatus.ARCHIVED.value
            post.restore_status = RestoreStatus.RESTORABLE.value
            post.unfavorite_status = UnfavoriteStatus.SKIPPED.value
            post.updated_at = utc_now()
            db.add(post)
            archived_count += 1
            results.append({"post_id": post.id, "status": "archived", "backup_path": str(backup_path)})
        except Exception as exc:
            failed_count += 1
            results.append({"post_id": post.id, "status": "failed", "reason": str(exc)})
    db.commit()
    return ConfirmUnfavoriteResponse(
        requested_count=len(payload.post_ids),
        backed_up_count=len(backup_paths),
        unfavorited_count=0,
        archived_count=archived_count,
        failed_count=failed_count,
        backup_paths=backup_paths,
        per_post_results=results,
    )


@router.post("/confirm-unfavorite", response_model=ConfirmUnfavoriteResponse)
async def confirm_unfavorite_posts(
    payload: ConfirmUnfavoriteRequest,
    db: Session = Depends(get_db),
    service: CrawlerService = Depends(get_crawler_service),
) -> dict:
    if not payload.post_ids:
        raise HTTPException(status_code=400, detail="No posts selected")
    return await service.confirm_unfavorite_posts(db, payload.post_ids, confirm=payload.confirm)


def _select_remove_posts(db: Session, post_ids: list[int]) -> list[Post]:
    if not post_ids:
        return []
    return (
        db.query(Post)
        .filter(Post.id.in_(post_ids), Post.review_status == ReviewStatus.REMOVE_FROM_XHS.value)
        .order_by(Post.imported_at.desc(), Post.id.desc())
        .all()
    )
