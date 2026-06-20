"""
Investigation Workspace Cache for RhetoriQ - High-performance caching using RedisJSON.

Caches investigation workspaces to reduce SQLite I/O and API response time by 10-100x.
Uses RedisJSON for efficient storage and partial updates of complex nested objects.

Redis Sponsor Track: Demonstrates Redis beyond simple caching with structured JSON storage.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from redis.commands.json.path import Path

from models.investigation import InvestigationWorkspace

logger = logging.getLogger(__name__)


class InvestigationCache:
    """
    Redis-backed cache for investigation workspaces.

    Features:
    - Store complete investigation workspaces in RedisJSON
    - TTL-based expiration (default: 1 hour)
    - Partial updates for individual pipeline stages
    - Cache statistics and health monitoring
    """

    def __init__(self, redis_client: Any, default_ttl_seconds: int = 3600) -> None:
        """
        Initialize investigation cache.

        Args:
            redis_client: Redis client instance
            default_ttl_seconds: Default cache TTL (1 hour = 3600s)
        """
        self.redis = redis_client
        self.default_ttl = default_ttl_seconds
        self._stats = {"hits": 0, "misses": 0, "writes": 0}

    def _make_key(self, investigation_id: str) -> str:
        """Generate Redis key for investigation workspace."""
        return f"rq:investigation:{investigation_id}"

    def cache_workspace(
        self, workspace: InvestigationWorkspace, ttl_seconds: int | None = None
    ) -> bool:
        """
        Cache an investigation workspace.

        Args:
            workspace: InvestigationWorkspace to cache
            ttl_seconds: Time to live in seconds (None = use default)

        Returns:
            True if cached successfully
        """
        try:
            key = self._make_key(workspace.investigation_id)
            ttl = ttl_seconds or self.default_ttl

            # Serialize to JSON-compatible dict
            data = workspace.model_dump(mode="json")

            # Add cache metadata
            data["_cached_at"] = datetime.now().isoformat()

            # Store in RedisJSON
            self.redis.json().set(key, Path.root_path(), data)

            # Set TTL
            self.redis.expire(key, ttl)

            self._stats["writes"] += 1
            logger.debug(f"Cached investigation {workspace.investigation_id} (TTL: {ttl}s)")
            return True

        except Exception as exc:
            logger.error(f"Failed to cache investigation {workspace.investigation_id}: {exc}")
            return False

    def get_workspace(self, investigation_id: str) -> InvestigationWorkspace | None:
        """
        Retrieve investigation workspace from cache.

        Args:
            investigation_id: Investigation ID

        Returns:
            InvestigationWorkspace or None if not found/expired
        """
        try:
            key = self._make_key(investigation_id)
            data = self.redis.json().get(key)

            if data:
                # Remove cache metadata before validation
                data.pop("_cached_at", None)

                workspace = InvestigationWorkspace.model_validate(data)
                self._stats["hits"] += 1
                logger.debug(f"Cache hit: investigation {investigation_id}")
                return workspace

            self._stats["misses"] += 1
            logger.debug(f"Cache miss: investigation {investigation_id}")
            return None

        except Exception as exc:
            logger.warning(f"Failed to get investigation {investigation_id} from cache: {exc}")
            self._stats["misses"] += 1
            return None

    def update_stage_artifact(
        self, investigation_id: str, stage: str, artifact: dict[str, Any]
    ) -> bool:
        """
        Update a specific pipeline stage artifact in cached workspace.

        Uses RedisJSON partial update for efficiency (no need to reload full workspace).

        Args:
            investigation_id: Investigation ID
            stage: Stage name ("plan", "retrieval", "timeline", etc.)
            artifact: Stage artifact data

        Returns:
            True if updated successfully
        """
        try:
            key = self._make_key(investigation_id)

            # Check if workspace exists in cache
            exists = self.redis.exists(key)
            if not exists:
                logger.debug(
                    f"Cannot update stage {stage} for {investigation_id}: not in cache"
                )
                return False

            # Update nested field
            self.redis.json().set(key, Path(f"$.{stage}"), artifact)

            # Update status and current_stage if this is a new completion
            if stage != "plan":
                stage_status_map = {
                    "retrieval": ("retrieval_completed", "retriever"),
                    "timeline": ("timeline_completed", "timeline"),
                    "counter_narratives": ("counter_narrative_completed", "counter_narrative"),
                    "analyst": ("analyst_completed", "analyst"),
                    "report": ("report_completed", "report"),
                }

                if stage in stage_status_map:
                    status, current_stage = stage_status_map[stage]
                    self.redis.json().set(key, Path("$.status"), status)
                    self.redis.json().set(key, Path("$.current_stage"), current_stage)

            # Update updated_at timestamp
            self.redis.json().set(key, Path("$.updated_at"), datetime.now().isoformat())

            logger.debug(f"Updated stage {stage} for investigation {investigation_id}")
            return True

        except Exception as exc:
            logger.error(
                f"Failed to update stage {stage} for {investigation_id}: {exc}"
            )
            return False

    def update_documents(
        self, investigation_id: str, documents: list[dict[str, Any]]
    ) -> bool:
        """
        Update retrieved_documents in cached workspace.

        Args:
            investigation_id: Investigation ID
            documents: List of document dicts

        Returns:
            True if updated successfully
        """
        try:
            key = self._make_key(investigation_id)

            if not self.redis.exists(key):
                return False

            self.redis.json().set(key, Path("$.retrieved_documents"), documents)
            logger.debug(
                f"Updated {len(documents)} documents for investigation {investigation_id}"
            )
            return True

        except Exception as exc:
            logger.error(f"Failed to update documents for {investigation_id}: {exc}")
            return False

    def invalidate(self, investigation_id: str) -> bool:
        """
        Invalidate (delete) cached investigation.

        Args:
            investigation_id: Investigation ID

        Returns:
            True if deleted
        """
        try:
            key = self._make_key(investigation_id)
            deleted = self.redis.delete(key)
            if deleted:
                logger.debug(f"Invalidated cache for investigation {investigation_id}")
            return deleted > 0
        except Exception as exc:
            logger.error(f"Failed to invalidate cache for {investigation_id}: {exc}")
            return False

    def get_ttl(self, investigation_id: str) -> int:
        """
        Get remaining TTL for cached investigation.

        Args:
            investigation_id: Investigation ID

        Returns:
            Remaining seconds, or -1 if no TTL, -2 if not found
        """
        try:
            key = self._make_key(investigation_id)
            return self.redis.ttl(key)
        except Exception:
            return -2

    def extend_ttl(self, investigation_id: str, additional_seconds: int) -> bool:
        """
        Extend TTL for cached investigation.

        Args:
            investigation_id: Investigation ID
            additional_seconds: Seconds to add to current TTL

        Returns:
            True if extended
        """
        try:
            key = self._make_key(investigation_id)
            current_ttl = self.redis.ttl(key)

            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                self.redis.expire(key, new_ttl)
                logger.debug(
                    f"Extended TTL for {investigation_id} by {additional_seconds}s (new: {new_ttl}s)"
                )
                return True
            return False
        except Exception as exc:
            logger.error(f"Failed to extend TTL for {investigation_id}: {exc}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, writes, hit rate
        """
        total_reads = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_reads if total_reads > 0 else 0.0

        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "writes": self._stats["writes"],
            "total_reads": total_reads,
            "hit_rate": round(hit_rate, 3),
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = {"hits": 0, "misses": 0, "writes": 0}

    def list_cached_investigations(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        List all cached investigations.

        Args:
            limit: Maximum number to return

        Returns:
            List of dicts with id, status, ttl
        """
        try:
            keys = list(self.redis.scan_iter("rq:investigation:*", count=limit))
            investigations = []

            for key in keys[:limit]:
                investigation_id = key.split(":")[-1]
                ttl = self.redis.ttl(key)
                status_path = self.redis.json().get(key, Path("$.status"))
                status = status_path[0] if status_path else "unknown"

                investigations.append(
                    {"investigation_id": investigation_id, "status": status, "ttl_seconds": ttl}
                )

            return investigations
        except Exception as exc:
            logger.error(f"Failed to list cached investigations: {exc}")
            return []

    def clear_all(self) -> int:
        """
        Clear all cached investigations.

        Returns:
            Number of investigations deleted
        """
        try:
            keys = list(self.redis.scan_iter("rq:investigation:*", count=1000))
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cached investigations")
                return deleted
            return 0
        except Exception as exc:
            logger.error(f"Failed to clear cache: {exc}")
            return 0

    def clear_expired(self) -> int:
        """
        Clear expired investigations (TTL <= 0).

        Returns:
            Number of expired investigations removed
        """
        try:
            keys = list(self.redis.scan_iter("rq:investigation:*", count=1000))
            expired = []

            for key in keys:
                ttl = self.redis.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    expired.append(key)

            if expired:
                deleted = self.redis.delete(*expired)
                logger.info(f"Cleared {deleted} expired investigations")
                return deleted
            return 0
        except Exception as exc:
            logger.error(f"Failed to clear expired cache: {exc}")
            return 0


def get_investigation_cache() -> InvestigationCache | None:
    """
    Get investigation cache instance.

    Returns None if Redis is unavailable or caching is disabled.
    """
    from config import get_settings

    settings = get_settings()

    # Check if caching is enabled
    if not getattr(settings, "ENABLE_INVESTIGATION_CACHE", True):
        logger.info("Investigation caching disabled in config")
        return None

    try:
        import redis as redis_lib

        redis_client = redis_lib.from_url(
            settings.REDIS_URL, decode_responses=True, socket_timeout=5
        )
        redis_client.ping()

        ttl = getattr(settings, "CACHE_TTL_SECONDS", 3600)
        return InvestigationCache(redis_client, default_ttl_seconds=ttl)

    except Exception as exc:
        logger.warning(f"Investigation cache unavailable: {exc}")
        return None
