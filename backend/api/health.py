from fastapi import APIRouter
from config import get_settings
from services.embedding_service import get_embedding_service

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "demo_mode": settings.DEMO_MODE,
        "version": "0.1.0",
    }


@router.get("/health/embeddings")
def embedding_health() -> dict:
    service = get_embedding_service()
    try:
        service.load_model()
        return {
            "status": "ok",
            "model": service.model_name,
            "dimension": service.dimension,
            "cache_enabled": service.cache_enabled,
        }
    except Exception as exc:
        return {
            "status": "error",
            "model": service.model_name,
            "dimension": service.dimension,
            "cache_enabled": service.cache_enabled,
            "error": str(exc),
        }
