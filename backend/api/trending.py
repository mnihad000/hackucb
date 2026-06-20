"""
GET  /api/trending        — top spiking narratives from live store
POST /api/trending/poll   — trigger a fresh GDELT + HN pull for all seed topics

Typical usage:
  1. Call POST /api/trending/poll once to seed the live store.
  2. Call GET /api/trending to get the ranked narrative list.
  3. Wire a cron / scheduler to call poll every 15 minutes.
"""

from fastapi import APIRouter, Query

from services.trending_detector import SEED_TOPICS, TrendingDetector

router = APIRouter(prefix="/api")

# Module-level singleton — PhraseStore state accumulates across requests
_detector = TrendingDetector()


@router.get("/trending")
def get_trending(limit: int = Query(default=10, ge=1, le=25)) -> list[dict]:
    """
    Returns up to `limit` spiking civic narratives detected across GDELT and HN.

    Each item matches the LiveNarrativeTopic shape expected by the frontend:
    id, title, canonical_phrase, spike_score, status, confidence_score,
    confidence_label, source_count, first_observed_at, source_diversity_snapshot,
    recent_growth_rate, timeline (7-day), mutation_count, recent_source_velocity,
    gdelt_confirmed.

    Returns [] if the live store is empty. Call POST /api/trending/poll first.
    """
    return _detector.get_trending(limit=limit)


@router.post("/trending/poll")
def poll_sources(poll_hours: int = Query(default=24, ge=1, le=168)) -> dict:
    """
    Pulls GDELT + HN for all seed topics for the last `poll_hours` hours.
    Saves results to the live DocumentStore and updates the PhraseStore.

    Call this on a 15-minute cron for a live trending feed.
    A single manual call with poll_hours=24 is enough for a demo run.

    Seed topics:
      election, immigration, border, tax, energy, climate, crime, student debt,
      housing, healthcare, protest, education, inflation, voting, AI regulation
    """
    return _detector.poll_sources(poll_hours=poll_hours)


@router.get("/trending/status")
def trending_status() -> dict:
    """Health check for the trending pipeline."""
    return {
        "last_poll": _detector.last_poll,
        "using_redis": _detector._phrase_store.using_redis,
        "seed_topics": SEED_TOPICS,
        "seed_topic_count": len(SEED_TOPICS),
    }
