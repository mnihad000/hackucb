import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient

from api import trending as trending_api
from main import app
from models.document import Document
from models.trending import (
    DiscoveryQuery,
    PublishedTrendingSnapshot,
    TopicTimelinePoint,
    TrendingFeedResponse,
    TrendingTopic,
)
from services.investigation_repository import InvestigationRepository
from services.search_provider import MultiSearchProvider, SerpApiSearchProvider
from services.trending_ranker import TrendingRanker
from services.trending_repository import TrendingRepository
from services.trending_service import TrendingService

client = TestClient(app)


def _document(doc_id: str, title: str, url: str, published_at: datetime, source_type: str) -> Document:
    return Document(
        id=doc_id,
        source_id=f"domain:{url.split('/')[2]}",
        source_name=url.split("/")[2],
        source_type=source_type,
        url=url,
        title=title,
        author=None,
        published_at=published_at,
        collected_at=published_at,
        text=title,
        snippet=title,
        language="en",
        content_type="article",
        geographic_scope="national",
        entities=[],
        phrases=["energy tax"],
        metadata={},
    )


def test_serpapi_provider_normalizes_results(monkeypatch):
    fake_payload = {
        "news_results": [
            {
                "title": "Energy tax story",
                "link": "https://example.com/story",
                "snippet": "A story about an energy tax phrase.",
                "source": {"name": "Example News"},
            }
        ]
    }

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return fake_payload

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url, params):
            return _Response()

    monkeypatch.setattr("httpx.Client", lambda timeout=30: _Client())
    monkeypatch.setattr(
        "services.search_provider.get_settings",
        lambda: type("Settings", (), {"SERPAPI_API_KEY": "test-key"})(),
    )

    provider = SerpApiSearchProvider()
    results = provider.search("energy tax", type("TW", (), {"label": "recent"})(), ["national_news"], 5)
    assert len(results) == 1
    assert results[0].provider == "serpapi"
    assert results[0].metadata["source_name_hint"] == "Example News"


def test_multi_provider_orchestrates_discovery_and_enrichment():
    class _DiscoveryProvider:
        name = "serpapi"

        def __init__(self):
            self.calls = []

        def search(self, query, time_window, source_types, limit):
            self.calls.append(("discovery", query, limit))
            return []

    class _EnrichmentProvider:
        name = "tavily"

        def __init__(self):
            self.calls = []

        def search(self, query, time_window, source_types, limit):
            self.calls.append(("enrichment", query, limit))
            return []

    discovery = _DiscoveryProvider()
    enrichment = _EnrichmentProvider()
    provider = MultiSearchProvider(discovery_provider=discovery, enrichment_provider=enrichment)

    provider.search_discovery("energy tax", type("TW", (), {"label": "recent"})(), [], 4)
    provider.search_enrichment("energy tax counter narrative", type("TW", (), {"label": "recent"})(), [], 3)

    assert discovery.calls == [("discovery", "energy tax", 4)]
    assert enrichment.calls == [("enrichment", "energy tax counter narrative", 3)]
    assert provider.provider_mix == {"discovery": "serpapi", "enrichment": "tavily"}


def test_trending_repository_and_ranker_build_publishable_topic(tmp_path):
    repo = TrendingRepository(str(tmp_path / "trending.sqlite3"))
    now = datetime(2026, 6, 20, 18, 0, tzinfo=timezone.utc)
    queries = [DiscoveryQuery(query="energy tax", provider_role="discovery", topic_seed="energy")]

    repo.create_run("disc_1", is_reseed=True, queries=queries)
    repo.create_run("disc_2", is_reseed=False, queries=queries)

    docs = [
        _document("doc1", "Energy tax debate grows", "https://a.com/story-1", now - timedelta(hours=4), "national_news"),
        _document("doc2", "Energy tax debate expands", "https://b.com/story-2", now - timedelta(hours=3), "commentary"),
        _document("doc3", "Local energy tax debate spreads", "https://c.com/story-3", now - timedelta(hours=2), "local_news"),
        _document("doc4", "Energy tax debate prompts response", "https://d.com/story-4", now - timedelta(hours=1), "national_news"),
    ]

    for doc in docs[:2]:
        repo.save_discovery_document("disc_1", doc, canonical_url=doc.url, domain=doc.source_name, provider="serpapi", search_query="energy tax")
    for doc in docs:
        repo.save_discovery_document("disc_2", doc, canonical_url=doc.url, domain=doc.source_name, provider="tavily", search_query="energy tax narrative")

    ranker = TrendingRanker()
    topics = ranker.rank(repo.list_discovery_documents(), now=now, max_topics=5)

    assert topics
    assert topics[0].canonical_phrase
    assert topics[0].source_count >= 4
    assert topics[0].publisher_count >= 3
    assert topics[0].persistence_runs >= 2


def test_trending_service_reuses_topic_investigation_from_runtime(tmp_path):
    repo = TrendingRepository(str(tmp_path / "trending.sqlite3"))
    investigation_repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))

    class _Runtime:
        redis_available = True

        def __init__(self):
            self.mapping = {}

        def acquire_refresh_lock(self):
            return True

        def release_refresh_lock(self):
            return None

        def refresh_lock_active(self):
            return False

        def set_topic_investigation(self, topic_id, investigation_id, ttl_seconds):
            self.mapping[topic_id] = investigation_id

        def get_topic_investigation(self, topic_id):
            return self.mapping.get(topic_id)

        def set_last_error(self, message):
            return None

        def get_last_error(self):
            return None

    runtime = _Runtime()
    service = TrendingService(repository=repo, runtime_store=runtime)
    generated_at = datetime.now(timezone.utc)
    topic = TrendingTopic(
        id="topic_1",
        title="Energy Tax Debate",
        canonical_phrase="energy tax debate",
        summary="summary",
        related_phrases=["energy tax"],
        status="emerging",
        confidence_label="High",
        confidence_score=0.82,
        source_count=5,
        publisher_count=4,
        first_observed_at=generated_at - timedelta(hours=5),
        latest_observed_at=generated_at - timedelta(hours=1),
        source_diversity_snapshot={"national_news": 3, "commentary": 2},
        timeline=[TopicTimelinePoint(timestamp=generated_at, count=5)],
        velocity_score=2.4,
        persistence_runs=2,
        provider_mix={"serpapi": 3, "tavily": 2},
        supporting_document_ids=["doc1"],
    )
    snapshot = PublishedTrendingSnapshot(
        snapshot_id="snap_1",
        state="ready",
        generated_at=generated_at,
        fresh_until=generated_at + timedelta(hours=6),
        last_completed_run_at=generated_at,
        last_reseed_at=generated_at,
        topics=[topic],
    )
    repo.save_snapshot(snapshot)

    first = service.start_investigation_for_topic("topic_1", investigation_repo)
    second = service.start_investigation_for_topic("topic_1", investigation_repo)

    assert first.reused_existing is False
    assert second.reused_existing is True
    assert first.investigation_id == second.investigation_id


def test_trending_endpoint_returns_live_envelope_without_demo_cards(monkeypatch):
    monkeypatch.setattr(
        trending_api,
        "_service",
        type(
            "StubService",
            (),
            {
                "get_feed": lambda self, limit=6: TrendingFeedResponse(
                    state="warming",
                    warning="Discovery pipeline is warming up.",
                    topics=[],
                )
            },
        )(),
    )

    response = client.get("/api/trending")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "warming"
    assert payload["topics"] == []
    assert "Hidden Energy Tax" not in str(payload)
