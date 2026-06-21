from __future__ import annotations

import re
from difflib import SequenceMatcher

from config import get_settings
from models.document import Document
from models.narrative import MutationEntry, NarrativeCluster

_STOPWORDS = {
    "about",
    "after",
    "against",
    "around",
    "because",
    "between",
    "cost",
    "costs",
    "claim",
    "claims",
    "debate",
    "energy",
    "frame",
    "framing",
    "from",
    "hidden",
    "into",
    "mandate",
    "narrative",
    "over",
    "policy",
    "power",
    "ratepayer",
    "secret",
    "story",
    "surcharge",
    "talking",
    "tax",
    "through",
    "utility",
}


class MutationDetector:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def detect_mutations(self, documents: list[Document]) -> list[dict]:
        """
        Compare phrase pairs across documents and return chronologically ordered
        mutation edges. The result preserves the legacy keys used by the old
        `/api/mutations` route while also adding richer edge metadata for the
        narrative-family artifact.
        """
        low = self._settings.MUTATION_SIMILARITY_LOW
        high = self._settings.MUTATION_SIMILARITY_HIGH

        phrase_doc_pairs: list[tuple[str, Document]] = []
        for doc in documents:
            for phrase in doc.phrases:
                normalized = phrase.strip()
                if normalized:
                    phrase_doc_pairs.append((normalized, doc))

        mutations: list[dict] = []
        seen: set[tuple[str, str, str, str]] = set()

        for i, (left_phrase, left_doc) in enumerate(phrase_doc_pairs):
            for right_phrase, right_doc in phrase_doc_pairs[i + 1 :]:
                if left_doc.id == right_doc.id:
                    continue

                ordered = self._chronological_pair(left_phrase, left_doc, right_phrase, right_doc)
                from_phrase, from_doc, to_phrase, to_doc = ordered
                key = (from_phrase.lower(), to_phrase.lower(), from_doc.id, to_doc.id)
                if key in seen:
                    continue
                seen.add(key)

                if from_doc.published_at is None or to_doc.published_at is None:
                    continue

                lexical_similarity = self._similarity(from_phrase, to_phrase)
                if lexical_similarity > 1.0 - 1e-9:
                    continue

                from_tokens = self._phrase_tokens(from_phrase)
                to_tokens = self._phrase_tokens(to_phrase)
                shared_tokens = from_tokens & to_tokens
                source_shift = from_doc.source_name != to_doc.source_name
                source_type_shift = from_doc.source_type != to_doc.source_type
                salient_overlap = len(shared_tokens & self._salient_terms(from_doc, to_doc))
                overlap_ratio = self._overlap_ratio(from_tokens, to_tokens)
                chrono_hours = max(
                    0.0,
                    (to_doc.published_at - from_doc.published_at).total_seconds() / 3600,
                )
                chronology_bonus = 0.08 if 0.0 <= chrono_hours <= 96.0 else 0.04
                source_shift_bonus = 0.07 if source_shift else 0.0
                source_type_bonus = 0.05 if source_type_shift else 0.0

                combined_score = min(
                    1.0,
                    (lexical_similarity * 0.58)
                    + (overlap_ratio * 0.2)
                    + (min(0.18, salient_overlap * 0.06))
                    + chronology_bonus
                    + source_shift_bonus
                    + source_type_bonus,
                )
                if combined_score < low:
                    continue
                if not shared_tokens and lexical_similarity < (low + 0.06):
                    continue

                mutation_type = "mutation" if combined_score <= high else "phrase_reuse"
                explanation = self._build_explanation(
                    from_phrase=from_phrase,
                    to_phrase=to_phrase,
                    shared_tokens=sorted(shared_tokens),
                    source_shift=source_shift,
                    source_type_shift=source_type_shift,
                    time_delta_hours=chrono_hours,
                    mutation_type=mutation_type,
                )

                mutations.append(
                    {
                        "from_phrase": from_phrase,
                        "to_phrase": to_phrase,
                        "from_doc_id": from_doc.id,
                        "to_doc_id": to_doc.id,
                        "mutation_type": mutation_type,
                        "similarity_score": round(combined_score, 4),
                        "time_delta_hours": round(chrono_hours, 2),
                        "source_shift": source_shift,
                        "explanation": explanation,
                        # Legacy compatibility for existing callers/tests/routes.
                        "phrase_a": from_phrase,
                        "phrase_b": to_phrase,
                        "similarity": round(combined_score, 4),
                        "doc_a_id": from_doc.id,
                        "doc_b_id": to_doc.id,
                        "doc_a_timestamp": from_doc.published_at,
                        "doc_b_timestamp": to_doc.published_at,
                    }
                )

        return sorted(
            mutations,
            key=lambda item: (
                item["doc_a_timestamp"],
                item["time_delta_hours"],
                item["from_phrase"].lower(),
                item["to_phrase"].lower(),
            ),
        )

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

        for mutation in mutations:
            for phrase, doc_id, ts in [
                (mutation["from_phrase"], mutation["from_doc_id"], mutation["doc_a_timestamp"]),
                (mutation["to_phrase"], mutation["to_doc_id"], mutation["doc_b_timestamp"]),
            ]:
                if phrase in seen_phrases or ts is None:
                    continue
                seen_phrases.add(phrase)
                trail.append(
                    MutationEntry(
                        phrase=phrase,
                        first_doc_id=doc_id,
                        timestamp=ts,
                        source_type="",
                    )
                )

        return sorted(trail, key=lambda entry: entry.timestamp)

    def _chronological_pair(
        self,
        left_phrase: str,
        left_doc: Document,
        right_phrase: str,
        right_doc: Document,
    ) -> tuple[str, Document, str, Document]:
        left_ts = left_doc.published_at
        right_ts = right_doc.published_at
        if left_ts is None or right_ts is None:
            return left_phrase, left_doc, right_phrase, right_doc
        if left_ts <= right_ts:
            return left_phrase, left_doc, right_phrase, right_doc
        return right_phrase, right_doc, left_phrase, left_doc

    def _phrase_tokens(self, value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9']+", value.lower())
            if len(token) > 2
        }

    def _salient_terms(self, left_doc: Document, right_doc: Document) -> set[str]:
        values = [
            *left_doc.entities,
            *right_doc.entities,
            *left_doc.phrases,
            *right_doc.phrases,
        ]
        terms: set[str] = set()
        for value in values:
            for token in re.findall(r"[a-z0-9']+", value.lower()):
                if len(token) <= 3 or token in _STOPWORDS:
                    continue
                terms.add(token)
        return terms

    def _overlap_ratio(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    def _build_explanation(
        self,
        *,
        from_phrase: str,
        to_phrase: str,
        shared_tokens: list[str],
        source_shift: bool,
        source_type_shift: bool,
        time_delta_hours: float,
        mutation_type: str,
    ) -> str:
        overlap_text = (
            f"Shared terms: {', '.join(shared_tokens[:3])}."
            if shared_tokens
            else "Low direct token overlap; classified from phrase-shape similarity."
        )
        source_text = []
        if source_shift:
            source_text.append("the phrase moved across sources")
        if source_type_shift:
            source_text.append("it crossed source types")
        if not source_text:
            source_text.append("it remained within a similar source context")
        mutation_label = "phrase reuse" if mutation_type == "phrase_reuse" else "phrase mutation"
        return (
            f"Detected {mutation_label} from '{from_phrase}' to '{to_phrase}' "
            f"after {time_delta_hours:.1f} hours; {overlap_text} "
            f"Chronology suggests {source_text[0]}."
        )
