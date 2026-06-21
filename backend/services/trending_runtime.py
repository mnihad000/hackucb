from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from models.trending import PublishedTrendingSnapshot


_LATEST_SNAPSHOT_KEY = "rq:trending:latest_snapshot"
_REFRESH_LOCK_KEY = "rq:trending:refresh_lock"
_LAST_ERROR_KEY = "rq:trending:last_error"


class TrendingRuntimeStore:
    def __init__(self, redis_url: str = "") -> None:
        self._redis: Any = None
        if redis_url:
            try:
                import redis as _redis_lib  # type: ignore[import]

                client = _redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=2)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    @property
    def redis_available(self) -> bool:
        return self._redis is not None

    def acquire_refresh_lock(self, ttl_seconds: int = 600) -> bool:
        if not self._redis:
            return False
        try:
            return bool(self._redis.set(_REFRESH_LOCK_KEY, "1", nx=True, ex=ttl_seconds))
        except Exception:
            return False

    def release_refresh_lock(self) -> None:
        if not self._redis:
            return
        try:
            self._redis.delete(_REFRESH_LOCK_KEY)
        except Exception:
            return

    def refresh_lock_active(self) -> bool:
        if not self._redis:
            return False
        try:
            return bool(self._redis.exists(_REFRESH_LOCK_KEY))
        except Exception:
            return False

    def set_latest_snapshot(self, snapshot: PublishedTrendingSnapshot) -> None:
        if not self._redis:
            return
        try:
            self._redis.set(_LATEST_SNAPSHOT_KEY, snapshot.model_dump_json())
        except Exception:
            return

    def get_latest_snapshot(self) -> PublishedTrendingSnapshot | None:
        if not self._redis:
            return None
        try:
            payload = self._redis.get(_LATEST_SNAPSHOT_KEY)
        except Exception:
            return None
        if not payload:
            return None
        try:
            return PublishedTrendingSnapshot.model_validate_json(payload)
        except Exception:
            try:
                self._redis.delete(_LATEST_SNAPSHOT_KEY)
            except Exception:
                pass
            return None

    def set_topic_investigation(
        self,
        topic_id: str,
        investigation_id: str,
        *,
        ttl_seconds: int,
    ) -> None:
        if not self._redis:
            return
        try:
            self._redis.hset(
                f"rq:trending:topic:{topic_id}",
                mapping={
                    "investigation_id": investigation_id,
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self._redis.expire(f"rq:trending:topic:{topic_id}", ttl_seconds)
        except Exception:
            return

    def get_topic_investigation(self, topic_id: str) -> str | None:
        if not self._redis:
            return None
        try:
            data = self._redis.hgetall(f"rq:trending:topic:{topic_id}")
        except Exception:
            return None
        if not data:
            return None
        return data.get("investigation_id")

    def set_last_error(self, message: str | None) -> None:
        if not self._redis:
            return
        try:
            if message:
                self._redis.set(_LAST_ERROR_KEY, message, ex=int(timedelta(days=1).total_seconds()))
            else:
                self._redis.delete(_LAST_ERROR_KEY)
        except Exception:
            return

    def get_last_error(self) -> str | None:
        if not self._redis:
            return None
        try:
            value = self._redis.get(_LAST_ERROR_KEY)
        except Exception:
            return None
        return str(value) if value else None
