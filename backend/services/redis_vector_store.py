"""
Redis Vector Store for RhetoriQ — uses Redis 8 native vectorset (VADD/VSIM).

Provides semantic similarity search for documents without requiring RediSearch.
Uses VADD to store embeddings and VSIM for K-nearest-neighbor search.

Redis Sponsor Track: Demonstrates Redis vector search + RedisJSON document storage.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from models.document import Document
from services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

VSET_KEY = "rq:vset:docs"


class VectorSearchResult:
    def __init__(
        self,
        doc_id: str,
        score: float,
        title: str = "",
        source_name: str = "",
        snippet: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.id = doc_id
        self.score = score
        self.title = title
        self.source_name = source_name
        self.snippet = snippet
        self.metadata = metadata or {}


class RedisVectorStore:
    """
    Redis-backed vector store using native Redis 8 vectorset commands (VADD/VSIM).
    Falls back gracefully if Redis is unavailable.
    """

    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis: Any | None = redis_client
        self._embedding_service = get_embedding_service()

    @property
    def redis(self) -> Any:
        """Get Redis client (text mode — vectorset accepts plain float values)."""
        if self._redis is None:
            from config import get_settings
            settings = get_settings()
            try:
                import redis as redis_lib
                self._redis = redis_lib.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=10,
                    socket_connect_timeout=10,
                )
                self._redis.ping()
                logger.info("Redis vector store connected")
            except Exception as exc:
                logger.error("Failed to connect to Redis: %s", exc)
                raise
        return self._redis

    @property
    def json_redis(self) -> Any:
        return self.redis

    def add_document(self, doc: Document, generate_embedding: bool = True) -> bool:
        """Add a document to the vector store."""
        try:
            embedding = doc.embedding
            if not embedding and generate_embedding:
                embedding = self._embedding_service.embed_document(doc)
            if not embedding:
                logger.warning("Document %s has no embedding, skipping", doc.id)
                return False

            # Store embedding in vectorset (plain float list works with text client)
            vec = [float(v) for v in embedding]
            self.redis.execute_command("VADD", VSET_KEY, "VALUES", len(vec), *vec, doc.id)

            # Store metadata in RedisJSON for retrieval
            meta = {
                "id": doc.id,
                "title": doc.title,
                "source_name": doc.source_name,
                "snippet": doc.snippet or "",
            }
            self.redis.json().set(f"rq:doc:meta:{doc.id}", "$", meta)

            logger.debug("Added document %s to vector store", doc.id)
            return True

        except Exception as exc:
            logger.error("Failed to add document %s: %s", doc.id, exc)
            return False

    def add_documents_batch(
        self, docs: list[Document], batch_size: int = 32, generate_embeddings: bool = True
    ) -> int:
        """Add multiple documents, generating embeddings in batch."""
        if not docs:
            return 0

        docs_needing_embeddings = [doc for doc in docs if not doc.embedding]
        if docs_needing_embeddings and generate_embeddings:
            logger.info("Generating embeddings for %d documents...", len(docs_needing_embeddings))
            embeddings = self._embedding_service.embed_batch_documents(
                docs_needing_embeddings, batch_size=batch_size
            )
            for doc, embedding in zip(docs_needing_embeddings, embeddings):
                doc.embedding = embedding

        added = 0
        for doc in docs:
            if self.add_document(doc, generate_embedding=False):
                added += 1

        logger.info("Added %d documents to vector store", added)
        return added

    def semantic_search(
        self,
        query: str | list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for semantically similar documents."""
        try:
            if isinstance(query, str):
                query_embedding = self._embedding_service.embed_query(query)
            else:
                query_embedding = query

            vec = np.array(query_embedding, dtype=np.float32).tolist()

            raw = self.redis.execute_command(
                "VSIM", VSET_KEY, "VALUES", len(vec), *vec,
                "WITHSCORES", "COUNT", limit,
            )

            # VSIM returns [element, score, element, score, ...]
            results = []
            if raw:
                it = iter(raw)
                for doc_id_bytes, score_bytes in zip(it, it):
                    doc_id = doc_id_bytes.decode() if isinstance(doc_id_bytes, bytes) else doc_id_bytes
                    score = float(score_bytes.decode() if isinstance(score_bytes, bytes) else score_bytes)

                    # Fetch metadata from RedisJSON
                    title, source_name, snippet = "", "", None
                    try:
                        meta = self.redis.json().get(f"rq:doc:meta:{doc_id}")
                        if meta:
                            title = meta.get("title", "")
                            source_name = meta.get("source_name", "")
                            snippet = meta.get("snippet") or None
                    except Exception:
                        pass

                    results.append(VectorSearchResult(
                        doc_id=doc_id,
                        score=score,
                        title=title,
                        source_name=source_name,
                        snippet=snippet,
                    ))

            logger.debug("Semantic search returned %d results", len(results))
            return results

        except Exception as exc:
            logger.error("Semantic search failed: %s", exc)
            return []

    def count_documents(self) -> int:
        """Count total documents in the vector store."""
        try:
            result = self.redis.execute_command("VCARD", VSET_KEY)
            return int(result) if result else 0
        except Exception:
            return 0

    def delete_document(self, doc_id: str) -> bool:
        """Remove a document from the vector store."""
        try:
            self.redis.execute_command("VREM", VSET_KEY, doc_id)
            self.redis.delete(f"rq:doc:meta:{doc_id}")
            return True
        except Exception as exc:
            logger.error("Failed to delete document %s: %s", doc_id, exc)
            return False

    def find_similar_documents(
        self, doc: Document, limit: int = 10, exclude_self: bool = True
    ) -> list[VectorSearchResult]:
        """Find documents similar to a given document."""
        if not doc.embedding:
            doc.embedding = self._embedding_service.embed_document(doc)
        results = self.semantic_search(doc.embedding, limit=limit + 1 if exclude_self else limit)
        if exclude_self:
            results = [r for r in results if r.id != doc.id]
        return results[:limit]

    def health_check(self) -> dict[str, Any]:
        """Check Redis vector store health."""
        try:
            self.redis.ping()
            doc_count = self.count_documents()
            return {
                "connected": True,
                "vset_key": VSET_KEY,
                "document_count": doc_count,
                "embedding_dimension": self._embedding_service.dimension,
                "embedding_model": self._embedding_service.model_name,
            }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}


def get_redis_vector_store() -> RedisVectorStore | None:
    """Get Redis vector store instance. Returns None if Redis is unavailable."""
    from config import get_settings
    settings = get_settings()

    if not getattr(settings, "ENABLE_VECTOR_SEARCH", True):
        logger.info("Vector search disabled in config")
        return None

    try:
        store = RedisVectorStore()
        store.redis.ping()
        return store
    except Exception as exc:
        logger.warning("Redis vector store unavailable: %s", exc)
        return None
