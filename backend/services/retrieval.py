from config import get_settings
from datetime import datetime, timezone
from models.document import Document
from models.narrative import NarrativeCluster
from models.report import InvestigationReport


# In-memory semantic cache: {cluster_id: {"report": InvestigationReport, "cached_at": str}}
_REPORT_CACHE: dict[str, dict] = {}


class Retriever:
    def __init__(self) -> None:
        self._settings = get_settings()

    def get_documents_by_ids(self, ids: list[str], all_docs: list[Document]) -> list[Document]:
        id_set = set(ids)
        return [d for d in all_docs if d.id in id_set]

    def get_related_documents(
        self,
        cluster: NarrativeCluster,
        all_docs: list[Document],
    ) -> list[Document]:
        """Returns cluster documents sorted by published_at ascending."""
        docs = self.get_documents_by_ids(cluster.document_ids, all_docs)
        return sorted(docs, key=lambda d: d.published_at or datetime.max.replace(tzinfo=timezone.utc))

    def build_context_packet(
        self,
        cluster: NarrativeCluster,
        all_docs: list[Document],
        prior_memory: dict | None = None,
    ) -> dict:
        """
        Assembles the Redis-style context packet before any LLM call.
        In demo mode the packet is built from in-memory data.
        Real implementation replaces this with Redis vector search + sorted sets.
        """
        related = self.get_related_documents(cluster, all_docs)

        phrase_stats: dict[str, dict] = {}
        for entry in cluster.mutation_trail:
            # Count docs that contain this phrase
            count = sum(
                1 for d in related
                if entry.phrase.lower() in d.text.lower()
                or any(entry.phrase.lower() in p.lower() for p in d.phrases)
            )
            phrase_stats[entry.phrase] = {
                "spike_score": cluster.spike_score,
                "first_seen": entry.timestamp.isoformat(),
                "count": count,
            }

        retrieval_mode = "narrow" if prior_memory else "broad"

        return {
            "retrieval_mode": retrieval_mode,
            "retrieved_sources": [d.id for d in related],
            "prior_memories": list(prior_memory.keys()) if prior_memory else [],
            "phrase_stats": phrase_stats,
        }

    def get_semantic_cache_hit(
        self,
        cluster_id: str,
        report_cache: dict | None = None,
    ) -> InvestigationReport | None:
        cache = report_cache if report_cache is not None else _REPORT_CACHE
        entry = cache.get(cluster_id)
        if entry:
            report = entry["report"]
            return report.model_copy(update={"cached": True})
        return None

    def save_to_cache(
        self,
        cluster_id: str,
        report: InvestigationReport,
        report_cache: dict | None = None,
    ) -> None:
        from datetime import datetime, timezone
        cache = report_cache if report_cache is not None else _REPORT_CACHE
        cache[cluster_id] = {
            "report": report,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
