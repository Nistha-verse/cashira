from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..services.alerts import effective_as_of
from .helpers import response

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    return response({"status": "ok", "service": "cashira-backend", "forecaster": "prophet" if settings.use_prophet else "baseline", "anchor_enabled": settings.chain_enabled, "data_as_of": effective_as_of(db).isoformat(), "version": settings.app_version})
