from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


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
        return bool(self._redis.set("rq:trending:refresh_lock", "1", nx=True, ex=ttl_seconds))

    def release_refresh_lock(self) -> None:
        if self._redis:
            self._redis.delete("rq:trending:refresh_lock")

    def refresh_lock_active(self) -> bool:
        if not self._redis:
            return False
        return bool(self._redis.exists("rq:trending:refresh_lock"))

    def set_topic_investigation(
        self,
        topic_id: str,
        investigation_id: str,
        *,
        ttl_seconds: int,
    ) -> None:
        if not self._redis:
            return
        self._redis.hset(
            f"rq:trending:topic:{topic_id}",
            mapping={
                "investigation_id": investigation_id,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self._redis.expire(f"rq:trending:topic:{topic_id}", ttl_seconds)

    def get_topic_investigation(self, topic_id: str) -> str | None:
        if not self._redis:
            return None
        data = self._redis.hgetall(f"rq:trending:topic:{topic_id}")
        if not data:
            return None
        return data.get("investigation_id")

    def set_last_error(self, message: str | None) -> None:
        if not self._redis:
            return
        key = "rq:trending:last_error"
        if message:
            self._redis.set(key, message, ex=int(timedelta(days=1).total_seconds()))
        else:
            self._redis.delete(key)

    def get_last_error(self) -> str | None:
        if not self._redis:
            return None
        value = self._redis.get("rq:trending:last_error")
        return str(value) if value else None

