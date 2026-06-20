from __future__ import annotations

from models.document import Document
from models.investigation import (
    AnalystResult,
    CandidateClaim,
    CounterNarrativeResult,
    FinalReportClaim,
    FinalReportResult,
    FinalReportSections,
    InvestigationPlan,
    ReportCitation,
    RetrievalResult,
    TimelineResult,
)

_KEY_CLAIM_TYPE_PRIORITY = {
    "observed_fact": 0,
    "inference": 1,
    "uncertainty": 2,
    "limitation": 3,
    "recommendation": 4,
}


def build_final_report(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
    analyst: AnalystResult,
) -> FinalReportResult:
    docs_by_id = {doc.id: doc for doc in documents}
    key_claims = _select_key_claims(analyst.candidate_claims)
    report_claims = [_build_report_claim(claim, docs_by_id) for claim in key_claims]
    evidence_packet = _build_evidence_packet(report_claims)
    title = _report_title(plan)
    summary = _report_summary(analyst, timeline, counter_narratives, report_claims)
    sections = FinalReportSections(
        headline=title,
        executive_summary=analyst.draft_report_sections.executive_summary,
        observed_facts=analyst.draft_report_sections.observed_facts,
        reasonable_inferences=analyst.draft_report_sections.reasonable_inferences,
        timeline_summary=analyst.draft_report_sections.timeline_summary,
        counter_narrative_summary=analyst.draft_report_sections.counter_narrative_summary,
        limitations=_join_or_fallback(
            analyst.limitations,
            "No additional limitations were recorded beyond the analyst draft.",
        ),
        recommended_human_checks=_join_or_fallback(
            analyst.recommended_human_checks,
            "No additional human checks were recorded.",
        ),
    )
    confidence_score, confidence_label = _confidence_score(
        retrieval,
        timeline,
        counter_narratives,
        analyst,
        report_claims,
    )

    return FinalReportResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        report_title=title,
        report_summary=summary,
        sections=sections,
        key_claims=report_claims,
        evidence_packet=evidence_packet,
        limitations=analyst.limitations,
        recommended_human_checks=analyst.recommended_human_checks,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
    )


def _select_key_claims(claims: list[CandidateClaim]) -> list[CandidateClaim]:
    ranked = sorted(
        claims,
        key=lambda claim: (
            _KEY_CLAIM_TYPE_PRIORITY.get(claim.claim_type, 99),
            -claim.confidence_score,
            claim.id,
        ),
    )
    selected: list[CandidateClaim] = []
    for claim in ranked:
        if claim.claim_type in {"limitation", "recommendation"}:
            continue
        if claim.claim_type == "uncertainty" and any(
            existing.claim_type == "uncertainty" for existing in selected
        ):
            continue
        selected.append(claim)
        if len(selected) >= 5:
            break
    return selected


def _build_report_claim(
    claim: CandidateClaim,
    docs_by_id: dict[str, Document],
) -> FinalReportClaim:
    citations: list[ReportCitation] = []
    for doc_id in claim.supporting_document_ids[:3]:
        doc = docs_by_id.get(doc_id)
        if doc is None:
            continue
        citations.append(
            ReportCitation(
                document_id=doc.id,
                source_name=doc.source_name,
                source_type=doc.source_type,
                title=doc.title,
                url=doc.url,
                published_at=doc.published_at,
                snippet=_best_snippet(doc),
                relevance_note=_relevance_note(claim),
            )
        )

    return FinalReportClaim(
        claim_id=claim.id,
        claim_text=claim.claim_text,
        claim_type=claim.claim_type,
        confidence_score=claim.confidence_score,
        caveats=claim.caveats,
        citations=citations,
    )


def _build_evidence_packet(report_claims: list[FinalReportClaim]) -> list[ReportCitation]:
    packet: list[ReportCitation] = []
    seen: set[str] = set()
    for claim in report_claims:
        for citation in claim.citations:
            if citation.document_id in seen:
                continue
            seen.add(citation.document_id)
            packet.append(citation)
    return packet


def _report_title(plan: InvestigationPlan) -> str:
    if plan.canonical_phrase:
        return f"Investigation Report: {plan.canonical_phrase}"
    if plan.topic:
        return f"Investigation Report: {plan.topic}"
    return "Investigation Report"


def _report_summary(
    analyst: AnalystResult,
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
    report_claims: list[FinalReportClaim],
) -> str:
    parts = [analyst.draft_report_sections.executive_summary]
    if report_claims:
        parts.append(
            f"The final report surfaces {len(report_claims)} claim(s) with inline document support."
        )
    parts.append(
        f"The timeline contains {len(timeline.timeline_events)} dated event(s) used for chronology."
    )
    if counter_narratives.counter_narratives:
        parts.append(
            f"{len(counter_narratives.counter_narratives)} counter-frame cluster(s) were incorporated into the synthesis."
        )
    else:
        parts.append("No clear counter-frame was identified in the retrieved corpus.")
    return " ".join(parts)


def _confidence_score(
    retrieval: RetrievalResult,
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
    analyst: AnalystResult,
    report_claims: list[FinalReportClaim],
) -> tuple[float, str]:
    evidence_coverage = 0.0
    if report_claims:
        cited = sum(1 for claim in report_claims if claim.citations)
        evidence_coverage = cited / len(report_claims)

    score = (
        (analyst.confidence_score * 0.45)
        + (timeline.confidence_score * 0.2)
        + (counter_narratives.confidence_score * 0.1)
        + (_retrieval_confidence(retrieval.evidence_coverage_confidence) * 0.15)
        + (evidence_coverage * 0.1)
    )
    bounded = round(min(max(score, 0.0), 0.95), 3)
    if bounded >= 0.72:
        return bounded, "high"
    if bounded >= 0.46:
        return bounded, "medium"
    return bounded, "low"


def _retrieval_confidence(label: str) -> float:
    if label == "high":
        return 0.82
    if label == "medium":
        return 0.58
    return 0.32


def _best_snippet(doc: Document) -> str | None:
    if doc.snippet:
        return doc.snippet.strip()
    text = doc.text.strip()
    if not text:
        return None
    return text[:220]


def _relevance_note(claim: CandidateClaim) -> str:
    if claim.claim_type == "observed_fact":
        return "Directly supports an observed fact in the final report."
    if claim.claim_type == "inference":
        return "Provides chronology or context supporting an inference in the final report."
    if claim.claim_type == "uncertainty":
        return "Documents a boundary on what the retrieved evidence can establish."
    return "Included as supporting context for this report claim."


def _join_or_fallback(values: list[str], fallback: str) -> str:
    if not values:
        return fallback
    return " ".join(values)
