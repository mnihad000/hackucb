import math
import os

import pytest

from services.redis_memory import RedisMemoryService


class FakeEmbeddingService:
    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * 4
        lower = text.lower()
        if "climate" in lower:
            vector[0] = 1.0
        if "policy" in lower:
            vector[1] = 1.0
        if "pasta" in lower:
            vector[3] = 1.0
        if not any(vector):
            vector[2] = 1.0
        return vector


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.sets = {}
        self.vectors = {}

    def ping(self):
        return True

    def set(self, key, value):
        self.values[key] = value
        return True

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)
        return 1

    def smembers(self, key):
        return self.sets.get(key, set())

    def execute_command(self, *args):
        command = args[0]
        if command == "VADD":
            key = args[1]
            dimension = int(args[3])
            vector = [float(value) for value in args[4 : 4 + dimension]]
            item_id = args[4 + dimension]
            self.vectors.setdefault(key, {})[item_id] = vector
            return 1
        if command == "VSIM":
            key = args[1]
            dimension = int(args[3])
            query = [float(value) for value in args[4 : 4 + dimension]]
            count = int(args[args.index("COUNT") + 1])
            scored = [
                (item_id, _cosine(query, vector))
                for item_id, vector in self.vectors.get(key, {}).items()
            ]
            scored.sort(key=lambda item: item[1], reverse=True)
            flattened = []
            for item_id, score in scored[:count]:
                flattened.extend([item_id, str(score)])
            return flattened
        if command == "VCARD":
            return len(self.vectors.get(args[1], {}))
        raise AssertionError(f"Unexpected Redis command: {args}")


def _cosine(left, right):
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def test_store_article_vector_preserves_metadata():
    redis = FakeRedis()
    memory = RedisMemoryService(redis_client=redis, embedding_service=FakeEmbeddingService())

    stored = memory.store_article_vector(
        "article_1",
        "Climate policy spreads locally",
        [1.0, 1.0, 0.0, 0.0],
        {
            "investigation_id": "inv_1",
            "source_name": "Local News",
            "source_url": "https://example.com/a",
            "narrative_role": "main",
        },
    )
    context = memory.get_investigation_context("inv_1")

    assert stored is True
    assert context["articles"][0]["metadata"]["source_name"] == "Local News"
    assert context["articles"][0]["metadata"]["source_url"] == "https://example.com/a"
    assert context["articles"][0]["metadata"]["narrative_role"] == "main"


def test_search_similar_claims_returns_metadata():
    redis = FakeRedis()
    memory = RedisMemoryService(redis_client=redis, embedding_service=FakeEmbeddingService())
    memory.store_claim_vector(
        "claim_climate",
        "Climate policy claim",
        [1.0, 1.0, 0.0, 0.0],
        {"investigation_id": "inv_1", "agent_name": "Analyst Agent"},
    )
    memory.store_claim_vector(
        "claim_pasta",
        "Pasta dinner claim",
        [0.0, 0.0, 0.0, 1.0],
        {"investigation_id": "inv_2", "agent_name": "Analyst Agent"},
    )

    results = memory.search_similar_claims([1.0, 1.0, 0.0, 0.0], top_k=1)

    assert results[0]["id"] == "claim_climate"
    assert results[0]["metadata"]["investigation_id"] == "inv_1"


def test_investigation_context_groups_memory_items():
    redis = FakeRedis()
    memory = RedisMemoryService(redis_client=redis, embedding_service=FakeEmbeddingService())

    memory.store_article_vector("article_1", "Climate article", [1.0, 0.0, 0.0, 0.0], {"investigation_id": "inv_1"})
    memory.store_claim_vector("claim_1", "Climate claim", [1.0, 0.0, 0.0, 0.0], {"investigation_id": "inv_1"})
    memory.store_timeline_event("event_1", "First timeline node", [1.0, 0.0, 0.0, 0.0], {"investigation_id": "inv_1"})
    memory.store_agent_finding("finding_1", "Safety Agent", "inv_1", "Use cautious language", {})

    context = memory.get_investigation_context("inv_1")

    assert [item["id"] for item in context["articles"]] == ["article_1"]
    assert [item["id"] for item in context["claims"]] == ["claim_1"]
    assert [item["id"] for item in context["timeline_events"]] == ["event_1"]
    assert [item["id"] for item in context["agent_findings"]] == ["finding_1"]


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_REDIS_TESTS") != "1",
    reason="Set RUN_REDIS_TESTS=1 to run against real Redis.",
)
def test_real_redis_memory_round_trip():
    memory = RedisMemoryService(embedding_service=FakeEmbeddingService())
    assert memory.available is True

    stored = memory.store_claim_vector(
        "test_real_claim",
        "Climate policy claim",
        [1.0, 1.0, 0.0, 0.0],
        {"investigation_id": "inv_real_memory_test"},
    )
    results = memory.search_similar_claims([1.0, 1.0, 0.0, 0.0], top_k=1)

    assert stored is True
    assert any(result["id"] == "test_real_claim" for result in results)
