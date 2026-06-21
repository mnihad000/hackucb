from __future__ import annotations

from datetime import datetime, timedelta, timezone

from models.trending import PublishedTrendingSnapshot, TopicTimelinePoint, TrendingTopic


DEMO_TRENDING_WARNING = (
    "Live trending articles can also be generated from the discovery pipeline."
)


def build_demo_trending_snapshot(*, now: datetime | None = None) -> PublishedTrendingSnapshot:
    now = now or datetime.now(timezone.utc)
    topics = [
        _topic(
            topic_id="demo_trump_ballroom",
            title="Trump's White House Ballroom",
            canonical_phrase="trump's ballroom",
            summary=(
                "Coverage clusters around the White House ballroom project, "
                "funding questions, preservation concerns, and official responses."
            ),
            related_phrases=["white house ballroom", "east wing construction", "ballroom funding"],
            source_mix={"national_news": 3, "official_statement": 1, "commentary": 1},
            first_seen=now - timedelta(hours=10),
            latest_seen=now - timedelta(minutes=35),
            velocity=7.2,
            confidence=0.74,
        ),
        _topic(
            topic_id="demo_ai_policy_controls",
            title="AI Export Controls Debate",
            canonical_phrase="ai export controls",
            summary=(
                "A policy story branches between national-security framing, "
                "industry competitiveness, and access to advanced model infrastructure."
            ),
            related_phrases=["ai chips", "model access", "export restrictions"],
            source_mix={"national_news": 2, "official_statement": 1, "technology_news": 2},
            first_seen=now - timedelta(hours=8),
            latest_seen=now - timedelta(minutes=52),
            velocity=5.6,
            confidence=0.68,
        ),
        _topic(
            topic_id="demo_fed_rate_path",
            title="Fed Rate Path Speculation",
            canonical_phrase="fed rate path",
            summary=(
                "Markets, policy commentators, and officials are framing the same signals "
                "through competing recession-risk and inflation-risk narratives."
            ),
            related_phrases=["federal reserve", "rate cuts", "inflation outlook"],
            source_mix={"national_news": 2, "financial_news": 2, "commentary": 1},
            first_seen=now - timedelta(hours=6),
            latest_seen=now - timedelta(minutes=20),
            velocity=4.8,
            confidence=0.64,
        ),
    ]
    return PublishedTrendingSnapshot(
        snapshot_id="demo_cached_trending_v1",
        state="ready",
        generated_at=now,
        fresh_until=now + timedelta(hours=2),
        last_completed_run_at=now,
        last_reseed_at=now,
        warning=DEMO_TRENDING_WARNING,
        topics=topics,
    )


def demo_trending_topics(*, now: datetime | None = None) -> list[TrendingTopic]:
    return build_demo_trending_snapshot(now=now).topics


def _topic(
    *,
    topic_id: str,
    title: str,
    canonical_phrase: str,
    summary: str,
    related_phrases: list[str],
    source_mix: dict[str, int],
    first_seen: datetime,
    latest_seen: datetime,
    velocity: float,
    confidence: float,
) -> TrendingTopic:
    source_count = sum(source_mix.values())
    return TrendingTopic(
        id=topic_id,
        title=title,
        canonical_phrase=canonical_phrase,
        summary=summary,
        related_phrases=related_phrases,
        status="Active",
        confidence_label="Medium",
        confidence_score=confidence,
        source_count=source_count,
        publisher_count=max(3, len(source_mix)),
        first_observed_at=first_seen,
        latest_observed_at=latest_seen,
        source_diversity_snapshot=source_mix,
        timeline=[
            TopicTimelinePoint(timestamp=first_seen, count=1),
            TopicTimelinePoint(timestamp=latest_seen, count=source_count),
        ],
        velocity_score=velocity,
        persistence_runs=1,
        provider_mix={"demo_cache": source_count},
        supporting_document_ids=[],
    )
