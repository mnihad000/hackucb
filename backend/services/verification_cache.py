"""
Redis cache for Browserbase verification results.

Stores one verification result per URL with a 24-hour TTL.  Keeps
Browserbase sessions from re-opening the same page during a single
hackathon demo session and lets VerificationService serve report
pipelines with real statuses from prior Browserbase runs.

Key schema:
  rq:verify:{url_hash}  →  JSON blob (verification result dict)

The URL is MD5-hashed to keep key lengths predictable.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# 24 hours — long enough to survive the hackathon demo, short enough
# to pick up page changes between sessions.
_VERIFICATION_TTL = 86_400

_CACHE_KEY_PREFIX = "rq:verify:"


def _url_key(url: str) -> str:
    return _CACHE_KEY_PREFIX + hashlib.md5(url.encode()).hexdigest()


class VerificationCache:
    """
    Thin Redis wrapper for URL-level verification results.

    Falls back silently to a no-op when Redis is unavailable so the
    BrowserbaseAgent can run even without a Redis connection.
    """

    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client

    @property
    def available(self) -> bool:
        return self._redis is not None

    def get(self, url: str) -> dict[str, Any] | None:
        if not self._redis:
            return None
        try:
            raw = self._redis.get(_url_key(url))
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.warning("VerificationCache.get failed for %s: %s", url, exc)
        return None

    def set(self, url: str, result: dict[str, Any]) -> None:
        if not self._redis:
            return
        try:
            self._redis.setex(
                _url_key(url),
                _VERIFICATION_TTL,
                json.dumps(result, default=str),
            )
            logger.debug("Cached verification for %s", url)
        except Exception as exc:
            logger.warning("VerificationCache.set failed for %s: %s", url, exc)

    def delete(self, url: str) -> None:
        if not self._redis:
            return
        try:
            self._redis.delete(_url_key(url))
        except Exception as exc:
            logger.warning("VerificationCache.delete failed for %s: %s", url, exc)

    def count(self) -> int:
        if not self._redis:
            return 0
        try:
            return sum(1 for _ in self._redis.scan_iter(_CACHE_KEY_PREFIX + "*", count=500))
        except Exception:
            return 0

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return up to `limit` cached verification results (for the status endpoint)."""
        if not self._redis:
            return []
        try:
            results = []
            for key in self._redis.scan_iter(_CACHE_KEY_PREFIX + "*", count=500):
                raw = self._redis.get(key)
                if raw:
                    try:
                        results.append(json.loads(raw))
                    except Exception:
                        pass
                if len(results) >= limit:
                    break
            return results
        except Exception as exc:
            logger.warning("VerificationCache.recent failed: %s", exc)
            return []


_singleton: VerificationCache | None = None


def get_verification_cache() -> VerificationCache:
    """Return the process-wide VerificationCache singleton."""
    global _singleton
    if _singleton is None:
        from config import get_settings
        settings = get_settings()
        try:
            import redis as redis_lib
            client = redis_lib.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            client.ping()
            _singleton = VerificationCache(client)
            logger.info("VerificationCache connected to Redis")
        except Exception as exc:
            logger.warning("VerificationCache: Redis unavailable (%s) — running without cache", exc)
            _singleton = VerificationCache(None)
    return _singleton
