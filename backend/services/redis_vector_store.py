"""
Redis Vector Store for RhetoriQ - Semantic search using RediSearch vector indices.

Provides vector similarity search for documents, enabling:
- Semantic document retrieval (find similar docs by meaning, not just keywords)
- Phrase mutation detection (find semantically similar phrases)
- Claim-to-evidence matching (auto-cite supporting documents)
- Counter-narrative detection (find opposing viewpoints)

Redis Sponsor Track: Demonstrates Redis beyond caching with vector search and agent memory.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

import numpy as np

from models.document import Document
from services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class VectorSearchResult:
    """Single result from vector similarity search."""

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
        self.score = score  # Similarity score [0, 1]
        self.title = title
        self.source_name = source_name
        self.snippet = snippet
        self.metadata = metadata or {}


class RedisVectorStore:
    """
    Redis-backed vector store with semantic search.

    Uses RediSearch vector indices for fast approximate nearest neighbor search.
    """

    def __init__(self, redis_client: Any | None = None, index_name: str = "idx:documents") -> None:
        """
        Initialize Redis vector store.

        Args:
            redis_client: Redis client instance (falls back to new connection)
            index_name: Name of the RediSearch index
        """
        self.index_name = index_name
        self._redis: Any | None = redis_client
        self._embedding_service = get_embedding_service()
        self._index_exists = False

    @property
    def redis(self) -> Any:
        """Get or create Redis client."""
        if self._redis is None:
            from config import get_settings

            settings = get_settings()
            redis_url = settings.REDIS_URL

            try:
                import redis as redis_lib

                self._redis = redis_lib.from_url(
                    redis_url, decode_responses=True, socket_timeout=5
                )
                self._redis.ping()
                logger.info(f"Redis vector store connected to {redis_url}")
            except Exception as exc:
                logger.error(f"Failed to connect to Redis: {exc}")
                raise

        return self._redis

    def create_index(
        self,
        dimension: int = 384,
        distance_metric: Literal["COSINE", "L2", "IP"] = "COSINE",
        index_type: Literal["FLAT", "HNSW"] = "HNSW",
    ) -> bool:
        """
        Create RediSearch vector index for documents.

        Args:
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
            distance_metric: COSINE (recommended), L2, or IP (inner product)
            index_type: FLAT (exact) or HNSW (approximate, faster for >10K docs)

        Returns:
            True if created, False if already exists
        """
        try:
            from redis.commands.search.field import TextField, TagField, VectorField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType

            # Check if index already exists
            try:
                self.redis.ft(self.index_name).info()
                logger.info(f"Index {self.index_name} already exists")
                self._index_exists = True
                return False
            except Exception:
                pass  # Index doesn't exist, create it

            # Define schema
            schema = [
                TextField("$.id", as_name="id"),
                TextField("$.title", as_name="title"),
                TextField("$.text", as_name="text", no_stem=True),
                TextField("$.snippet", as_name="snippet"),
                TagField("$.source_type", as_name="source_type"),
                TagField("$.source_name", as_name="source_name"),
            ]

            # Vector field configuration
            vector_params = {
                "TYPE": "FLOAT32",
                "DIM": dimension,
                "DISTANCE_METRIC": distance_metric,
            }

            if index_type == "HNSW":
                # HNSW (Hierarchical Navigable Small World) for fast ANN
                vector_params.update(
                    {
                        "INITIAL_CAP": 10000,
                        "M": 16,  # Connections per node
                        "EF_CONSTRUCTION": 200,  # Build-time accuracy
                    }
                )

            schema.append(VectorField("$.embedding", index_type, vector_params, as_name="embedding"))

            # Create index
            self.redis.ft(self.index_name).create_index(
                schema,
                definition=IndexDefinition(prefix=["rq:doc:"], index_type=IndexType.JSON),
            )

            logger.info(
                f"Created RediSearch index '{self.index_name}' "
                f"({index_type}, {dimension}-dim, {distance_metric})"
            )
            self._index_exists = True
            return True

        except Exception as exc:
            logger.error(f"Failed to create RediSearch index: {exc}")
            raise

    def add_document(self, doc: Document, generate_embedding: bool = True) -> bool:
        """
        Add a document to the vector store.

        Args:
            doc: Document to add
            generate_embedding: If True, generate embedding if missing

        Returns:
            True if added successfully
        """
        try:
            # Generate embedding if needed
            embedding = doc.embedding
            if not embedding and generate_embedding:
                embedding = self._embedding_service.embed_document(doc)

            if not embedding:
                logger.warning(f"Document {doc.id} has no embedding, skipping vector store")
                return False

            # Store as RedisJSON
            key = f"rq:doc:{doc.id}"
            doc_dict = doc.model_dump(mode="json")
            doc_dict["embedding"] = embedding

            self.redis.json().set(key, "$", doc_dict)
            logger.debug(f"Added document {doc.id} to vector store")
            return True

        except Exception as exc:
            logger.error(f"Failed to add document {doc.id}: {exc}")
            return False

    def add_documents_batch(
        self, docs: list[Document], batch_size: int = 32, generate_embeddings: bool = True
    ) -> int:
        """
        Add multiple documents efficiently.

        Args:
            docs: List of documents
            batch_size: Batch size for embedding generation
            generate_embeddings: Generate embeddings if missing

        Returns:
            Number of documents added
        """
        if not docs:
            return 0

        # Generate embeddings in batch for docs missing them
        docs_needing_embeddings = [doc for doc in docs if not doc.embedding]

        if docs_needing_embeddings and generate_embeddings:
            logger.info(f"Generating embeddings for {len(docs_needing_embeddings)} documents...")
            embeddings = self._embedding_service.embed_batch_documents(
                docs_needing_embeddings, batch_size=batch_size
            )

            # Assign embeddings
            for doc, embedding in zip(docs_needing_embeddings, embeddings):
                doc.embedding = embedding

        # Add documents to Redis
        added = 0
        pipeline = self.redis.pipeline()

        for doc in docs:
            if doc.embedding:
                key = f"rq:doc:{doc.id}"
                doc_dict = doc.model_dump(mode="json")
                pipeline.json().set(key, "$", doc_dict)
                added += 1

        if added > 0:
            pipeline.execute()
            logger.info(f"Added {added} documents to vector store")

        return added

    def semantic_search(
        self,
        query: str | list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """
        Search for documents by semantic similarity.

        Args:
            query: Query text or pre-computed embedding vector
            limit: Maximum number of results
            filters: Optional filters (e.g., {"source_type": "local_news"})

        Returns:
            List of VectorSearchResult, sorted by similarity (highest first)
        """
        try:
            from redis.commands.search.query import Query

            # Get query embedding
            if isinstance(query, str):
                query_embedding = self._embedding_service.embed_query(query)
            else:
                query_embedding = query

            # Convert to bytes for Redis
            query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

            # Build query
            # KNN = K-Nearest Neighbors
            base_query = f"(*)=>[KNN {limit} @embedding $vec AS score]"

            # Add filters if provided
            if filters:
                filter_parts = []
                for field, value in filters.items():
                    if isinstance(value, list):
                        # Tag field with multiple values
                        filter_parts.append(f"@{field}:{{{' | '.join(value)}}}")
                    else:
                        filter_parts.append(f"@{field}:{{{value}}}")
                if filter_parts:
                    base_query = f"({' '.join(filter_parts)})=>[KNN {limit} @embedding $vec AS score]"

            query_obj = (
                Query(base_query)
                .sort_by("score")
                .return_fields("id", "title", "source_name", "snippet", "score")
                .paging(0, limit)
                .dialect(2)
            )

            # Execute search
            results = self.redis.ft(self.index_name).search(query_obj, {"vec": query_bytes})

            # Parse results
            search_results = []
            for doc in results.docs:
                # RedisSearch returns fields as attributes
                doc_id = getattr(doc, "id", doc.id)
                score = float(getattr(doc, "score", 0.0))
                title = getattr(doc, "title", "")
                source_name = getattr(doc, "source_name", "")
                snippet = getattr(doc, "snippet", None)

                search_results.append(
                    VectorSearchResult(
                        doc_id=doc_id,
                        score=score,
                        title=title,
                        source_name=source_name,
                        snippet=snippet,
                    )
                )

            logger.debug(f"Semantic search returned {len(search_results)} results")
            return search_results

        except Exception as exc:
            logger.error(f"Semantic search failed: {exc}")
            return []

    def get_document(self, doc_id: str) -> Document | None:
        """
        Retrieve a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document or None if not found
        """
        try:
            key = f"rq:doc:{doc_id}"
            data = self.redis.json().get(key)
            if data:
                return Document.model_validate(data)
            return None
        except Exception as exc:
            logger.warning(f"Failed to get document {doc_id}: {exc}")
            return None

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store."""
        try:
            key = f"rq:doc:{doc_id}"
            deleted = self.redis.delete(key)
            return deleted > 0
        except Exception as exc:
            logger.error(f"Failed to delete document {doc_id}: {exc}")
            return False

    def count_documents(self) -> int:
        """Count total documents in the store."""
        try:
            info = self.redis.ft(self.index_name).info()
            # Parse index info to get document count
            num_docs = info.get("num_docs", 0)
            return int(num_docs)
        except Exception:
            # Fallback: count keys with prefix
            keys = list(self.redis.scan_iter("rq:doc:*", count=1000))
            return len(keys)

    def clear_all_documents(self) -> int:
        """
        Delete all documents from the store.

        Returns:
            Number of documents deleted
        """
        try:
            keys = list(self.redis.scan_iter("rq:doc:*", count=1000))
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Deleted {deleted} documents from vector store")
                return deleted
            return 0
        except Exception as exc:
            logger.error(f"Failed to clear documents: {exc}")
            return 0

    def find_similar_documents(
        self, doc: Document, limit: int = 10, exclude_self: bool = True
    ) -> list[VectorSearchResult]:
        """
        Find documents similar to a given document.

        Args:
            doc: Source document
            limit: Max results
            exclude_self: If True, exclude the source document from results

        Returns:
            List of similar documents
        """
        if not doc.embedding:
            doc.embedding = self._embedding_service.embed_document(doc)

        results = self.semantic_search(doc.embedding, limit=limit + 1 if exclude_self else limit)

        if exclude_self:
            results = [r for r in results if r.id != doc.id]

        return results[:limit]

    def health_check(self) -> dict[str, Any]:
        """
        Check Redis vector store health.

        Returns:
            Dict with status info
        """
        try:
            self.redis.ping()
            doc_count = self.count_documents()

            return {
                "connected": True,
                "index_name": self.index_name,
                "index_exists": self._index_exists,
                "document_count": doc_count,
                "embedding_dimension": self._embedding_service.dimension,
                "embedding_model": self._embedding_service.model_name,
            }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}


def get_redis_vector_store() -> RedisVectorStore | None:
    """
    Get Redis vector store instance.

    Returns None if Redis is unavailable (graceful degradation).
    """
    from config import get_settings

    settings = get_settings()

    # Check if vector search is enabled
    if not getattr(settings, "ENABLE_VECTOR_SEARCH", True):
        logger.info("Vector search disabled in config")
        return None

    try:
        store = RedisVectorStore()
        # Test connection
        store.redis.ping()
        return store
    except Exception as exc:
        logger.warning(f"Redis vector store unavailable: {exc}")
        return None
