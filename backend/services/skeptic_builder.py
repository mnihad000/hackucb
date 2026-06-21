from __future__ import annotations

from models.investigation import (
    AnalystResult,
    GapAnalysisResult,
    InvestigationPlan,
    ProvenanceTraceResult,
    SkepticClaimReview,
    SkepticReviewResult,
    StopCondition,
)


def build_skeptic_review(
    investigation_id: str,
    plan: InvestigationPlan,
    analyst: AnalystResult,
    gaps: GapAnalysisResult,
    provenance: ProvenanceTraceResult,
    *,
    pass_number: int,
    max_passes: int,
) -> SkepticReviewResult:
    claim_reviews: list[SkepticClaimReview] = []
    gap_lookup = {gap.gap_id: gap for gap in gaps.missing_evidence}

    for claim in analyst.candidate_claims:
        if claim.claim_type == "inference":
            related_gap_ids = [gap.gap_id for gap in gaps.missing_evidence if gap.gap_type in {"chronology", "duplication", "origin_confidence", "provenance"}]
            if related_gap_ids:
                softened = f"The retrieved evidence suggests that {claim.claim_text[0].lower() + claim.claim_text[1:]}"
                claim_reviews.append(
                    SkepticClaimReview(
                        claim_id=claim.id,
                        claim_text=claim.claim_text,
                        decision="pass_with_softening",
                        reason="Inference is directionally useful but constrained by open evidence gaps.",
                        softened_text=softened,
                        related_gap_ids=related_gap_ids,
                    )
                )
                continue
        claim_reviews.append(
            SkepticClaimReview(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                decision="pass",
                reason="No high-risk overclaim detected for this claim at current evidence strength.",
                related_gap_ids=[],
            )
        )

    critical_or_high_gaps = [gap for gap in gaps.missing_evidence if gap.severity in {"critical", "high"} and gap.status == "open"]
    retry_instructions = [query for gap in critical_or_high_gaps for query in gap.follow_up_queries]
    overall_decision = "pass"
    reason = "Evidence packet cleared skeptic review."
    if critical_or_high_gaps and pass_number < max_passes:
        overall_decision = "retry_required"
        reason = "Addressable high-severity evidence gaps remain and justify a targeted retry pass."
    elif critical_or_high_gaps:
        overall_decision = "pass_with_softening"
        reason = "Evidence gaps remain after the retry budget; final language must stay explicitly cautious."
    elif any(review.decision == "pass_with_softening" for review in claim_reviews):
        overall_decision = "pass_with_softening"
        reason = "Claims can proceed, but only with softened language and preserved uncertainty."

    stop_condition_status = _evaluate_stop_conditions(plan.stop_conditions, gaps, provenance)
    return SkepticReviewResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        pass_number=pass_number,
        overall_decision=overall_decision,
        reason=reason,
        claim_reviews=claim_reviews,
        retry_instructions=retry_instructions,
        stop_condition_status=stop_condition_status,
    )


def _evaluate_stop_conditions(
    stop_conditions: list[StopCondition],
    gaps: GapAnalysisResult,
    provenance: ProvenanceTraceResult,
) -> list[StopCondition]:
    open_gap_types = {gap.gap_type for gap in gaps.missing_evidence if gap.status == "open"}
    output: list[StopCondition] = []
    for condition in stop_conditions:
        status = "satisfied"
        lowered = condition.description.lower()
        if "earliest" in lowered and provenance.earliest_anchor_document_id is None:
            status = "unsatisfied"
        elif "provenance" in lowered and provenance.confidence_score < 0.45:
            status = "unsatisfied"
        elif "contradiction" in lowered and "contradiction" in open_gap_types:
            status = "unsatisfied"
        elif "official" in lowered and any(gap_type in open_gap_types for gap_type in {"primary_source", "provenance"}):
            status = "unsatisfied"
        elif "diversity" in lowered and "source_diversity" in open_gap_types:
            status = "unsatisfied"
        output.append(condition.model_copy(update={"status": status}))
    return output
