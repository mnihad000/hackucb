from __future__ import annotations

from collections import Counter

from models.document import Document
from models.investigation import (
    CounterNarrative,
    CounterNarrativeResult,
    InvestigationPlan,
    RetrievalResult,
)

_COUNTER_TERMS = {
    "however",
    "but",
    "despite",
    "critics",
    "supporters",
    "opponents",
    "denies",
    "refutes",
    "debunks",
    "fact check",
    "counter",
    "rebuttal",
    "argue",
    "instead",
    "rejects",
    "disputes",
}
_CORRECTIVE_TERMS = {"debunks", "fact check", "refutes", "corrects", "disputes", "rejects"}
_REFRAMING_TERMS = {"instead", "however", "argue", "supporters", "investment", "savings", "benefits"}
_GENERIC_PHRASE_WORDS = {
    "hidden",
    "energy",
    "tax",
    "narrative",
    "claim",
    "story",
    "policy",
    "debate",
    "issue",
    "plan",
}


def build_counter_narratives(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
) -> CounterNarrativeResult:
    docs_by_id = {doc.id: doc for doc in documents}
    candidate_docs = [
        docs_by_id[doc_id]
        for doc_id in retrieval.counter_narrative_candidate_ids
        if doc_id in docs_by_id
    ]

    if not candidate_docs:
        return CounterNarrativeResult(
            investigation_id=investigation_id,
            plan_snapshot=plan,
            counter_narratives=[],
            notes=["No clear counter-narrative candidates were identified in the retrieved corpus."],
            limitations=[
                "Counter-narrative detection depends on retrieved coverage and may miss weak or late-arriving opposing frames."
            ],
            confidence_score=0.22,
            confidence_label="low",
        )

    grouped = _group_candidates(candidate_docs, plan)
    counter_narratives = [_build_counter_narrative(index, group, plan) for index, group in enumerate(grouped, start=1)]

    unique_sources = len({doc.source_name for doc in candidate_docs})
    dated_docs = sum(1 for doc in candidate_docs if doc.published_at is not None)
    limitations = [
        "Counter-narrative identification is based on retrieved evidence and may miss off-dataset opposition.",
    ]
    if unique_sources <= 1:
        limitations.append("Counter-frame evidence comes from a narrow slice of sources.")
    if dated_docs == 0:
        limitations.append("Counter-frame timing confidence is limited because retrieved opposing documents were undated.")

    notes = [
        f"Detected {len(counter_narratives)} counter-frame cluster(s) across {unique_sources} source(s).",
    ]
    confidence_score, confidence_label = _confidence(candidate_docs, counter_narratives)

    return CounterNarrativeResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        counter_narratives=counter_narratives,
        notes=notes,
        limitations=limitations,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
    )


def _group_candidates(documents: list[Document], plan: InvestigationPlan) -> list[list[Document]]:
    grouped: dict[str, list[Document]] = {}
    for doc in documents:
        key = _group_key(doc, plan)
        grouped.setdefault(key, []).append(doc)
    return list(grouped.values())


def _group_key(document: Document, plan: InvestigationPlan) -> str:
    phrases = [
        phrase.lower()
        for phrase in document.phrases
        if _is_counter_phrase(phrase, plan.canonical_phrase)
    ]
    if phrases:
        return phrases[0]
    title_words = [word.lower() for word in document.title.split() if len(word) > 4]
    for word in title_words:
        if word not in _GENERIC_PHRASE_WORDS:
            return word
    return "counter_frame"


def _build_counter_narrative(index: int, documents: list[Document], plan: InvestigationPlan) -> CounterNarrative:
    ordered = sorted(
        documents,
        key=lambda doc: doc.published_at.isoformat() if doc.published_at is not None else "9999-99-99",
    )
    first_doc = ordered[0] if ordered else None
    related_phrases = _collect_related_phrases(documents, plan.canonical_phrase)
    canonical_phrase = related_phrases[0] if related_phrases else None
    relationship = _relationship(documents)
    title = _title_for_counter_frame(canonical_phrase, relationship, plan)
    summary = _summary_for_counter_frame(documents, canonical_phrase, relationship, plan)
    confidence_score = _counter_confidence(documents)

    return CounterNarrative(
        id=f"counter_{index}",
        title=title,
        summary=summary,
        canonical_phrase=canonical_phrase,
        related_phrases=related_phrases,
        supporting_document_ids=[doc.id for doc in ordered],
        first_observed_doc_id=first_doc.id if first_doc else None,
        relationship_to_main_narrative=relationship,
        confidence_score=confidence_score,
    )


def _collect_related_phrases(documents: list[Document], main_phrase: str | None) -> list[str]:
    phrases: list[str] = []
    main_phrase_lower = (main_phrase or "").lower()
    for doc in documents:
        for phrase in doc.phrases:
            normalized = phrase.strip()
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered == main_phrase_lower:
                continue
            if not _is_counter_phrase(normalized, main_phrase):
                continue
            if lowered not in {existing.lower() for existing in phrases}:
                phrases.append(normalized)
    return phrases[:6]


def _is_counter_phrase(phrase: str, main_phrase: str | None) -> bool:
    lowered = phrase.lower().strip()
    if not lowered:
        return False
    if main_phrase and lowered == main_phrase.lower().strip():
        return False
    words = [word for word in lowered.replace("-", " ").split() if len(word) > 2]
    if not words:
        return False
    if all(word in _GENERIC_PHRASE_WORDS for word in words):
        return False
    return True


def _relationship(documents: list[Document]) -> str:
    haystacks = [
        " ".join(filter(None, [doc.title, doc.snippet or "", doc.text])).lower()
        for doc in documents
    ]
    corrective_hits = sum(any(term in haystack for term in _CORRECTIVE_TERMS) for haystack in haystacks)
    reframing_hits = sum(any(term in haystack for term in _REFRAMING_TERMS) for haystack in haystacks)
    if corrective_hits >= max(1, len(documents) // 2):
        return "corrective"
    if reframing_hits >= max(1, len(documents) // 2):
        return "reframing"
    return "opposing"


def _title_for_counter_frame(
    canonical_phrase: str | None,
    relationship: str,
    plan: InvestigationPlan,
) -> str:
    phrase = canonical_phrase or f"response to {plan.canonical_phrase or plan.topic}"
    suffix = {
        "corrective": "Corrective Frame",
        "reframing": "Alternative Frame",
        "opposing": "Counter-Narrative",
    }[relationship]
    return f"{phrase.title()} {suffix}"


def _summary_for_counter_frame(
    documents: list[Document],
    canonical_phrase: str | None,
    relationship: str,
    plan: InvestigationPlan,
) -> str:
    phrase_text = canonical_phrase or "an alternative framing"
    source_count = len({doc.source_name for doc in documents})
    relationship_text = {
        "corrective": "directly challenges or fact-checks",
        "reframing": "reframes",
        "opposing": "pushes back against",
    }[relationship]
    return (
        f"This frame {relationship_text} the main narrative around {plan.canonical_phrase or plan.topic} "
        f"and clusters around '{phrase_text}'. It appears across {source_count} source(s) in the retrieved dataset."
    )


def _counter_confidence(documents: list[Document]) -> float:
    unique_sources = len({doc.source_name for doc in documents})
    dated_docs = sum(1 for doc in documents if doc.published_at is not None)
    score = 0.28
    score += min(0.22, len(documents) * 0.08)
    score += min(0.2, unique_sources * 0.06)
    score += min(0.15, dated_docs * 0.05)
    return round(min(score, 0.9), 3)


def _confidence(
    candidate_docs: list[Document],
    counter_narratives: list[CounterNarrative],
) -> tuple[float, str]:
    unique_sources = len({doc.source_name for doc in candidate_docs})
    dated_docs = sum(1 for doc in candidate_docs if doc.published_at is not None)
    score = 0.25
    score += min(0.2, len(candidate_docs) * 0.05)
    score += min(0.18, unique_sources * 0.05)
    score += min(0.12, len(counter_narratives) * 0.06)
    score += min(0.12, dated_docs * 0.03)
    score = round(min(score, 0.88), 3)

    if score >= 0.67:
        return score, "high"
    if score >= 0.42:
        return score, "medium"
    return score, "low"
