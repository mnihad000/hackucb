from __future__ import annotations

from datetime import datetime

from models.document import Document
from models.investigation import (
    AnalystResult,
    CandidateClaim,
    CounterNarrativeResult,
    DraftReportSections,
    InvestigationPlan,
    RetrievalResult,
    TimelineEvent,
    TimelineResult,
)

_COVERAGE_SCORES = {"low": 0.34, "medium": 0.58, "high": 0.8}
_NICHE_SOURCE_TYPES = {"forum", "blog", "local_news"}
_BROAD_SOURCE_TYPES = {"national_news", "commentary", "speech_transcript"}


def build_analyst_result(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
) -> AnalystResult:
    docs_by_id = {doc.id: doc for doc in documents}
    timeline_docs = [docs_by_id[event.document_id] for event in timeline.timeline_events if event.document_id in docs_by_id]
    first_doc = docs_by_id.get(timeline.first_observed_doc_id or "")
    broader_pickups = [event for event in timeline.timeline_events if event.event_type == "broader_pickup"]
    official_mentions = [event for event in timeline.timeline_events if event.event_type == "official_mention"]
    counter_events = [event for event in timeline.timeline_events if event.event_type == "counter_narrative_entry"]

    spread_pattern = _infer_spread_pattern(timeline.timeline_events)
    observed_facts_lines = _observed_fact_lines(
        first_doc,
        timeline,
        broader_pickups,
        official_mentions,
        counter_narratives,
        retrieval,
    )
    inference_lines = _inference_lines(spread_pattern, timeline.timeline_events, counter_narratives)
    uncertainty_lines = _uncertainty_lines(plan, timeline, counter_narratives)
    limitations = _merge_unique(
        timeline.limitations,
        counter_narratives.limitations,
    )
    recommended_human_checks = _recommended_human_checks(
        plan,
        first_doc,
        broader_pickups,
        official_mentions,
        counter_events,
    )
    candidate_claims = _candidate_claims(
        first_doc,
        timeline,
        counter_narratives,
        broader_pickups,
        official_mentions,
        spread_pattern,
        limitations,
        recommended_human_checks,
    )
    confidence_score, confidence_label = _confidence_score(
        retrieval,
        timeline,
        counter_narratives,
        candidate_claims,
    )

    sections = DraftReportSections(
        executive_summary=_executive_summary(
            plan,
            first_doc,
            broader_pickups,
            official_mentions,
            counter_narratives,
            spread_pattern,
        ),
        observed_facts=" ".join(observed_facts_lines),
        reasonable_inferences=" ".join(inference_lines),
        timeline_summary=timeline.timeline_summary,
        counter_narrative_summary=_counter_summary(counter_narratives),
        uncertainties=" ".join(uncertainty_lines),
    )

    return AnalystResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        draft_report_sections=sections,
        candidate_claims=candidate_claims,
        limitations=limitations,
        recommended_human_checks=recommended_human_checks,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
    )


def _executive_summary(
    plan: InvestigationPlan,
    first_doc: Document | None,
    broader_pickups: list[TimelineEvent],
    official_mentions: list[TimelineEvent],
    counter_narratives: CounterNarrativeResult,
    spread_pattern: str,
) -> str:
    parts: list[str] = []
    if first_doc and first_doc.published_at is not None:
        parts.append(
            f"In the retrieved dataset, the narrative was first observed via {first_doc.source_name} on {first_doc.published_at.date().isoformat()}."
        )
    elif first_doc:
        parts.append(f"In the retrieved dataset, the earliest identified document came from {first_doc.source_name}.")
    else:
        parts.append("The retrieved dataset does not establish a strong first-observed anchor.")

    if broader_pickups:
        parts.append("Later chronology shows movement into broader coverage beyond the earliest niche sources.")
    else:
        parts.append("The retrieved chronology does not clearly show a broader pickup moment.")

    if official_mentions:
        parts.append("The narrative also appears in an official or transcript-style source within the retrieved corpus.")

    if counter_narratives.counter_narratives:
        parts.append("A competing frame appears in the same investigation corpus and should be considered alongside the main narrative.")

    parts.append(
        f"The overall spread pattern is best described as {spread_pattern.replace('_', ' ')}, with cautious interpretation rather than origin or coordination claims."
    )
    return " ".join(parts)


def _observed_fact_lines(
    first_doc: Document | None,
    timeline: TimelineResult,
    broader_pickups: list[TimelineEvent],
    official_mentions: list[TimelineEvent],
    counter_narratives: CounterNarrativeResult,
    retrieval: RetrievalResult,
) -> list[str]:
    lines: list[str] = []
    if first_doc and first_doc.published_at is not None:
        lines.append(
            f"The first observed document in this dataset is '{first_doc.title}' from {first_doc.source_name} on {first_doc.published_at.date().isoformat()}."
        )
    elif first_doc:
        lines.append(
            f"The earliest anchored document in this dataset is '{first_doc.title}' from {first_doc.source_name}, but publication timing is limited."
        )

    source_type_count = len(retrieval.coverage_summary.source_type_distribution)
    dated_count = len(timeline.timeline_events)
    lines.append(
        f"The chronology includes {dated_count} dated document(s) across {source_type_count} observed source type(s)."
    )

    if broader_pickups:
        broader_sources = sorted({event.source_name for event in broader_pickups})
        lines.append(
            f"At least one broader pickup event appears in the timeline, including {', '.join(broader_sources[:3])}."
        )

    if official_mentions:
        lines.append("The timeline includes an official mention or transcript-style event.")

    if counter_narratives.counter_narratives:
        lines.append(
            f"The investigation identified {len(counter_narratives.counter_narratives)} counter-frame cluster(s) in the retrieved corpus."
        )
    else:
        lines.append("No clear counter-frame was identified in the retrieved corpus.")

    return lines


def _inference_lines(
    spread_pattern: str,
    timeline_events: list[TimelineEvent],
    counter_narratives: CounterNarrativeResult,
) -> list[str]:
    lines: list[str] = []
    if spread_pattern == "reactive_amplification":
        lines.append(
            "The event sequence is consistent with reactive amplification from earlier niche or local coverage into broader attention."
        )
    elif spread_pattern == "broad_but_shallow":
        lines.append(
            "The narrative appears across multiple source types, but the chronology is still too thin to support stronger spread conclusions."
        )
    else:
        lines.append(
            "The retrieved evidence supports only a cautious spread interpretation rather than a strong directional narrative."
        )

    if counter_narratives.counter_narratives:
        lines.append(
            "The presence of a counter-frame suggests the issue was contested in the observed corpus rather than repeated in a single unopposed framing."
        )
    else:
        lines.append(
            "Because no clear counter-frame was detected, the retrieved corpus may underrepresent competing interpretations."
        )
    return lines


def _counter_summary(counter_narratives: CounterNarrativeResult) -> str:
    if not counter_narratives.counter_narratives:
        return "No clear counter-narrative was identified in the retrieved evidence packet."
    summaries = [counter.summary for counter in counter_narratives.counter_narratives[:2]]
    return " ".join(summaries)


def _uncertainty_lines(
    plan: InvestigationPlan,
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
) -> list[str]:
    lines = list(plan.uncertainty_requirements)
    lines.extend(timeline.limitations[:2])
    lines.extend(counter_narratives.limitations[:2])
    if not lines:
        lines.append("The retrieved evidence packet may omit earlier, deleted, or off-dataset sources.")
    return _merge_unique(lines)


def _recommended_human_checks(
    plan: InvestigationPlan,
    first_doc: Document | None,
    broader_pickups: list[TimelineEvent],
    official_mentions: list[TimelineEvent],
    counter_events: list[TimelineEvent],
) -> list[str]:
    checks = [
        "Verify whether earlier appearances exist outside the retrieved dataset or in deleted/archived sources.",
    ]
    if first_doc is not None:
        checks.append(f"Verify the publication timestamp and provenance of {first_doc.source_name}.")
    if broader_pickups:
        checks.append("Check whether broader pickup sources cited the same statement, press release, or earlier article.")
    if official_mentions:
        checks.append("Compare the official mention against the earlier narrative wording to distinguish repetition from independent framing.")
    if counter_events:
        checks.append("Inspect whether the counter-frame materially disputes the same claim or reframes the issue around different evidence.")
    if plan.intent == "origin":
        checks.append("Treat first observed in the dataset as a retrieval anchor, not proof of true origin.")
    return _merge_unique(checks)


def _candidate_claims(
    first_doc: Document | None,
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
    broader_pickups: list[TimelineEvent],
    official_mentions: list[TimelineEvent],
    spread_pattern: str,
    limitations: list[str],
    recommended_human_checks: list[str],
) -> list[CandidateClaim]:
    claims: list[CandidateClaim] = []
    if first_doc is not None:
        claims.append(
            _claim(
                claim_id="claim_first_observed",
                claim_text=_first_observed_claim(first_doc),
                claim_type="observed_fact",
                document_ids=[first_doc.id],
                confidence_score=0.92 if first_doc.published_at is not None else 0.68,
                caveats=["First observed refers only to this retrieved dataset."],
            )
        )

    timeline_doc_ids = [event.document_id for event in timeline.timeline_events]
    claims.append(
        _claim(
            claim_id="claim_timeline_coverage",
            claim_text=f"The investigation chronology includes {len(timeline.timeline_events)} dated document(s).",
            claim_type="observed_fact",
            document_ids=timeline_doc_ids,
            confidence_score=min(0.88, timeline.confidence_score + 0.12),
            caveats=[],
        )
    )

    if broader_pickups:
        claims.append(
            _claim(
                claim_id="claim_broader_pickup",
                claim_text="The narrative later appears in broader coverage after earlier niche or local attention.",
                claim_type="observed_fact",
                document_ids=[event.document_id for event in broader_pickups[:3]],
                confidence_score=0.79,
                caveats=["This describes sequence in the retrieved dataset, not causal influence."],
            )
        )

    if official_mentions:
        claims.append(
            _claim(
                claim_id="claim_official_mention",
                claim_text="An official or transcript-style mention appears in the retrieved chronology.",
                claim_type="observed_fact",
                document_ids=[event.document_id for event in official_mentions[:2]],
                confidence_score=0.81,
                caveats=[],
            )
        )

    if counter_narratives.counter_narratives:
        support_ids = counter_narratives.counter_narratives[0].supporting_document_ids
        claims.append(
            _claim(
                claim_id="claim_counter_frame_present",
                claim_text="A competing counter-frame appears in the retrieved investigation corpus.",
                claim_type="observed_fact",
                document_ids=support_ids,
                confidence_score=min(0.86, counter_narratives.confidence_score + 0.1),
                caveats=[],
            )
        )

    claims.append(
        _claim(
            claim_id="claim_spread_inference",
            claim_text=f"The overall spread pattern is most consistent with {spread_pattern.replace('_', ' ')}.",
            claim_type="inference",
            document_ids=timeline_doc_ids[:4],
            confidence_score=min(0.74, timeline.confidence_score),
            caveats=[
                "This is an interpretive synthesis, not a claim about coordination or true origin.",
            ],
        )
    )

    for index, limitation in enumerate(limitations[:2], start=1):
        claims.append(
            _claim(
                claim_id=f"claim_limitation_{index}",
                claim_text=limitation,
                claim_type="limitation",
                document_ids=[],
                confidence_score=0.95,
                caveats=[],
            )
        )

    for index, check in enumerate(recommended_human_checks[:2], start=1):
        claims.append(
            _claim(
                claim_id=f"claim_recommendation_{index}",
                claim_text=check,
                claim_type="recommendation",
                document_ids=[],
                confidence_score=0.9,
                caveats=[],
            )
        )

    claims.append(
        _claim(
            claim_id="claim_uncertainty_dataset_scope",
            claim_text="Earlier sources may exist outside the retrieved dataset.",
            claim_type="uncertainty",
            document_ids=[],
            confidence_score=0.98,
            caveats=[],
        )
    )

    return claims


def _first_observed_claim(first_doc: Document) -> str:
    if first_doc.published_at is not None:
        return (
            f"In the retrieved dataset, the narrative is first observed in '{first_doc.title}' "
            f"from {first_doc.source_name} on {first_doc.published_at.date().isoformat()}."
        )
    return (
        f"In the retrieved dataset, the earliest anchored document is '{first_doc.title}' from {first_doc.source_name}."
    )


def _claim(
    claim_id: str,
    claim_text: str,
    claim_type: str,
    document_ids: list[str],
    confidence_score: float,
    caveats: list[str],
) -> CandidateClaim:
    return CandidateClaim(
        id=claim_id,
        claim_text=claim_text,
        claim_type=claim_type,
        supporting_document_ids=document_ids,
        supporting_evidence_span_ids=[f"span:{doc_id}:snippet" for doc_id in document_ids],
        confidence_score=round(min(max(confidence_score, 0.0), 1.0), 3),
        caveats=caveats,
    )


def _infer_spread_pattern(events: list[TimelineEvent]) -> str:
    if not events:
        return "insufficient_evidence"

    source_types = [event.source_type for event in events]
    has_niche = any(source_type in _NICHE_SOURCE_TYPES for source_type in source_types)
    has_broad = any(source_type in _BROAD_SOURCE_TYPES for source_type in source_types)
    has_broader_pickup = any(event.event_type == "broader_pickup" for event in events)
    has_official = any(event.event_type == "official_mention" for event in events)

    if has_niche and has_broad and has_broader_pickup:
        return "reactive_amplification"
    if has_official and has_broad:
        return "official_and_media_attention"
    if len(set(source_types)) >= 2:
        return "broad_but_shallow"
    return "insufficient_evidence"


def _confidence_score(
    retrieval: RetrievalResult,
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
    candidate_claims: list[CandidateClaim],
) -> tuple[float, str]:
    retrieval_score = _COVERAGE_SCORES.get(retrieval.evidence_coverage_confidence, 0.34)
    base = (retrieval_score * 0.35) + (timeline.confidence_score * 0.4) + (counter_narratives.confidence_score * 0.15)
    factual_density = sum(1 for claim in candidate_claims if claim.claim_type == "observed_fact")
    base += min(0.1, factual_density * 0.02)
    score = round(min(base, 0.93), 3)
    if score >= 0.72:
        return score, "high"
    if score >= 0.46:
        return score, "medium"
    return score, "low"


def _merge_unique(*lists: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for values in lists:
        for value in values:
            normalized = value.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(normalized)
    return output
