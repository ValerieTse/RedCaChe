from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Post, ReviewStatus, UnfavoriteStatus
from app.schemas import (
    PostCategoryUpdate,
    PostListResponse,
    PostNotesUpdate,
    PostRead,
    PostStatusUpdate,
)
from app.services.config_service import active_categories, get_or_create_config
from app.time import utc_now


router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
def list_posts(
    category: str | None = Query(default=None),
    status: ReviewStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PostListResponse:
    query = db.query(Post)
    if category:
        query = query.filter(Post.category == category)
    if status:
        query = query.filter(Post.review_status == status.value)
    posts = query.order_by(Post.imported_at.desc(), Post.id.desc()).all()
    return PostListResponse(total=len(posts), posts=posts)


@router.get("/backups/search", response_model=PostListResponse)
def search_backed_up_posts(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PostListResponse:
    query = db.query(Post).filter(
        or_(
            Post.backup_status.isnot(None),
            Post.review_status == ReviewStatus.ARCHIVED.value,
            Post.unfavorite_status.in_(
                [
                    UnfavoriteStatus.QUEUED.value,
                    UnfavoriteStatus.PROCESSING.value,
                    UnfavoriteStatus.UNFAVORITED.value,
                    UnfavoriteStatus.FAILED.value,
                    UnfavoriteStatus.SKIPPED.value,
                ]
            ),
        )
    )
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Post.title.ilike(pattern),
                Post.author.ilike(pattern),
                Post.note_id.ilike(pattern),
                Post.source_url.ilike(pattern),
                Post.open_url.ilike(pattern),
                Post.my_notes.ilike(pattern),
            )
        )
    posts = query.order_by(Post.updated_at.desc(), Post.id.desc()).all()
    return PostListResponse(total=len(posts), posts=posts)


@router.get("/{post_id}", response_model=PostRead)
def get_post(post_id: int, db: Session = Depends(get_db)) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.patch("/{post_id}/status", response_model=PostRead)
def update_post_status(
    post_id: int,
    payload: PostStatusUpdate,
    db: Session = Depends(get_db),
) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    post.review_status = payload.review_status.value
    post.updated_at = utc_now()
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.patch("/{post_id}/notes", response_model=PostRead)
def update_post_notes(
    post_id: int,
    payload: PostNotesUpdate,
    db: Session = Depends(get_db),
) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    post.my_notes = payload.my_notes
    post.updated_at = utc_now()
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.patch("/{post_id}/category", response_model=PostRead)
def update_post_category(
    post_id: int,
    payload: PostCategoryUpdate,
    db: Session = Depends(get_db),
) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    valid_slugs = {c["slug"] for c in active_categories(get_or_create_config(db))}
    if payload.category not in valid_slugs:
        raise HTTPException(status_code=400, detail="Unknown category")
    post.category = payload.category
    post.sub_category = None
    post.category_is_manual = True
    post.updated_at = utc_now()
    db.add(post)
    db.commit()
    db.refresh(post)
    return post
