from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.schemas import EvergreenExportRequest, ExportResponse
from app.services.obsidian_exporter import export_daily_review, export_evergreen


router = APIRouter(prefix="/export/obsidian", tags=["export"])


@router.post("/daily", response_model=ExportResponse)
def export_daily(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ExportResponse:
    if not settings.export_daily_review_enabled:
        raise HTTPException(status_code=400, detail="Daily review export is disabled")
    output_path, exported_count, skipped_count = export_daily_review(db, settings.obsidian_vault_path)
    return ExportResponse(
        output_path=str(output_path),
        exported_count=exported_count,
        skipped_count=skipped_count,
    )


@router.post("/evergreen", response_model=ExportResponse)
def export_evergreen_notes(
    payload: EvergreenExportRequest | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ExportResponse:
    post_ids = payload.post_ids if payload else None
    output_path, exported_count, skipped_count = export_evergreen(
        db, settings.obsidian_vault_path, post_ids=post_ids
    )
    return ExportResponse(
        output_path=str(output_path),
        exported_count=exported_count,
        skipped_count=skipped_count,
    )
