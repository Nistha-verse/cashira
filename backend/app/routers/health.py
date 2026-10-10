from fastapi import APIRouter

from .helpers import response

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return response({"status": "ok", "service": "cashira-backend"})
