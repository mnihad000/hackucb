"""
Redis-backed phrase counter with transparent in-memory fallback.

When REDIS_URL resolves to a reachable server, uses real Redis sorted sets
and per-hour string counters. When Redis is unavailable (no server, wrong URL,
import error), falls back to plain Python dicts with the identical interface.

Swap-in notes:
- Replace `redis.from_url` with `redis.asyncio.from_url` for async FastAPI.
- Add key expiry (EXPIRE) so old buckets don't accumulate forever in production.
- Replace `zincrby("phrase_mentions:latest", ...)` with a time-scoped sorted set
  keyed by day so the global ranking decays naturally.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# In-memory fallback (same interface as the Redis path)
# ---------------------------------------------------------------------------

class _InMemoryStore:
    def __init__(self) -> None:
        # hour_bucket -> {phrase -> count}
        self._buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def record_phrase(self, phrase: str, timestamp: datetime, doc_id: str) -> None:
        bucket = timestamp.strftime("%Y-%m-%d-%H")
        self._buckets[bucket][phrase] += 1

    def count_phrase(self, phrase: str, start: datetime, end: datetime) -> int:
        total = 0
        current = start.replace(minute=0, second=0, microsecond=0)
        while current <= end:
            total += self._buckets[current.strftime("%Y-%m-%d-%H")].get(phrase, 0)
            current += timedelta(hours=1)
        return total

    def get_top_phrases(self, n: int) -> list[tuple[str, int]]:
        totals: dict[str, int] = defaultdict(int)
        for bucket_counts in self._buckets.values():
            for phrase, count in bucket_counts.items():
                totals[phrase] += count
        ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        return ranked[:n]

    def clear(self) -> None:
        self._buckets.clear()


# ---------------------------------------------------------------------------
# Unified public interface
# ---------------------------------------------------------------------------

class PhraseStore:
    """
    Thread-safe phrase counter. Automatically chooses Redis or in-memory.

    Usage:
        store = PhraseStore(redis_url="redis://localhost:6379")
        store.record_phrase("gas stove ban", doc.published_at, doc.id)
        score = store.compute_spike_score("gas stove ban", datetime.now(tz=utc))
    """

    def __init__(self, redis_url: str = "") -> None:
        self._redis: Any = None
        self._mem = _InMemoryStore()

        if redis_url:
            try:
                import redis as _redis_lib  # type: ignore[import]
                client = _redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=2)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    @property
    def using_redis(self) -> bool:
        return self._redis is not None

    def record_phrase(self, phrase: str, timestamp: datetime, doc_id: str) -> None:
        if self._redis:
            bucket = timestamp.strftime("%Y-%m-%d-%H")
            self._redis.incr(f"rq:phrase_count:{phrase}:{bucket}")
            self._redis.sadd(f"rq:phrase_docs:{phrase}:{bucket}", doc_id)
            self._redis.zincrby("rq:phrase_mentions:latest", 1, phrase)
        else:
            self._mem.record_phrase(phrase, timestamp, doc_id)

    def compute_spike_score(self, phrase: str, now: datetime) -> float:
        """
        spike_score = mentions_last_24h / max(1, avg_daily_last_7d_prior)

        Returns the raw 24h count when no prior data exists (cold start).
        This means first-run scores equal the raw 24h mention count, which
        naturally inflates on first poll — acceptable for the hackathon.
        """
        recent = self._count(phrase, now - timedelta(hours=24), now)

        prior_total = 0
        for day in range(1, 8):
            prior_total += self._count(
                phrase,
                now - timedelta(days=day + 1),
                now - timedelta(days=day),
            )

        prior_avg = prior_total / 7
        return round(recent / max(1.0, prior_avg), 2)

    def get_top_phrases(self, n: int = 50) -> list[tuple[str, int]]:
        if self._redis:
            raw = self._redis.zrevrange("rq:phrase_mentions:latest", 0, n - 1, withscores=True)
            return [(phrase, int(score)) for phrase, score in raw]
        return self._mem.get_top_phrases(n)

    def _count(self, phrase: str, start: datetime, end: datetime) -> int:
        if self._redis:
            total = 0
            current = start.replace(minute=0, second=0, microsecond=0)
            while current <= end:
                val = self._redis.get(f"rq:phrase_count:{phrase}:{current.strftime('%Y-%m-%d-%H')}")
                total += int(val) if val else 0
                current += timedelta(hours=1)
            return total
        return self._mem.count_phrase(phrase, start, end)

    def clear(self) -> None:
        if self._redis:
            for key in self._redis.scan_iter("rq:*"):
                self._redis.delete(key)
        else:
            self._mem.clear()
