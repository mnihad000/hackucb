"""
Arize observability status endpoint for RhetoriQ.

GET /api/arize/status  —  reports:
  - whether ARIZE_API_KEY and ARIZE_SPACE_ID are configured
  - whether the OTEL tracer provider is active
  - project name and space info
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/arize/status")
def arize_status() -> dict[str, Any]:
    """Report Arize tracing configuration and readiness."""
    from config import get_settings
    from services.arize_tracer import init_arize_tracing, is_ready

    settings = get_settings()
    api_key_set = bool(settings.ARIZE_API_KEY)
    space_id_set = bool(settings.ARIZE_SPACE_ID)

    # Attempt init if not already done (idempotent)
    active = init_arize_tracing() if (api_key_set and space_id_set) else False

    return {
        "configured": api_key_set and space_id_set,
        "api_key_set": api_key_set,
        "space_id_set": space_id_set,
        "tracing_active": is_ready(),
        "project_name": "RhetoriQ",
        "transport": "grpc",
        "endpoint": "https://otlp.arize.com/v1",
        "spans_emitted_for": [
            "planner/gemini or planner/groq  — one span per plan_investigation() call",
            "receipts/gemini                 — one span per receipts build",
            "family/gemini                   — one span per narrative family build",
            "counterpoints/gemini            — one span per claim counterpoint build",
            "grounding_eval                  — one span per final report (scores claim receipts)",
        ],
        "note": (
            "Tracing active — spans are being exported to Arize cloud."
            if active
            else "Tracing not active. Check ARIZE_API_KEY and ARIZE_SPACE_ID in .env."
        ),
    }
