"""
Redis status endpoint for RhetoriQ.

Exposes a single GET /api/redis/status that reports the health and utilization
of every Redis layer in use: investigation cache (RedisJSON), vector store
(VADD/VSIM), and phrase counter (sorted sets).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def _build_cache_stats() -> dict[str, Any]:
    from services.investigation_cache import get_investigation_cache

    cache = get_investigation_cache()
    if cache is None:
        return {"available": False, "reason": "disabled or Redis unreachable"}

    try:
        stats = cache.get_stats()
        cached_list = cache.list_cached_investigations(limit=20)
        return {
            "available": True,
            "hit_rate": stats["hit_rate"],
            "hits": stats["hits"],
            "misses": stats["misses"],
            "writes": stats["writes"],
            "cached_investigations": len(cached_list),
            "sample": [
                {"id": e["investigation_id"], "status": e["status"], "ttl_seconds": e["ttl_seconds"]}
                for e in cached_list[:5]
            ],
        }
    except Exception as exc:
        logger.warning("Cache stats error: %s", exc)
        return {"available": False, "reason": str(exc)}


def _build_vector_stats() -> dict[str, Any]:
    from services.redis_vector_store import get_redis_vector_store

    store = get_redis_vector_store()
    if store is None:
        return {"available": False, "reason": "disabled or Redis unreachable"}

    try:
        health = store.health_check()
        return {
            "available": health.get("connected", False),
            "document_count": health.get("document_count", 0),
            "embedding_model": health.get("embedding_model", ""),
            "embedding_dimension": health.get("embedding_dimension", 0),
            "vset_key": health.get("vset_key", ""),
        }
    except Exception as exc:
        logger.warning("Vector store stats error: %s", exc)
        return {"available": False, "reason": str(exc)}


def _build_phrase_stats() -> dict[str, Any]:
    from services.redis_store import PhraseStore

    settings = get_settings()
    try:
        store = PhraseStore(redis_url=settings.REDIS_URL)
        top = store.get_top_phrases(10)
        return {
            "available": store.using_redis,
            "backend": "redis" if store.using_redis else "in-memory",
            "top_phrases": [{"phrase": p, "mentions": c} for p, c in top],
        }
    except Exception as exc:
        logger.warning("Phrase store stats error: %s", exc)
        return {"available": False, "reason": str(exc)}


def _build_memory_stats() -> dict[str, Any]:
    from services.redis_memory import get_redis_memory_service

    memory = get_redis_memory_service()
    try:
        health = memory.health_check()
        return {
            "available": health.get("connected", False),
            "counts": health.get("counts", {}),
            "vectorsets": health.get("vectorsets", {}),
            "reason": health.get("reason"),
        }
    except Exception as exc:
        logger.warning("Redis memory stats error: %s", exc)
        return {"available": False, "reason": str(exc)}


def _build_connection_stats() -> dict[str, Any]:
    settings = get_settings()
    try:
        import redis as redis_lib

        client = redis_lib.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        ping = client.ping()
        info = client.info("server")
        return {
            "connected": ping,
            "redis_version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
        }
    except Exception as exc:
        return {"connected": False, "reason": str(exc)}


@router.get("/redis/status")
def redis_status() -> dict[str, Any]:
    """
    Report the health and utilization of all Redis layers:
    - connection: ping + server info
    - investigation_cache: RedisJSON workspace cache hit/miss/write stats
    - vector_store: VADD/VSIM vectorset doc count + embedding info
    - phrase_store: sorted-set phrase counters + top phrases
    """
    return {
        "connection": _build_connection_stats(),
        "investigation_cache": _build_cache_stats(),
        "vector_store": _build_vector_stats(),
        "memory": _build_memory_stats(),
        "phrase_store": _build_phrase_stats(),
    }


@router.get("/health/redis")
def redis_health() -> dict[str, Any]:
    status = redis_status()
    return {
        "status": "ok" if status["connection"].get("connected") else "error",
        **status,
    }
