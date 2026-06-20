from difflib import SequenceMatcher
from datetime import datetime

from config import get_settings
from models.document import Document
from models.narrative import MutationEntry, NarrativeCluster


class MutationDetector:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def detect_mutations(self, documents: list[Document]) -> list[dict]:
        """
        Compares all phrase pairs across documents.
        Returns a list of mutation records sorted by doc_a timestamp ascending.
        """
        low = self._settings.MUTATION_SIMILARITY_LOW
        high = self._settings.MUTATION_SIMILARITY_HIGH

        # Build flat list of (phrase, doc) pairs
        phrase_doc_pairs: list[tuple[str, Document]] = []
        for doc in documents:
            for phrase in doc.phrases:
                phrase_doc_pairs.append((phrase, doc))

        mutations: list[dict] = []
        seen: set[tuple[str, str]] = set()

        for i, (phrase_a, doc_a) in enumerate(phrase_doc_pairs):
            for phrase_b, doc_b in phrase_doc_pairs[i + 1:]:
                if doc_a.id == doc_b.id:
                    continue
                # Ensure chronological order
                if doc_a.published_at > doc_b.published_at:
                    phrase_a, doc_a, phrase_b, doc_b = phrase_b, doc_b, phrase_a, doc_a

                key = (phrase_a, phrase_b, doc_a.id, doc_b.id)
                if key in seen:
                    continue
                seen.add(key)

                sim = self._similarity(phrase_a, phrase_b)
                if sim > 1.0 - 1e-9:
                    # Identical phrases — not a mutation
                    continue

                if low <= sim <= high:
                    mutation_type = "mutation"
                elif sim > high:
                    mutation_type = "phrase_reuse"
                else:
                    continue

                mutations.append({
                    "phrase_a": phrase_a,
                    "phrase_b": phrase_b,
                    "similarity": round(sim, 4),
                    "mutation_type": mutation_type,
                    "doc_a_id": doc_a.id,
                    "doc_b_id": doc_b.id,
                    "doc_a_timestamp": doc_a.published_at,
                    "doc_b_timestamp": doc_b.published_at,
                })

        return sorted(mutations, key=lambda m: m["doc_a_timestamp"])

    def build_mutation_trail(
        self,
        mutations: list[dict],
        cluster: NarrativeCluster,
    ) -> list[MutationEntry]:
        """
        Returns a deduplicated chronological mutation trail for this cluster.
        In demo mode, returns the pre-built trail from the cluster.
        """
        if get_settings().DEMO_MODE:
            return cluster.mutation_trail

        seen_phrases: set[str] = set()
        trail: list[MutationEntry] = []

        for m in mutations:
            for phrase, doc_id, ts, source_type in [
                (m["phrase_a"], m["doc_a_id"], m["doc_a_timestamp"], ""),
                (m["phrase_b"], m["doc_b_id"], m["doc_b_timestamp"], ""),
            ]:
                if phrase not in seen_phrases:
                    seen_phrases.add(phrase)
                    trail.append(
                        MutationEntry(
                            phrase=phrase,
                            first_doc_id=doc_id,
                            timestamp=ts,
                            source_type=source_type,
                        )
                    )

        return sorted(trail, key=lambda e: e.timestamp)
