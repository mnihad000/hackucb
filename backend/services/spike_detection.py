from collections import defaultdict
from datetime import datetime, timezone

from config import get_settings
from models.document import Document
from models.narrative import NarrativeCluster


class SpikeDetector:
    def __init__(self) -> None:
        self._settings = get_settings()

    def compute_spike_score(self, phrase: str, documents: list[Document]) -> float:
        """
        spike_score = mentions_in_most_recent_day / max(1, avg_daily_mentions_in_prior_N_days)
        where N = settings.SPIKE_WINDOW_DAYS
        """
        phrase_lower = phrase.lower()
        daily: dict[str, int] = defaultdict(int)

        for doc in documents:
            if doc.published_at and (any(phrase_lower in p.lower() for p in doc.phrases) or phrase_lower in doc.text.lower()):
                day = doc.published_at.strftime("%Y-%m-%d")
                daily[day] += 1

        if not daily:
            return 0.0

        sorted_days = sorted(daily.keys())
        most_recent_day = sorted_days[-1]
        recent_count = daily[most_recent_day]

        prior_days = sorted_days[-(self._settings.SPIKE_WINDOW_DAYS + 1):-1]
        if not prior_days:
            # No prior data — any mention is a spike
            return round(float(recent_count), 2)

        avg_prior = sum(daily[d] for d in prior_days) / len(prior_days)
        return round(recent_count / max(1.0, avg_prior), 2)

    def get_spiking_narratives(
        self,
        clusters: list[NarrativeCluster],
        documents: list[Document],
    ) -> list[NarrativeCluster]:
        """Returns clusters sorted by spike_score descending."""
        if get_settings().DEMO_MODE:
            return sorted(clusters, key=lambda c: c.spike_score, reverse=True)

        enriched: list[NarrativeCluster] = []
        for cluster in clusters:
            cluster_docs = [d for d in documents if d.id in cluster.document_ids]
            best_phrase = cluster.canonical_phrases[0] if cluster.canonical_phrases else ""
            score = self.compute_spike_score(best_phrase, cluster_docs)
            enriched.append(cluster.model_copy(update={"spike_score": score}))

        return sorted(enriched, key=lambda c: c.spike_score, reverse=True)

    def compute_phrase_timeline(self, phrase: str, documents: list[Document]) -> list[dict]:
        """Returns [{date, count}] sorted ascending for frontend spike chart."""
        phrase_lower = phrase.lower()
        daily: dict[str, int] = defaultdict(int)

        for doc in documents:
            if doc.published_at and (any(phrase_lower in p.lower() for p in doc.phrases) or phrase_lower in doc.text.lower()):
                day = doc.published_at.strftime("%Y-%m-%d")
                daily[day] += 1

        return [{"date": d, "count": daily[d]} for d in sorted(daily.keys())]
