from fastapi import APIRouter
from config import get_settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "demo_mode": settings.DEMO_MODE,
        "version": "0.1.0",
    }
