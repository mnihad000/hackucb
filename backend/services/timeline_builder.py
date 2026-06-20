from __future__ import annotations

from datetime import timedelta

from models.document import Document
from models.investigation import InvestigationPlan, RetrievalResult, TimelineEvent, TimelineResult

_NICHE_SOURCE_TYPES = {"forum", "blog", "local_news"}
_BROADER_SOURCE_TYPES = {"national_news", "commentary"}
_RESURFACING_GAP = timedelta(hours=72)


def build_timeline(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
) -> TimelineResult:
    dated_documents = sorted(
        (doc for doc in documents if doc.published_at is not None),
        key=lambda doc: doc.published_at,
    )
    undated_count = len(documents) - len(dated_documents)
    first_doc = dated_documents[0] if dated_documents else None
    timeline_events: list[TimelineEvent] = []
    broader_pickup_assigned = False
    counter_candidates = _counter_candidate_ids(retrieval, documents)
    main_ids = set(retrieval.main_narrative_document_ids)
    context_ids = set(retrieval.context_document_ids)
    phrase = (plan.canonical_phrase or "").strip().lower()

    for index, doc in enumerate(dated_documents):
        previous = dated_documents[index - 1] if index > 0 else None
        source_transition = previous is not None and previous.source_name != doc.source_name
        event_type = _classify_event_type(
            index=index,
            document=doc,
            previous=previous,
            first_document=first_doc,
            dated_documents=dated_documents,
            broader_pickup_assigned=broader_pickup_assigned,
            counter_candidate_ids=counter_candidates,
        )
        if event_type == "broader_pickup":
            broader_pickup_assigned = True
        narrative_side = _classify_narrative_side(doc, phrase, main_ids, counter_candidates, context_ids)
        importance_score = _importance_score(doc, event_type, phrase, source_transition)
        explanation = _build_explanation(doc, event_type, narrative_side)
        timeline_events.append(
            TimelineEvent(
                id=f"timeline_{index + 1}_{doc.id}",
                document_id=doc.id,
                timestamp=doc.published_at,
                source_name=doc.source_name,
                source_type=doc.source_type,
                title=doc.title,
                url=doc.url,
                snippet=doc.snippet,
                event_type=event_type,
                narrative_side=narrative_side,
                importance_score=importance_score,
                explanation=explanation,
            )
        )

    limitations = _build_limitations(documents, dated_documents, undated_count)
    summary = _build_summary(timeline_events, first_doc)
    confidence_label, confidence_score = _confidence(documents, dated_documents)

    return TimelineResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        timeline_events=timeline_events,
        first_observed_doc_id=first_doc.id if first_doc else None,
        timeline_summary=summary,
        limitations=limitations,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
    )


def _classify_event_type(
    *,
    index: int,
    document: Document,
    previous: Document | None,
    first_document: Document | None,
    dated_documents: list[Document],
    broader_pickup_assigned: bool,
    counter_candidate_ids: set[str],
) -> str:
    if index == 0:
        return "first_observed"
    if document.source_type == "speech_transcript":
        return "official_mention"
    if document.id in counter_candidate_ids:
        return "counter_narrative_entry"
    if previous and (document.published_at - previous.published_at) >= _RESURFACING_GAP:
        return "resurfacing"
    if not broader_pickup_assigned and _is_broader_pickup(index, document, dated_documents):
        return "broader_pickup"
    if first_document and index <= 3 and (document.published_at - first_document.published_at) <= timedelta(hours=24):
        if previous and previous.source_name != document.source_name:
            return "early_amplification"
    return "other"


def _is_broader_pickup(index: int, document: Document, dated_documents: list[Document]) -> bool:
    if document.source_type not in _BROADER_SOURCE_TYPES:
        return False
    prior_types = {doc.source_type for doc in dated_documents[:index]}
    return bool(prior_types & _NICHE_SOURCE_TYPES)


def _classify_narrative_side(
    document: Document,
    canonical_phrase: str,
    main_ids: set[str],
    counter_ids: set[str],
    context_ids: set[str],
) -> str:
    if document.id in main_ids:
        return "main"
    if document.id in counter_ids:
        return "counter"
    if document.id in context_ids:
        return "related"
    haystack = " ".join(filter(None, [document.title, document.snippet or "", document.text])).lower()
    if canonical_phrase and canonical_phrase in haystack:
        return "main"
    return "unknown"


def _importance_score(
    document: Document,
    event_type: str,
    canonical_phrase: str,
    source_transition: bool,
) -> float:
    score = 0.0
    if event_type == "first_observed":
        score += 0.35
    if event_type == "official_mention":
        score += 0.20
    if event_type == "broader_pickup":
        score += 0.15
    if event_type == "counter_narrative_entry":
        score += 0.15
    haystack = " ".join(filter(None, [document.title, document.snippet or "", document.text])).lower()
    if canonical_phrase and canonical_phrase in haystack:
        score += 0.10
    if source_transition:
        score += 0.10
    retrieval_score = float((document.metadata or {}).get("retrieval_score", 0.0) or 0.0)
    if retrieval_score >= 5.0:
        score += 0.10
    elif retrieval_score >= 3.0:
        score += 0.05
    return round(min(score, 1.0), 3)


def _build_explanation(document: Document, event_type: str, narrative_side: str) -> str:
    if event_type == "first_observed":
        return f"Earliest dated document in the retrieved corpus from {document.source_name}."
    if event_type == "official_mention":
        return "Official mention based on speech transcript source classification."
    if event_type == "counter_narrative_entry":
        return "Counter-narrative entry based on retriever counter-framing classification."
    if event_type == "resurfacing":
        return "Narrative resurfacing after a gap of at least 72 hours in the dated corpus."
    if event_type == "broader_pickup":
        return "Broader pickup after earlier coverage in forum, blog, or local news sources."
    if event_type == "early_amplification":
        return "Early amplification during the first 24 hours with a source transition."
    if narrative_side == "related":
        return "Related contextual coverage included in the retrieved investigation corpus."
    return "Chronology event derived from the dated investigation corpus."


def _build_summary(timeline_events: list[TimelineEvent], first_document: Document | None) -> str:
    if first_document is None:
        return "No strict chronology could be built because none of the retrieved documents had usable published dates."

    dated_count = len(timeline_events)
    source_type_count = len({event.source_type for event in timeline_events})
    has_counter = any(event.event_type == "counter_narrative_entry" for event in timeline_events)
    has_official = any(event.event_type == "official_mention" for event in timeline_events)
    crossed_types = source_type_count >= 2
    first_date = first_document.published_at.date().isoformat()
    parts = [
        f"The narrative was first observed in our dataset on {first_date} via {first_document.source_name}.",
        f"{dated_count} dated documents were included in the chronology.",
        "Coverage crossed multiple source types." if crossed_types else "Coverage stayed within a narrow set of source types.",
        "A counter-narrative entry appears in the dated corpus." if has_counter else "No counter-narrative entry appears in the dated corpus.",
        "An official mention appears in the dated corpus." if has_official else "No official mention appears in the dated corpus.",
    ]
    return " ".join(parts)


def _build_limitations(
    documents: list[Document],
    dated_documents: list[Document],
    undated_count: int,
) -> list[str]:
    limitations = [
        "First observed refers only to this retrieved investigation corpus, not true origin.",
    ]
    if undated_count > 0:
        limitations.append(
            "Some retrieved documents were excluded from strict chronology because published dates were unavailable."
        )
    if len(dated_documents) < 3:
        limitations.append(
            "Timeline confidence is limited because only a small number of dated documents were retrieved."
        )
    unique_sources = len({doc.source_name for doc in dated_documents})
    if dated_documents and unique_sources <= max(2, len(dated_documents) // 3):
        limitations.append("Chronology may overrepresent a narrow slice of sources.")
    if not documents:
        limitations.append("No retrieved documents were available to build a chronology.")
    return limitations


def _confidence(documents: list[Document], dated_documents: list[Document]) -> tuple[str, float]:
    if not documents:
        return "low", 0.15

    unique_sources = len({doc.source_name for doc in dated_documents})
    source_types = len({doc.source_type for doc in dated_documents})
    timestamp_fraction = len(dated_documents) / len(documents)
    cross_source_transition = any(
        left.source_name != right.source_name
        for left, right in zip(dated_documents, dated_documents[1:])
    )

    if len(dated_documents) >= 6 and unique_sources >= 4 and source_types >= 2:
        score = 0.75
        score += min(0.1, max(0.0, timestamp_fraction - 0.5) * 0.2)
        score += 0.05 if cross_source_transition else 0.0
        score += min(0.05, max(0, unique_sources - 4) * 0.02)
        return "high", round(min(score, 0.95), 3)

    if len(dated_documents) >= 3 and unique_sources >= 2:
        score = 0.45
        score += min(0.12, max(0.0, timestamp_fraction - 0.3) * 0.2)
        score += 0.07 if cross_source_transition else 0.0
        score += min(0.1, max(0, source_types - 1) * 0.05)
        return "medium", round(min(score, 0.74), 3)

    score = 0.15
    score += min(0.14, timestamp_fraction * 0.14)
    score += min(0.1, max(0, len(dated_documents) - 1) * 0.05)
    score += 0.05 if cross_source_transition else 0.0
    return "low", round(min(score, 0.44), 3)


def _counter_candidate_ids(retrieval: RetrievalResult, documents: list[Document]) -> set[str]:
    if retrieval.counter_narrative_candidate_ids:
        return set(retrieval.counter_narrative_candidate_ids)
    return {
        doc.id
        for doc in documents
        if "counter_signal" in set((doc.metadata or {}).get("retrieval_reason_tags", []))
    }
