#!/usr/bin/env python3
"""
Redis Setup Script for RhetoriQ

This script:
1. Tests Redis connection
2. Creates RediSearch vector indices
3. Optionally indexes demo documents
4. Verifies vector search functionality

Run this after starting Redis Stack:
    python backend/setup_redis.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_redis_connection():
    """Test basic Redis connection."""
    from config import get_settings

    settings = get_settings()

    try:
        import redis as redis_lib

        client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=5)
        client.ping()
        logger.info(f"✅ Redis connected: {settings.REDIS_URL}")
        return client
    except Exception as exc:
        logger.error(f"❌ Redis connection failed: {exc}")
        logger.error(
            "\nMake sure Redis Stack is running:\n"
            "  docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest\n"
        )
        return None


def create_vector_index():
    """Create RediSearch vector index for documents."""
    from services.redis_vector_store import RedisVectorStore
    from config import get_settings

    settings = get_settings()

    try:
        store = RedisVectorStore()
        dimension = settings.EMBEDDING_DIMENSION

        logger.info(f"Creating RediSearch vector index (dimension={dimension})...")
        created = store.create_index(dimension=dimension, index_type="HNSW")

        if created:
            logger.info("✅ Vector index created successfully")
        else:
            logger.info("ℹ️  Vector index already exists")

        return store
    except Exception as exc:
        logger.error(f"❌ Failed to create vector index: {exc}")
        return None


def index_demo_documents(limit: int = 20):
    """Index demo documents with embeddings."""
    from demo_data import ALL_DOCUMENTS
    from services.redis_vector_store import RedisVectorStore

    try:
        store = RedisVectorStore()
        docs_to_index = ALL_DOCUMENTS[:limit]

        logger.info(f"Indexing {len(docs_to_index)} demo documents...")
        added = store.add_documents_batch(docs_to_index, generate_embeddings=True)

        logger.info(f"✅ Indexed {added} documents with embeddings")
        return added
    except Exception as exc:
        logger.error(f"❌ Failed to index documents: {exc}")
        return 0


def test_vector_search():
    """Test semantic search functionality."""
    from services.redis_vector_store import RedisVectorStore

    try:
        store = RedisVectorStore()

        test_queries = [
            "energy policy costs",
            "climate change narrative",
            "government regulation",
        ]

        logger.info("\n🔍 Testing vector search:")
        for query in test_queries:
            results = store.semantic_search(query, limit=3)
            logger.info(f"\nQuery: '{query}'")
            if results:
                for i, result in enumerate(results, 1):
                    logger.info(
                        f"  {i}. {result.title[:60]}... "
                        f"(score: {result.score:.3f}, source: {result.source_name})"
                    )
            else:
                logger.warning(f"  No results found")

        logger.info("\n✅ Vector search working!")
        return True
    except Exception as exc:
        logger.error(f"❌ Vector search test failed: {exc}")
        return False


def test_investigation_cache():
    """Test investigation caching."""
    from services.investigation_cache import InvestigationCache
    from models.investigation import InvestigationWorkspace, InvestigationPlan
    from datetime import datetime
    import redis as redis_lib
    from config import get_settings

    settings = get_settings()

    try:
        client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        cache = InvestigationCache(client, default_ttl_seconds=300)

        # Create test workspace
        test_plan = InvestigationPlan(
            query_text="test query",
            topic="test topic",
            canonical_phrase="test phrase",
            intent="general investigation",
        )

        workspace = InvestigationWorkspace(
            investigation_id="test_cache_001",
            query_text="test query",
            status="planning_completed",
            current_stage="planner",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            plan=test_plan,
            retrieval=None,
            retrieved_documents=[],
            timeline=None,
            counter_narratives=None,
            analyst=None,
            report=None,
        )

        # Test cache write
        logger.info("\n💾 Testing investigation cache:")
        success = cache.cache_workspace(workspace, ttl_seconds=60)
        if success:
            logger.info("  ✅ Cached workspace")
        else:
            logger.error("  ❌ Failed to cache workspace")
            return False

        # Test cache read
        retrieved = cache.get_workspace("test_cache_001")
        if retrieved and retrieved.investigation_id == "test_cache_001":
            logger.info("  ✅ Retrieved cached workspace")
        else:
            logger.error("  ❌ Failed to retrieve workspace")
            return False

        # Test stats
        stats = cache.get_stats()
        logger.info(f"  📊 Cache stats: {stats}")

        # Cleanup
        cache.invalidate("test_cache_001")
        logger.info("  ✅ Investigation cache working!")

        return True
    except Exception as exc:
        logger.error(f"❌ Investigation cache test failed: {exc}")
        return False


def show_health_status():
    """Show comprehensive health status."""
    from services.redis_vector_store import RedisVectorStore

    logger.info("\n📊 Redis Health Status:")

    try:
        store = RedisVectorStore()
        health = store.health_check()

        logger.info(f"  Connected: {health.get('connected')}")
        logger.info(f"  Index: {health.get('index_name')}")
        logger.info(f"  Index exists: {health.get('index_exists')}")
        logger.info(f"  Documents: {health.get('document_count')}")
        logger.info(f"  Embedding model: {health.get('embedding_model')}")
        logger.info(f"  Embedding dimension: {health.get('embedding_dimension')}")

        return True
    except Exception as exc:
        logger.error(f"❌ Health check failed: {exc}")
        return False


def main():
    """Run full Redis setup."""
    logger.info("=" * 60)
    logger.info("RhetoriQ Redis Setup")
    logger.info("=" * 60)

    # Step 1: Test connection
    client = test_redis_connection()
    if not client:
        sys.exit(1)

    # Step 2: Create vector index
    store = create_vector_index()
    if not store:
        sys.exit(1)

    # Step 3: Index demo documents (optional, comment out if slow)
    logger.info("\n" + "=" * 60)
    response = input("Index demo documents? This may take 1-2 minutes. (y/N): ")
    if response.lower() == "y":
        indexed = index_demo_documents(limit=50)
        if indexed > 0:
            # Step 4: Test vector search
            test_vector_search()

    # Step 5: Test investigation cache
    test_investigation_cache()

    # Step 6: Show health status
    show_health_status()

    logger.info("\n" + "=" * 60)
    logger.info("✅ Redis setup complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. Update backend/.env with Redis settings")
    logger.info("  2. Run backend server: uvicorn main:app --reload")
    logger.info("  3. Test semantic search in investigations")
    logger.info("\nFor sponsor evidence, document in docs/REDIS_SPONSOR_INTEGRATION.md")


if __name__ == "__main__":
    main()
