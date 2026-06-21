from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from config import get_settings

router = APIRouter(prefix="/api")


def _band_sdk_available() -> bool:
    try:
        from band import BandLink  # noqa: F401

        return True
    except Exception:
        return False


@router.get("/band/status")
def band_status() -> dict[str, Any]:
    settings = get_settings()
    api_key_set = bool(settings.BAND_API_KEY)
    agent_id_set = bool(settings.BAND_AGENT_ID)
    room_id_set = bool(settings.BAND_ROOM_ID)
    sdk_available = _band_sdk_available()

    return {
        "configured": api_key_set and agent_id_set and sdk_available,
        "api_key_set": api_key_set,
        "agent_id_set": agent_id_set,
        "room_id_set": room_id_set,
        "sdk_available": sdk_available,
        "rest_url": settings.BAND_REST_URL,
        "ws_url": settings.BAND_WS_URL,
        "mode": "reuse_room" if room_id_set else "create_chat_per_investigation",
        "events_emitted_for": [
            "Analyst Agent",
            "Skeptic Agent",
            "Receipts Agent",
            "Counter-Narrative Agent",
            "Safety Agent",
            "Final Language Agent",
        ],
        "note": (
            "Band sync active. New agent-debate artifacts are posted into a Band chat."
            if api_key_set and agent_id_set and sdk_available
            else "Band sync inactive. Set BAND_API_KEY and BAND_AGENT_ID, and install band-sdk."
        ),
    }
