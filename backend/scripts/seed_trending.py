"""
Quick-seed: fetch 4 trending political/news stories via Tavily right now and
write them directly into Redis as a PublishedTrendingSnapshot.

Run from the backend/ directory:
    python scripts/seed_trending.py
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx

from config import get_settings
from models.trending import PublishedTrendingSnapshot, TrendingTopic
from services.trending_runtime import TrendingRuntimeStore


def _search_tavily(api_key: str, query: str, max_results: int = 6) -> list[dict]:
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True,
        "topic": "news",
    }
    with httpx.Client(timeout=20) as client:
        r = client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
    return r.json().get("results") or []


def _make_topic(result: dict, index: int, query: str) -> TrendingTopic:
    now = datetime.now(timezone.utc)
    title = result.get("title") or query
    url   = result.get("url") or ""
    snippet = (result.get("content") or "")[:300]
    domain = url.split("/")[2] if url.startswith("http") else "unknown"
    return TrendingTopic(
        id=f"seed_{uuid4().hex[:12]}",
        title=title,
        canonical_phrase=" ".join(title.lower().split()[:5]),
        summary=snippet or title,
        related_phrases=[query],
        status="active",
        confidence_label="Medium",
        confidence_score=round(0.65 - index * 0.03, 2),
        source_count=1,
        publisher_count=1,
        first_observed_at=now,
        latest_observed_at=now,
        source_diversity_snapshot={domain: 1},
        velocity_score=round(0.8 - index * 0.07, 2),
        provider_mix={"tavily": 1},
        supporting_document_ids=[],
    )


def main() -> None:
    settings = get_settings()

    if not settings.TAVILY_API_KEY:
        print("ERROR: TAVILY_API_KEY not set")
        sys.exit(1)
    if not settings.REDIS_URL:
        print("ERROR: REDIS_URL not set")
        sys.exit(1)

    queries = [
        "breaking political news today",
        "major policy news today",
        "US government news today",
        "world news headline today",
    ]

    print("Searching Tavily for trending stories...")
    topics: list[TrendingTopic] = []
    for query in queries:
        if len(topics) >= 4:
            break
        try:
            results = _search_tavily(settings.TAVILY_API_KEY, query, max_results=3)
            if results:
                topic = _make_topic(results[0], len(topics), query)
                topics.append(topic)
                print(f"  [{len(topics)}] {topic.title[:80]}")
        except Exception as exc:
            print(f"  WARN: {query!r} failed — {exc}")

    if not topics:
        print("ERROR: No results returned from Tavily")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    snapshot = PublishedTrendingSnapshot(
        snapshot_id=f"seed_{uuid4().hex}",
        state="ready",
        generated_at=now,
        fresh_until=now + timedelta(hours=1),
        last_completed_run_at=now,
        last_reseed_at=now,
        topics=topics,
    )

    import redis as _r
    _client = _r.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=10, socket_timeout=10)
    _client.ping()

    store = TrendingRuntimeStore.__new__(TrendingRuntimeStore)
    store._redis = _client
    store.set_latest_snapshot(snapshot)
    print(f"\nDone — {len(topics)} stories seeded into Redis (fresh for 1 hour)")
    print("The frontend will pick them up on the next GET /api/trending call.")


if __name__ == "__main__":
    main()
