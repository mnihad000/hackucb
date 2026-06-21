"""
Browserbase status endpoint for RhetoriQ.

GET /api/browserbase/status  —  reports:
  - whether a valid API key + project ID are configured
  - whether playwright is installed (required for real-browser mode)
  - Redis verification cache count and recent results
  - backend mode (browserbase | httpx_fallback)
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


@router.get("/browserbase/status")
def browserbase_status() -> dict[str, Any]:
    """
    Report Browserbase configuration and verification cache state.
    """
    from services.verification_cache import get_verification_cache

    settings = get_settings()
    api_key_set = bool(settings.BROWSERBASE_API_KEY)
    project_id_set = bool(settings.BROWSERBASE_PROJECT_ID)
    playwright_ok = _playwright_available()
    real_browser_mode = api_key_set and playwright_ok

    cache = get_verification_cache()
    cached_count = cache.count()
    recent = cache.recent(limit=5)

    return {
        "configured": api_key_set and project_id_set,
        "api_key_set": api_key_set,
        "project_id_set": project_id_set,
        "playwright_available": playwright_ok,
        "backend": "browserbase" if real_browser_mode else "httpx_fallback",
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
        "note": (
            "Real browser verification active."
            if real_browser_mode
            else "Playwright not installed — falling back to httpx for URL verification. "
                 "Install playwright and run `playwright install chromium` to enable real browser mode."
        ),
    }
