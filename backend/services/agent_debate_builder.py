from __future__ import annotations

from collections import Counter

from models.investigation import (
    AgentDebateResult,
    AnalystResult,
    ClaimCounterpointResult,
    CounterNarrativeResult,
    FinalReportResult,
    InvestigationPlan,
    NarrativeFamilyResult,
    ReceiptsResult,
    SoftenedClaim,
)

_REJECTED_STATUSES = {"unsupported", "contradicted", "insufficient_evidence"}


def build_agent_debate(
    investigation_id: str,
    plan: InvestigationPlan,
    analyst: AnalystResult,
    counter_narratives: CounterNarrativeResult,
    narrative_family: NarrativeFamilyResult | None,
    claim_counterpoints: ClaimCounterpointResult,
    receipts: ReceiptsResult,
    report: FinalReportResult | None,
) -> AgentDebateResult:
    rejected_claims = _rejected_claims(receipts)
    softened_claims = _softened_claims(receipts)
    analyst_position = _analyst_position(analyst)
    skeptic_response = _skeptic_response(
        analyst,
        counter_narratives,
        narrative_family,
        claim_counterpoints,
        receipts,
    )
    receipts_check = _receipts_check(receipts)
    counter_narrative_note = _counter_narrative_note(counter_narratives, narrative_family, claim_counterpoints)
    safety_grounding_decision = _safety_grounding_decision(
        receipts,
        narrative_family,
        rejected_claims,
        softened_claims,
    )
    final_language_decision = _final_language_decision(
        report,
        narrative_family,
        receipts,
        rejected_claims,
        softened_claims,
    )
    limitations = [
        "Agent debate is summarized deterministically from observable stage outputs; a dedicated skeptic or safety agent is not yet running in this backend.",
    ]
    if report is None:
        limitations.append(
            "Final language guidance was generated without a persisted final report artifact, so the debate summary reflects pre-report stage outputs."
        )
    confidence_score = _debate_confidence(receipts, counter_narratives, softened_claims, rejected_claims)

    return AgentDebateResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        analyst_position=analyst_position,
        skeptic_response=skeptic_response,
        receipts_check=receipts_check,
        counter_narrative_note=counter_narrative_note,
        safety_grounding_decision=safety_grounding_decision,
        final_language_decision=final_language_decision,
        rejected_claims=rejected_claims,
        softened_claims=softened_claims,
        limitations=limitations,
        confidence_score=confidence_score,
        confidence_label=_confidence_label(confidence_score),
    )


def _analyst_position(analyst: AnalystResult) -> str:
    executive = analyst.draft_report_sections.executive_summary.strip()
    inference = analyst.draft_report_sections.reasonable_inferences.strip()
    if executive and inference:
        return f"{executive} {inference}"
    return executive or inference or "The analyst stage did not produce a strong synthesis summary."


def _skeptic_response(
    analyst: AnalystResult,
    counter_narratives: CounterNarrativeResult,
    narrative_family: NarrativeFamilyResult | None,
    claim_counterpoints: ClaimCounterpointResult,
    receipts: ReceiptsResult,
) -> str:
    status_counts = Counter(review.support_status for review in receipts.claim_receipts)
    challenged_count = (
        status_counts.get("partially_supported", 0)
        + status_counts.get("unsupported", 0)
        + status_counts.get("contradicted", 0)
        + status_counts.get("insufficient_evidence", 0)
    )
    parts = [
        f"The skeptic pass challenges {challenged_count} of {len(receipts.claim_receipts)} main report claim(s) on grounding strength or missing corroboration."
    ]
    if counter_narratives.counter_narratives:
        parts.append(
            f"It also notes {len(counter_narratives.counter_narratives)} competing frame cluster(s) that complicate one-sided interpretation."
        )
    if claim_counterpoints.pairs:
        strongest_pair = max(claim_counterpoints.pairs, key=lambda pair: pair.confidence_score)
        parts.append(
            f"The strongest claim-level counterpoint is a {strongest_pair.counter_type.replace('_', ' ')} response to '{strongest_pair.main_claim_text}'."
        )
    if narrative_family is not None and narrative_family.mutation_trail:
        parts.append(
            f"The active branch mutation rail contains {len(narrative_family.mutation_trail)} phrase-evolution step(s), so the debate should distinguish semantic drift from factual corroboration."
        )
    if analyst.limitations:
        parts.append(f"Key analyst limitation carried into the debate: {analyst.limitations[0]}")
    return " ".join(parts)


def _receipts_check(receipts: ReceiptsResult) -> str:
    reviews = [*receipts.claim_receipts, *receipts.counter_claim_receipts]
    status_counts = Counter(review.support_status for review in reviews)
    verification_counts = Counter(review.verification_state for review in reviews)
    return (
        f"Receipts review found {status_counts.get('supported', 0)} supported, "
        f"{status_counts.get('partially_supported', 0)} partially supported, "
        f"{status_counts.get('unsupported', 0)} unsupported, "
        f"{status_counts.get('contradicted', 0)} contradicted, and "
        f"{status_counts.get('insufficient_evidence', 0)} insufficient-evidence claim review(s). "
        f"Verification states were led by {verification_counts.most_common(1)[0][0].replace('_', ' ')}."
    )


def _counter_narrative_note(
    counter_narratives: CounterNarrativeResult,
    narrative_family: NarrativeFamilyResult | None,
    claim_counterpoints: ClaimCounterpointResult,
) -> str:
    if not counter_narratives.counter_narratives:
        if narrative_family is not None and narrative_family.mutation_summary:
            return (
                "No strong counter-frame cluster was available, so the debate remained anchored to the main evidence packet. "
                + narrative_family.mutation_summary
            )
        return "No strong counter-frame cluster was available, so the debate remained anchored to the main evidence packet."
    strongest_cluster = max(
        counter_narratives.counter_narratives,
        key=lambda item: item.confidence_score,
    )
    if not claim_counterpoints.pairs:
        return (
            f"The debate considered the counter-frame '{strongest_cluster.title}', but no claim-level pair was strong enough to attach to a report claim."
        )
    strongest_pair = max(claim_counterpoints.pairs, key=lambda pair: pair.confidence_score)
    note = (
        f"The debate incorporated the counter-frame '{strongest_cluster.title}' and the strongest claim-level response targeted "
        f"'{strongest_pair.main_claim_text}' with a {strongest_pair.counter_type.replace('_', ' ')} critique."
    )
    if narrative_family is not None and narrative_family.mutation_summary:
        note = f"{note} {narrative_family.mutation_summary}"
    return note


def _safety_grounding_decision(
    receipts: ReceiptsResult,
    narrative_family: NarrativeFamilyResult | None,
    rejected_claims: list[str],
    softened_claims: list[SoftenedClaim],
) -> str:
    if rejected_claims:
        decision = (
            f"Safety grounding requires {len(rejected_claims)} claim(s) to stay out of the report as confident conclusions and "
            f"{len(softened_claims)} claim(s) to use qualified language."
        )
        if narrative_family is not None and narrative_family.mutation_trail:
            decision += " Mutation lineage should be described as framing evolution, not independent proof."
        return decision
    if softened_claims:
        decision = (
            f"Safety grounding passes with caution: {len(softened_claims)} claim(s) should be presented as suggestive rather than settled."
        )
        if narrative_family is not None and narrative_family.mutation_trail:
            decision += " Mutation evidence should remain in the language of observed phrase shifts."
        return decision
    if receipts.claim_receipts:
        return "Safety grounding passes with no major claim rejections in the current retrieved corpus."
    return "Safety grounding remains limited because the investigation has no completed main-claim receipts review."


def _final_language_decision(
    report: FinalReportResult | None,
    narrative_family: NarrativeFamilyResult | None,
    receipts: ReceiptsResult,
    rejected_claims: list[str],
    softened_claims: list[SoftenedClaim],
) -> str:
    if rejected_claims:
        return (
            "Use cautious language that keeps unsupported or contradicted claims out of the executive framing and anchors any chronology to the retrieved dataset."
        )
    if softened_claims:
        return (
            "Use qualified language such as 'the retrieved evidence suggests' or 'in the observed corpus' for contested claims."
        )
    if report is not None:
        summary = report.report_summary
        if narrative_family is not None and narrative_family.mutation_summary:
            summary = f"{summary} {narrative_family.mutation_summary}"
        return f"Final language can stay close to the current report framing: {summary}"
    return "Final language can remain assertive only where receipts show strong support and limited contradiction."


def _rejected_claims(receipts: ReceiptsResult) -> list[str]:
    rejected: list[str] = []
    for review in receipts.claim_receipts:
        if review.support_status in _REJECTED_STATUSES:
            rejected.append(f"{review.claim_text} ({review.support_status.replace('_', ' ')})")
    return rejected


def _softened_claims(receipts: ReceiptsResult) -> list[SoftenedClaim]:
    softened: list[SoftenedClaim] = []
    for review in receipts.claim_receipts:
        if review.support_status == "partially_supported":
            softened.append(
                SoftenedClaim(
                    claim_id=review.claim_id,
                    original=review.claim_text,
                    softened=_soften_claim_text(review.claim_text, review.support_status),
                    reason="Receipts found some support, but corroboration is limited or contested.",
                )
            )
            continue
        if review.support_status == "supported" and review.verification_state != "verified":
            softened.append(
                SoftenedClaim(
                    claim_id=review.claim_id,
                    original=review.claim_text,
                    softened=f"In the retrieved dataset, evidence currently supports that {review.claim_text[0].lower() + review.claim_text[1:]}",
                    reason=f"Support is strong, but verification state is {review.verification_state.replace('_', ' ')} rather than fully verified.",
                )
            )
    return softened


def _soften_claim_text(claim_text: str, support_status: str) -> str:
    normalized = claim_text.rstrip(". ")
    if support_status == "partially_supported":
        return f"The retrieved evidence suggests that {normalized[0].lower() + normalized[1:]}."
    return f"The current retrieved corpus does not justify stating that {normalized[0].lower() + normalized[1:]} as a settled fact."


def _debate_confidence(
    receipts: ReceiptsResult,
    counter_narratives: CounterNarrativeResult,
    softened_claims: list[SoftenedClaim],
    rejected_claims: list[str],
) -> float:
    score = 0.22
    score += receipts.confidence_score * 0.45
    score += min(0.12, len(counter_narratives.counter_narratives) * 0.04)
    score += min(0.08, len(softened_claims) * 0.02)
    score += min(0.08, len(rejected_claims) * 0.02)
    return round(min(score, 0.93), 3)


def _confidence_label(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.46:
        return "medium"
    return "low"
