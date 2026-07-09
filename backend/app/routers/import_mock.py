from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Post
from app.schemas import ImportMockResponse
from app.services.mock_importer import import_sample_posts


router = APIRouter(prefix="/import", tags=["import"])


@router.post("/mock", response_model=ImportMockResponse)
def import_mock_posts(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImportMockResponse:
    imported_count, updated_count = import_sample_posts(db, settings.sample_posts_path)
    total = db.query(Post).count()
    return ImportMockResponse(
        imported_count=imported_count,
        updated_count=updated_count,
        total_in_database=total,
    )
