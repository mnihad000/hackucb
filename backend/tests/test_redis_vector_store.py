"""
Unit tests for RedisVectorStore.

Note: These tests require a running Redis Stack instance.
Set REDIS_URL in .env or they will be skipped.
"""

import pytest
from datetime import datetime

from models.document import Document
from services.redis_vector_store import RedisVectorStore, VectorSearchResult
from config import get_settings


@pytest.fixture
def redis_store():
    """Create a Redis vector store for testing."""
    settings = get_settings()

    try:
        store = RedisVectorStore(index_name="test:idx:documents")
        store.redis.ping()
        yield store
        # Cleanup
        store.clear_all_documents()
    except Exception:
        pytest.skip("Redis not available")


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            id="doc_001",
            source_id="src_001",
            source_name="Test News",
            source_type="blog",
            url="https://example.com/1",
            title="Climate Change Policy Debate",
            text="Climate change requires urgent policy action and regulation.",
            snippet="Climate policy debate...",
            entities=["climate", "policy"],
            phrases=["climate change"],
            published_at=datetime.now(),
        ),
        Document(
            id="doc_002",
            source_id="src_002",
            source_name="Tech Blog",
            source_type="blog",
            url="https://example.com/2",
            title="Global Warming Impacts",
            text="Global warming is accelerating and requires environmental action.",
            snippet="Global warming impacts...",
            entities=["warming", "environment"],
            phrases=["global warming"],
            published_at=datetime.now(),
        ),
        Document(
            id="doc_003",
            source_id="src_003",
            source_name="Food Blog",
            source_type="blog",
            url="https://example.com/3",
            title="Best Pasta Recipes",
            text="Here are the best pasta recipes for a delicious dinner.",
            snippet="Pasta cooking tips...",
            entities=["pasta", "recipes"],
            phrases=["cooking"],
            published_at=datetime.now(),
        ),
    ]


def test_create_index(redis_store):
    """Test creating RediSearch vector index."""
    created = redis_store.create_index(dimension=384)
    # Should return True on first call, False on subsequent
    assert isinstance(created, bool)


def test_add_document(redis_store, sample_documents):
    """Test adding a document with embedding."""
    redis_store.create_index(dimension=384)

    doc = sample_documents[0]
    success = redis_store.add_document(doc, generate_embedding=True)

    assert success is True

    # Verify document was stored
    retrieved = redis_store.get_document(doc.id)
    assert retrieved is not None
    assert retrieved.id == doc.id
    assert retrieved.embedding is not None
    assert len(retrieved.embedding) == 384


def test_add_documents_batch(redis_store, sample_documents):
    """Test batch document addition."""
    redis_store.create_index(dimension=384)

    added = redis_store.add_documents_batch(sample_documents, generate_embeddings=True)

    assert added == len(sample_documents)
    assert redis_store.count_documents() >= len(sample_documents)


def test_semantic_search(redis_store, sample_documents):
    """Test semantic similarity search."""
    redis_store.create_index(dimension=384)
    redis_store.add_documents_batch(sample_documents, generate_embeddings=True)

    # Search for climate-related content
    results = redis_store.semantic_search("environmental policy", limit=2)

    assert len(results) > 0
    assert isinstance(results[0], VectorSearchResult)

    # Top results should be climate-related, not pasta recipes
    top_result = results[0]
    assert "climate" in top_result.title.lower() or "warming" in top_result.title.lower()


def test_semantic_search_with_filters(redis_store, sample_documents):
    """Test semantic search with source type filter."""
    redis_store.create_index(dimension=384)
    redis_store.add_documents_batch(sample_documents, generate_embeddings=True)

    # Search only in blogs
    results = redis_store.semantic_search(
        "climate change", limit=5, filters={"source_type": "blog"}
    )

    assert all(r.id.startswith("doc_") for r in results)


def test_find_similar_documents(redis_store, sample_documents):
    """Test finding similar documents to a given document."""
    redis_store.create_index(dimension=384)
    redis_store.add_documents_batch(sample_documents, generate_embeddings=True)

    # Find documents similar to climate doc
    climate_doc = sample_documents[0]
    similar = redis_store.find_similar_documents(climate_doc, limit=2, exclude_self=True)

    assert len(similar) > 0
    # Should not include the source document
    assert all(s.id != climate_doc.id for s in similar)


def test_delete_document(redis_store, sample_documents):
    """Test document deletion."""
    redis_store.create_index(dimension=384)

    doc = sample_documents[0]
    redis_store.add_document(doc, generate_embedding=True)

    # Delete document
    deleted = redis_store.delete_document(doc.id)
    assert deleted is True

    # Verify it's gone
    retrieved = redis_store.get_document(doc.id)
    assert retrieved is None


def test_health_check(redis_store):
    """Test health check returns status."""
    health = redis_store.health_check()

    assert health["connected"] is True
    assert "document_count" in health
    assert "embedding_model" in health
