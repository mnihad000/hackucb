"""
Browserbase status endpoint for RhetoriQ.

GET /api/browserbase/status  —  reports:
  - whether a valid API key + project ID are configured
  - whether playwright is installed (required for real-browser mode)
  - page-fetch mode (browserbase | httpx_fallback)
  - Redis verification cache count and recent results
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _browserbase_sdk_available() -> bool:
    try:
        import browserbase  # noqa: F401
        return True
    except ImportError:
        return False


@router.get("/browserbase/status")
def browserbase_status() -> dict[str, Any]:
    """
    Report Browserbase configuration, page-fetch mode, and verification cache state.
    """
    from services.verification_cache import get_verification_cache

    settings = get_settings()
    api_key_set = bool(settings.BROWSERBASE_API_KEY)
    project_id_set = bool(settings.BROWSERBASE_PROJECT_ID)
    playwright_ok = _playwright_available()
    sdk_ok = _browserbase_sdk_available()
    real_browser_mode = api_key_set and project_id_set and playwright_ok and sdk_ok

    cache = get_verification_cache()
    cached_count = cache.count()
    recent = cache.recent(limit=5)

    if real_browser_mode:
        fetch_note = (
            "Browserbase real-browser fetching active — every article opened in a "
            "cloud Chromium session before it is cited."
        )
        fetch_backend = "browserbase"
    else:
        missing: list[str] = []
        if not api_key_set:
            missing.append("BROWSERBASE_API_KEY")
        if not project_id_set:
            missing.append("BROWSERBASE_PROJECT_ID")
        if not sdk_ok:
            missing.append("browserbase SDK (pip install browserbase)")
        if not playwright_ok:
            missing.append("playwright (pip install playwright && playwright install chromium)")
        fetch_note = f"httpx fallback active. Missing: {', '.join(missing)}."
        fetch_backend = "httpx_fallback"

    return {
        "configured": real_browser_mode,
        "api_key_set": api_key_set,
        "project_id_set": project_id_set,
        "playwright_available": playwright_ok,
        "browserbase_sdk_available": sdk_ok,
        "fetch_backend": fetch_backend,
        "note": fetch_note,
        "verification_cache": {
            "redis_connected": cache.available,
            "cached_urls": cached_count,
            "recent": [
                {
                    "url": r.get("url", ""),
                    "status": r.get("verified_status", ""),
                    "checked_at": r.get("checked_at", ""),
                }
                for r in recent
            ],
        },
    }
