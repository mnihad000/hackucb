"""
Live trending narrative detector.

Full pipeline:
  1. Pull GDELT (artlist) + HN for every SEED_TOPIC for the last N hours
  2. Normalize into Document objects, save to live store
  3. Record per-doc phrase mentions in PhraseStore by hour bucket
  4. Extract corpus-level n-gram phrases across all doc titles
  5. Score each candidate phrase: spike_score = recent_24h / prior_7d_avg
  6. Verify top spikes against GDELT TimelineVolRaw → +confidence bonus
  7. Derive lifecycle status and confidence label
  8. Return top N as LiveNarrativeTopic dicts ready for the API
"""

import hashlib
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from config import get_settings
from models.document import Document
from services.document_store import live_store
from services.gdelt import GDELTIngestion
from services.hn_ingestion import HNIngestion
from services.phrase_extractor import extract_top_phrases
from services.redis_store import PhraseStore


SEED_TOPICS = [
    "election",
    "immigration",
    "border",
    "tax",
    "energy",
    "climate",
    "crime",
    "student debt",
    "housing",
    "healthcare",
    "protest",
    "education",
    "inflation",
    "voting",
    "AI regulation",
]


# ---------------------------------------------------------------------------
# Output shape (matches LiveNarrativeTopic from FRONTEND_DESCRIPTION.md)
# ---------------------------------------------------------------------------

@dataclass
class LiveNarrativeTopic:
    id: str
    title: str
    canonical_phrase: str
    summary: str
    spike_score: float
    status: str
    confidence_score: float
    confidence_label: str
    source_count: int
    first_observed_at: str
    source_diversity_snapshot: dict
    recent_growth_rate: str
    timeline: list
    mutation_count: int = 0
    recent_source_velocity: int = 0
    gdelt_confirmed: bool = False


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _narrative_id(phrase: str) -> str:
    return "live_" + hashlib.md5(phrase.encode()).hexdigest()[:8]


def _build_diversity(docs: list[Document]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for doc in docs:
        counts[doc.source_type] += 1
    return dict(counts)


def _source_mix_label(diversity: dict[str, int]) -> str:
    labels = {
        "national_news": "National news",
        "local_news": "Local news",
        "forum": "Forum",
        "blog": "Blog",
        "commentary": "Commentary",
    }
    parts = [f"{labels[k]}: {v}" for k, v in labels.items() if diversity.get(k, 0) > 0]
    return ", ".join(parts) if parts else "Mixed"


def _derive_status(
    spike_score: float,
    hours_since_first: float,
    diversity: dict[str, int],
) -> str:
    total = sum(diversity.values()) or 1
    national = diversity.get("national_news", 0) + diversity.get("commentary", 0)
    cross_type = sum(1 for v in diversity.values() if v > 0)

    if spike_score >= 5 and hours_since_first < 24:
        return "emerging"
    if spike_score >= 4 and cross_type >= 2:
        return "amplifying"
    if spike_score >= 3 and national / total >= 0.25:
        return "mainstreaming"
    if spike_score < 2:
        return "declining"
    return "emerging"


def _derive_confidence(
    spike_score: float,
    source_count: int,
    cross_type_count: int,
    gdelt_confirmed: bool,
) -> tuple[float, str]:
    score = 0.0
    score += min(spike_score / 10.0, 0.35)       # spike strength, max 0.35
    score += min(source_count / 30.0, 0.30)       # source volume, max 0.30
    score += min(cross_type_count / 4.0, 0.20)    # source type diversity, max 0.20
    if gdelt_confirmed:
        score += 0.15                              # external GDELT confirmation

    score = round(score, 2)
    if score >= 0.70:
        label = "High"
    elif score >= 0.40:
        label = "Medium"
    else:
        label = "Low"
    return score, label


def _build_timeline(phrase: str, docs: list[Document], now: datetime) -> list[dict]:
    """7-day daily mention count for the spark chart."""
    return [
        {
            "date": (now - timedelta(days=d)).strftime("%Y-%m-%d"),
            "count": sum(
                1 for doc in docs
                if doc.published_at
                and doc.published_at.strftime("%Y-%m-%d") == (now - timedelta(days=d)).strftime("%Y-%m-%d")
            ),
        }
        for d in range(6, -1, -1)
    ]


def _phrase_docs(phrase: str, docs: list[Document]) -> list[Document]:
    pl = phrase.lower()
    return [
        d for d in docs
        if pl in d.title.lower() or any(pl in p.lower() for p in d.phrases)
    ]


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

class TrendingDetector:
    """
    Module-level singleton. Holds PhraseStore state across requests so that
    hourly bucket counts accumulate between polls.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._gdelt = GDELTIngestion()
        self._hn = HNIngestion()
        self._phrase_store = PhraseStore(redis_url=self._settings.REDIS_URL)
        self._last_poll: datetime | None = None

    # ------------------------------------------------------------------
    # Step 1 — pull sources
    # ------------------------------------------------------------------

    def poll_sources(self, poll_hours: int = 24) -> dict:
        """
        Pulls GDELT + HN for every SEED_TOPIC for the last `poll_hours` hours.
        Records phrase mentions in PhraseStore. Typically called every 15 min.
        """
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(hours=poll_hours)
        errors: list[str] = []
        total = 0

        for topic in SEED_TOPICS:
            # GDELT
            try:
                gdelt_docs = self._gdelt.fetch_articles(
                    query=topic,
                    start_dt=start_dt,
                    end_dt=now,
                    max_records=75,
                )
                live_store.save_batch(gdelt_docs)
                total += len(gdelt_docs)
                for doc in gdelt_docs:
                    for phrase in doc.phrases:
                        self._phrase_store.record_phrase(phrase, doc.published_at, doc.id)
            except Exception as exc:
                errors.append(f"GDELT/{topic}: {exc}")

            # HN
            try:
                hn_docs = self._hn.fetch_stories(
                    query=topic, start_dt=start_dt, end_dt=now, num_results=25
                )
                live_store.save_batch(hn_docs)
                total += len(hn_docs)
                for doc in hn_docs:
                    for phrase in doc.phrases:
                        self._phrase_store.record_phrase(phrase, doc.published_at, doc.id)
            except Exception as exc:
                errors.append(f"HN/{topic}: {exc}")

        self._last_poll = now
        return {
            "polled_at": now.isoformat(),
            "topics_polled": len(SEED_TOPICS),
            "total_ingested": total,
            "store_total": live_store.count(),
            "using_redis": self._phrase_store.using_redis,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Steps 2–9 — detect trending
    # ------------------------------------------------------------------

    def get_trending(self, limit: int = 10) -> list[dict]:
        """
        Returns the top `limit` spiking narratives as dicts.
        If the live store is empty, returns [].
        """
        now = datetime.now(timezone.utc)
        docs = live_store.get_all()
        if not docs:
            return []

        # Step 2: corpus-level n-gram extraction across all doc titles
        texts = [doc.title for doc in docs]
        corpus_phrases = extract_top_phrases(
            texts,
            ngram_range=(2, 4),
            top_n=150,
            min_doc_freq=2,
        )

        # Step 3: merge with phrase store top phrases (richer with hour-bucket data)
        store_top = dict(self._phrase_store.get_top_phrases(150))
        merged: dict[str, int] = {p: c for p, c in corpus_phrases}
        for phrase, count in store_top.items():
            merged[phrase] = max(merged.get(phrase, 0), count)

        # Step 4: score and filter
        threshold = self._settings.TRENDING_SPIKE_THRESHOLD
        min_docs = self._settings.TRENDING_MIN_DOCS
        seen_phrases: set[str] = set()
        candidates: list[LiveNarrativeTopic] = []

        for phrase, _ in sorted(merged.items(), key=lambda x: x[1], reverse=True):
            if len(candidates) >= limit * 4:
                break

            # Skip substrings/superstrings of already-selected phrases
            pl = phrase.lower()
            if any(pl in sp or sp in pl for sp in seen_phrases):
                continue

            matched_docs = _phrase_docs(phrase, docs)
            source_count = len(matched_docs)
            if source_count < min_docs:
                continue

            spike_score = self._phrase_store.compute_spike_score(phrase, now)
            if spike_score < threshold:
                continue

            seen_phrases.add(pl)

            matched_sorted = sorted(
                [doc for doc in matched_docs if doc.published_at is not None],
                key=lambda d: d.published_at,
            )
            if not matched_sorted:
                continue
            first_doc = matched_sorted[0]
            hours_since_first = (now - first_doc.published_at).total_seconds() / 3600

            diversity = _build_diversity(matched_docs)
            cross_type_count = sum(1 for v in diversity.values() if v > 0)

            # Step 5: GDELT external timeline confirmation
            gdelt_confirmed = False
            try:
                timeline_vol = self._gdelt.fetch_timeline_vol(phrase, days=7)
                if len(timeline_vol) >= 2:
                    last = timeline_vol[-1].get("count", 0)
                    prior_avg = sum(t.get("count", 0) for t in timeline_vol[:-1]) / max(1, len(timeline_vol) - 1)
                    gdelt_confirmed = last > prior_avg * 1.5
            except Exception:
                gdelt_confirmed = False

            if gdelt_confirmed:
                spike_score = round(spike_score * 1.15, 2)

            status = _derive_status(spike_score, hours_since_first, diversity)
            confidence_score, confidence_label = _derive_confidence(
                spike_score, source_count, cross_type_count, gdelt_confirmed
            )
            timeline = _build_timeline(phrase, matched_docs, now)
            recent_velocity = sum(
                1 for d in matched_docs if d.published_at and d.published_at >= now - timedelta(hours=2)
            )

            candidates.append(LiveNarrativeTopic(
                id=_narrative_id(phrase),
                title=phrase.title(),
                canonical_phrase=phrase,
                summary=(
                    f"Phrase '{phrase}' is appearing across {source_count} sources "
                    f"({_source_mix_label(diversity)})."
                ),
                spike_score=spike_score,
                status=status,
                confidence_score=confidence_score,
                confidence_label=confidence_label,
                source_count=source_count,
                first_observed_at=first_doc.published_at.isoformat(),
                source_diversity_snapshot=diversity,
                recent_growth_rate=f"{spike_score}x baseline",
                timeline=timeline,
                mutation_count=0,
                recent_source_velocity=recent_velocity,
                gdelt_confirmed=gdelt_confirmed,
            ))

        candidates.sort(key=lambda c: c.spike_score, reverse=True)
        return [asdict(c) for c in candidates[:limit]]

    @property
    def last_poll(self) -> str | None:
        return self._last_poll.isoformat() if self._last_poll else None
