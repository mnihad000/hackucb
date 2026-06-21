from __future__ import annotations

from models.document import Document
from models.investigation import (
    AnalystResult,
    GapAnalysisResult,
    GapAnalysisScores,
    GapItem,
    InvestigationPlan,
    ProvenanceTraceResult,
    RetrievalResult,
    SourceDiversityResult,
    TimelineResult,
    CounterNarrativeResult,
)


def build_gap_analysis(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
    source_diversity: SourceDiversityResult,
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
    analyst: AnalystResult,
    provenance: ProvenanceTraceResult,
    *,
    pass_number: int,
) -> GapAnalysisResult:
    total_docs = max(1, len(documents))
    chronology_coverage = min(1.0, len(timeline.timeline_events) / max(3, total_docs / 2))
    source_diversity_coverage = min(1.0, len(source_diversity.source_type_distribution) / 4)
    contradiction_coverage = 1.0 if counter_narratives.counter_narratives else 0.25
    primary_source_coverage = min(
        1.0,
        sum(1 for doc in documents if doc.source_name.endswith(".gov") or doc.source_type == "speech_transcript") / 2,
    )
    claim_support_density = min(
        1.0,
        sum(1 for claim in analyst.candidate_claims if claim.supporting_document_ids) / max(1, len(analyst.candidate_claims)),
    )
    duplication_contamination = min(1.0, len(retrieval.possible_duplicate_pairs) / max(1, total_docs / 2))
    evergreen_contamination = _evergreen_contamination(documents)
    origin_confidence = provenance.confidence_score

    scores = GapAnalysisScores(
        chronology_coverage=round(chronology_coverage, 3),
        source_diversity_coverage=round(source_diversity_coverage, 3),
        contradiction_coverage=round(contradiction_coverage, 3),
        primary_source_coverage=round(primary_source_coverage, 3),
        claim_support_density=round(claim_support_density, 3),
        duplication_contamination=round(duplication_contamination, 3),
        evergreen_contamination=round(evergreen_contamination, 3),
        origin_confidence=round(origin_confidence, 3),
    )

    gaps: list[GapItem] = []
    if chronology_coverage < 0.6:
        gaps.append(
            GapItem(
                gap_id="gap_chronology_coverage",
                gap_type="chronology",
                severity="high",
                summary="Chronology coverage is too thin for a confident spread/origin sequence.",
                recommended_retrieval_lane="provenance" if plan.intent == "origin" else "discovery",
                follow_up_queries=[f"{plan.canonical_phrase or plan.topic} earliest mention"],
            )
        )
    if contradiction_coverage < 0.6:
        gaps.append(
            GapItem(
                gap_id="gap_contradiction_coverage",
                gap_type="contradiction",
                severity="medium",
                summary="Counter-evidence coverage is weak or absent.",
                recommended_retrieval_lane="contradiction",
                follow_up_queries=[f"{plan.canonical_phrase or plan.topic} rebuttal", f"{plan.canonical_phrase or plan.topic} fact check"],
            )
        )
    if primary_source_coverage < 0.55:
        gaps.append(
            GapItem(
                gap_id="gap_primary_source",
                gap_type="primary_source",
                severity="high",
                summary="Primary or official source coverage is incomplete.",
                recommended_retrieval_lane="official",
                recommended_source_classes=["official_statement", "speech_transcript"],
                follow_up_queries=[f"{plan.canonical_phrase or plan.topic} official statement"],
            )
        )
    if duplication_contamination > 0.35:
        gaps.append(
            GapItem(
                gap_id="gap_duplication",
                gap_type="duplication",
                severity="high",
                summary="Apparent plurality may be inflated by duplicate or syndicated coverage.",
                recommended_retrieval_lane="corroboration",
                follow_up_queries=[f"{plan.canonical_phrase or plan.topic} independent coverage"],
            )
        )
    if plan.intent == "origin" and provenance.earliest_anchor_document_id is None:
        gaps.append(
            GapItem(
                gap_id="gap_origin_anchor",
                gap_type="origin_confidence",
                severity="critical",
                summary="The retrieved corpus does not yet contain a reliable earliest anchor.",
                recommended_retrieval_lane="provenance",
                follow_up_queries=[f"{plan.canonical_phrase or plan.topic} before"],
            )
        )
    if provenance.official_anchor_document_id is None and plan.intent in {"origin", "spread"}:
        gaps.append(
            GapItem(
                gap_id="gap_official_anchor",
                gap_type="provenance",
                severity="medium",
                summary="No official anchor was found to test whether repetition traces back to a primary source.",
                recommended_retrieval_lane="official",
                recommended_source_classes=["official_statement"],
                follow_up_queries=[f"{plan.canonical_phrase or plan.topic} press release"],
            )
        )

    weak_claim_ids = [
        claim.id for claim in analyst.candidate_claims if claim.claim_type == "inference" and claim.confidence_score < 0.72
    ]
    missing_source_classes = _missing_source_classes(plan.must_have_source_classes, source_diversity.source_type_distribution)
    retry_priority = [gap.gap_id for gap in sorted(gaps, key=lambda item: _severity_rank(item.severity), reverse=True)]
    confidence = _confidence(scores, gaps)

    return GapAnalysisResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        pass_number=pass_number,
        scores=scores,
        missing_evidence=gaps,
        weak_claim_ids=weak_claim_ids,
        missing_source_classes=missing_source_classes,
        retry_priority=retry_priority,
        confidence_score=confidence,
    )


def _missing_source_classes(required: list[str], observed: dict[str, int]) -> list[str]:
    return [source_class for source_class in required if observed.get(source_class, 0) == 0]


def _severity_rank(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity, 0)


def _evergreen_contamination(documents: list[Document]) -> float:
    evergreen_hits = sum(
        1
        for doc in documents
        if any(term in f"{doc.title} {doc.snippet or ''}".lower() for term in ("explainer", "what is", "guide"))
    )
    return round(min(1.0, evergreen_hits / max(1, len(documents))), 3)


def _confidence(scores: GapAnalysisScores, gaps: list[GapItem]) -> float:
    avg = (
        scores.chronology_coverage
        + scores.source_diversity_coverage
        + scores.contradiction_coverage
        + scores.primary_source_coverage
        + scores.claim_support_density
        + scores.origin_confidence
    ) / 6
    penalty = min(0.35, len(gaps) * 0.05)
    return round(max(0.0, min(0.95, avg - penalty)), 3)
