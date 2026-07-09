from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, Post, ReviewStatus
from app.schemas import PostListResponse, PostNotesUpdate, PostRead, PostStatusUpdate
from app.time import utc_now


router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
def list_posts(
    category: Category | None = Query(default=None),
    status: ReviewStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PostListResponse:
    query = db.query(Post)
    if category:
        query = query.filter(Post.category == category.value)
    if status:
        query = query.filter(Post.review_status == status.value)
    posts = query.order_by(Post.imported_at.desc()).all()
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
