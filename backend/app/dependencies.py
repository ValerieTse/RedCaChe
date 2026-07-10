from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.services.config_service import build_effective_settings


def get_effective_settings(db: Session = Depends(get_db)) -> Settings:
    """Site-aware settings: env infrastructure overlaid with the DB config."""
    return build_effective_settings(db)
