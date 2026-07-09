from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Post, ReviewStatus
from app.schemas import DailyReviewResponse


router = APIRouter(prefix="/review", tags=["review"])


@router.get("/daily", response_model=DailyReviewResponse)
def get_daily_review(
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
) -> DailyReviewResponse:
    posts = (
        db.query(Post)
        .filter(Post.review_status == ReviewStatus.UNREVIEWED.value)
        .order_by(Post.imported_at.desc())
        .limit(limit)
        .all()
    )
    return DailyReviewResponse(review_date=date.today(), count=len(posts), posts=posts)
