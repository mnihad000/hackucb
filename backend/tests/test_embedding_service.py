"""
Unit tests for EmbeddingService.
"""

import pytest
from datetime import datetime

from models.document import Document
from services.embedding_service import EmbeddingService, get_embedding_service


def test_embedding_service_initialization():
    """Test embedding service can be initialized."""
    service = EmbeddingService()
    assert service.model_name == "all-MiniLM-L6-v2"
    assert service.dimension == 384


def test_embed_query():
    """Test query embedding generation."""
    service = EmbeddingService()
    embedding = service.embed_query("climate change policy")

    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


def test_embed_document():
    """Test document embedding generation."""
    service = EmbeddingService()

    doc = Document(
        id="test_001",
        source_id="src_001",
        source_name="Test Source",
        source_type="blog",
        url="https://example.com/article",
        title="Climate Change Policy Debate",
        text="This is a longer article about climate policy and its economic impacts.",
        snippet="Climate policy debate continues...",
        entities=["climate", "policy"],
        phrases=["climate change"],
        published_at=datetime.now(),
    )

    embedding = service.embed_document(doc)

    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


def test_embed_batch_queries():
    """Test batch query embedding."""
    service = EmbeddingService()

    queries = [
        "energy policy",
        "climate change",
        "government regulation",
    ]

    embeddings = service.embed_batch_queries(queries)

    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)


def test_compute_similarity():
    """Test cosine similarity computation."""
    service = EmbeddingService()

    emb1 = service.embed_query("climate change")
    emb2 = service.embed_query("global warming")
    emb3 = service.embed_query("cooking recipes")

    # Similar queries should have high similarity
    similarity_12 = service.compute_similarity(emb1, emb2)
    assert similarity_12 > 0.7

    # Unrelated queries should have low similarity
    similarity_13 = service.compute_similarity(emb1, emb3)
    assert similarity_13 < 0.6


def test_find_similar_texts():
    """Test finding similar texts."""
    service = EmbeddingService()

    candidates = [
        "Climate change requires urgent action",
        "Global warming is accelerating",
        "Best pasta recipes for dinner",
        "Environmental policy debate",
    ]

    results = service.find_similar_texts("climate policy", candidates, top_k=2)

    assert len(results) == 2
    # First result should be climate-related
    assert results[0][1] > 0.6  # Similarity score


def test_singleton_instance():
    """Test get_embedding_service returns singleton."""
    service1 = get_embedding_service()
    service2 = get_embedding_service()

    assert service1 is service2
