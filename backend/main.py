from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.ingest import router as ingest_router
from api.narratives import router as narratives_router
from api.trending import router as trending_router
from api.trending import _service as trending_service
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="RhetoriQ API",
    description="Civic AI narrative intelligence platform. Demo mode active.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(narratives_router)
app.include_router(trending_router)


@app.on_event("startup")
def warm_trending_feed() -> None:
    if settings.DEMO_MODE:
        return
    trending_service.ensure_warm_async()


@app.get("/")
def root() -> dict:
    return {
        "name": "RhetoriQ",
        "demo_mode": settings.DEMO_MODE,
        "docs": "/docs",
        "endpoints": [
            "GET    /health",
            "GET    /api/gdelt/search",
            "POST   /api/ingest",
            "GET    /api/store/status",
            "DELETE /api/store",
            "GET    /api/narratives",
            "GET    /api/narratives/{id}",
            "GET    /api/narratives/{id}/timeline",
            "POST   /api/investigate  (query_text -> planner artifact)",
            "GET    /api/investigations  (list recent persisted investigations)",
            "GET    /api/investigations/{id}  (load persisted investigation workspace)",
            "POST   /api/investigations/{id}/retrieve  (run retriever agent)",
            "POST   /api/investigations/{id}/source-diversity  (build deterministic source diversity artifact)",
            "POST   /api/investigations/{id}/timeline  (build deterministic timeline artifact)",
            "POST   /api/investigations/{id}/counter-narratives  (build counter-frame artifact)",
            "POST   /api/investigations/{id}/family  (build narrative family artifact)",
            "POST   /api/investigations/{id}/analyst  (build synthesis artifact)",
            "POST   /api/investigations/{id}/claim-counterpoints  (build claim-level counterpoint artifact)",
            "POST   /api/investigations/{id}/receipts  (build claim grounding artifact)",
            "POST   /api/investigations/{id}/agent-debate  (build readable multi-agent debate summary)",
            "POST   /api/investigations/{id}/report  (assemble final investigation report)",
            "GET    /api/graph/{narrative_id}",
            "GET    /api/receipts/{narrative_id}",
            "GET    /api/mutations/{narrative_id}",
            "GET    /api/trending",
            "GET    /api/trending/status",
            "POST   /api/trending/refresh",
            "POST   /api/trending/{topic_id}/investigate",
        ],
    }
