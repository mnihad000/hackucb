from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from config import get_settings
from services.embedding_service import get_embedding_service, normalize_embedding_text

logger = logging.getLogger(__name__)


VSET_KEYS = {
    "article": "rq:memory:vset:articles",
    "claim": "rq:memory:vset:claims",
    "timeline_event": "rq:memory:vset:timeline_events",
    "agent_finding": "rq:memory:vset:agent_findings",
}

CONTEXT_BUCKETS = {
    "article": "articles",
    "claim": "claims",
    "timeline_event": "timeline_events",
    "agent_finding": "agent_findings",
}


class RedisMemoryService:
    """
    Redis-backed agent memory for RhetoriQ.

    Redis stores generated vectors and metadata so agents can connect a new
    investigation to prior articles, claims, timeline nodes, and findings. It
    does not store SentenceTransformer model weights.
    """

    def __init__(
        self,
        *,
        redis_client: Any | None = None,
        redis_url: str | None = None,
        embedding_service: Any | None = None,
    ) -> None:
        settings = get_settings()
        self.redis_url = redis_url if redis_url is not None else getattr(settings, "REDIS_URL", "")
        self._redis = redis_client
        self._available: bool | None = True if redis_client is not None else None
        self._embedding_service = embedding_service or get_embedding_service()

    @property
    def available(self) -> bool:
        if self._available is False:
            return False
        if self._redis is None and not self.redis_url:
            self._available = False
            return False
        try:
            self.redis.ping()
            self._available = True
            return True
        except Exception as exc:
            logger.warning("Redis memory unavailable: %s", exc)
            self._available = False
            return False

    @property
    def redis(self) -> Any:
        if self._redis is None:
            import redis as redis_lib

            self._redis = redis_lib.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=3,
                socket_connect_timeout=3,
            )
        return self._redis

    def store_article_vector(
        self,
        article_id: str,
        text: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return self._store_vector("article", article_id, text, embedding, metadata)

    def store_claim_vector(
        self,
        claim_id: str,
        claim_text: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return self._store_vector("claim", claim_id, claim_text, embedding, metadata)

    def store_timeline_event(
        self,
        event_id: str,
        text: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return self._store_vector("timeline_event", event_id, text, embedding, metadata)

    def store_agent_finding(
        self,
        finding_id: str,
        agent_name: str,
        investigation_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        merged_metadata = {
            **(metadata or {}),
            "agent_name": agent_name,
            "investigation_id": investigation_id,
            "content_type": "agent_finding",
        }
        return self._store_vector("agent_finding", finding_id, text, None, merged_metadata)

    def search_similar_claims(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self._search("claim", query_embedding, top_k, filters)

    def search_related_articles(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return self._search("article", query_embedding, top_k, filters)

    def get_investigation_context(self, investigation_id: str) -> dict[str, Any]:
        context: dict[str, Any] = {
            "investigation_id": investigation_id,
            "articles": [],
            "claims": [],
            "timeline_events": [],
            "agent_findings": [],
        }
        if not self.available:
            return context

        try:
            locators = self.redis.smembers(_investigation_key(investigation_id)) or []
            for locator in sorted(str(item) for item in locators):
                content_type, _, item_id = locator.partition(":")
                bucket = CONTEXT_BUCKETS.get(content_type)
                if not bucket or not item_id:
                    continue
                record = self._get_record(content_type, item_id)
                if record is not None:
                    context[bucket].append(record)
        except Exception as exc:
            logger.warning("Redis investigation context lookup failed: %s", exc)
        return context

    def health_check(self) -> dict[str, Any]:
        if not self.available:
            return {"connected": False, "reason": "Redis unavailable"}

        counts: dict[str, int] = {}
        for content_type, key in VSET_KEYS.items():
            try:
                counts[content_type] = int(self.redis.execute_command("VCARD", key) or 0)
            except Exception:
                counts[content_type] = 0
        return {
            "connected": True,
            "vectorsets": VSET_KEYS,
            "counts": counts,
        }

    def _store_vector(
        self,
        content_type: str,
        item_id: str,
        text: str,
        embedding: list[float] | None,
        metadata: dict[str, Any] | None,
    ) -> bool:
        if content_type not in VSET_KEYS:
            raise ValueError(f"Unknown Redis memory content_type: {content_type}")
        normalized_text = normalize_embedding_text(text)
        if not normalized_text:
            return False
        if not self.available:
            return False

        metadata = dict(metadata or {})
        metadata.setdefault("content_type", content_type)
        metadata.setdefault("collected_at", datetime.now(timezone.utc).isoformat())
        embedding = embedding or self._embedding_service.embed_text(normalized_text)
        if not embedding:
            return False

        try:
            vec = [float(value) for value in embedding]
            self.redis.execute_command(
                "VADD",
                VSET_KEYS[content_type],
                "VALUES",
                len(vec),
                *vec,
                item_id,
            )
            record = {
                "id": item_id,
                "text": normalized_text,
                "metadata": metadata,
            }
            self.redis.set(_metadata_key(content_type, item_id), json.dumps(record, default=str))

            investigation_id = metadata.get("investigation_id")
            if investigation_id:
                self.redis.sadd(_investigation_key(str(investigation_id)), f"{content_type}:{item_id}")
            return True
        except Exception as exc:
            logger.warning("Redis memory store failed for %s:%s: %s", content_type, item_id, exc)
            return False

    def _search(
        self,
        content_type: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if content_type not in VSET_KEYS or not query_embedding or not self.available:
            return []
        try:
            vec = [float(value) for value in query_embedding]
            raw = self.redis.execute_command(
                "VSIM",
                VSET_KEYS[content_type],
                "VALUES",
                len(vec),
                *vec,
                "WITHSCORES",
                "COUNT",
                max(top_k * 3, top_k),
            )
            results = []
            iterator = iter(raw or [])
            for raw_id, raw_score in zip(iterator, iterator):
                item_id = _decode(raw_id)
                score = float(_decode(raw_score))
                record = self._get_record(content_type, item_id)
                if record is None or not _metadata_matches(record.get("metadata", {}), filters):
                    continue
                results.append({**record, "score": score})
                if len(results) >= top_k:
                    break
            return results
        except Exception as exc:
            logger.warning("Redis memory search failed for %s: %s", content_type, exc)
            return []

    def _get_record(self, content_type: str, item_id: str) -> dict[str, Any] | None:
        try:
            raw = self.redis.get(_metadata_key(content_type, item_id))
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            if not raw:
                return None
            record = json.loads(raw)
            return record if isinstance(record, dict) else None
        except Exception:
            return None


def _metadata_key(content_type: str, item_id: str) -> str:
    return f"rq:memory:{content_type}:meta:{item_id}"


def _investigation_key(investigation_id: str) -> str:
    return f"rq:memory:investigation:{investigation_id}:items"


def _decode(value: Any) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def _metadata_matches(metadata: dict[str, Any], filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        if metadata.get(key) != expected:
            return False
    return True


_memory_service: RedisMemoryService | None = None


def get_redis_memory_service() -> RedisMemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = RedisMemoryService()
    return _memory_service
