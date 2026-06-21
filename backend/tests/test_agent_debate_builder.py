import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.investigation import (
    AnalystResult,
    CandidateClaim,
    ClaimCounterpointPair,
    ClaimCounterpointResult,
    ClaimReceiptReview,
    CounterNarrative,
    CounterNarrativeResult,
    DraftReportSections,
    InvestigationPlan,
    InvestigationPlanTimeWindow,
    NarrativeFamilyResult,
    ReceiptsResult,
    SoftenedClaim,
)
from services.agent_debate_builder import build_agent_debate


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        query_text="Trace the hidden energy tax story.",
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="spread",
        entities=["energy", "tax"],
        search_queries=["hidden energy tax"],
        semantic_queries=["trace hidden energy tax spread"],
        target_source_types=["local_news", "national_news"],
        requested_outputs=["receipts", "agent_debate"],
        time_window=InvestigationPlanTimeWindow(label="all_time"),
        retrieval_mode="broad",
        risk_notes=[],
        uncertainty_requirements=[],
    )


def test_agent_debate_builder_surfaces_rejected_and_softened_claims():
    plan = _plan()
    analyst = AnalystResult(
        investigation_id="inv_debate",
        plan_snapshot=plan,
        draft_report_sections=DraftReportSections(
            executive_summary="The narrative spread quickly.",
            observed_facts="facts",
            reasonable_inferences="Possible coordination signals exist.",
            timeline_summary="timeline",
            counter_narrative_summary="counter",
            uncertainties="uncertainties",
        ),
        candidate_claims=[
            CandidateClaim(
                id="claim_supported",
                claim_text="The narrative spread quickly.",
                claim_type="observed_fact",
                supporting_document_ids=["doc_1"],
                supporting_evidence_span_ids=[],
                confidence_score=0.8,
                caveats=[],
            )
        ],
        limitations=["First observed is limited to the retrieved corpus."],
        recommended_human_checks=[],
        confidence_score=0.7,
        confidence_label="high",
    )
    counter = CounterNarrativeResult(
        investigation_id="inv_debate",
        plan_snapshot=plan,
        counter_narratives=[
            CounterNarrative(
                id="counter_1",
                title="Corrective frame",
                summary="A corrective frame exists.",
                canonical_phrase="energy myth",
                related_phrases=[],
                supporting_document_ids=["doc_2"],
                first_observed_doc_id="doc_2",
                relationship_to_main_narrative="corrective",
                confidence_score=0.6,
            )
        ],
        notes=[],
        limitations=[],
        confidence_score=0.6,
        confidence_label="medium",
    )
    counterpoints = ClaimCounterpointResult(
        investigation_id="inv_debate",
        plan_snapshot=plan,
        pairs=[
            ClaimCounterpointPair(
                claim_id="claim_supported",
                main_claim_text="The narrative spread quickly.",
                counter_claim_text="The evidence is more mixed than the main claim implies.",
                counter_type="corrective",
                relationship_summary="summary",
                supporting_document_ids=["doc_1"],
                counter_document_ids=["doc_2"],
                main_receipts=[],
                counter_receipts=[],
                confidence_score=0.74,
                caveats=[],
            )
        ],
        unmatched_claim_ids=[],
        limitations=[],
        confidence_score=0.7,
        confidence_label="medium",
    )
    family = NarrativeFamilyResult(
        investigation_id="inv_debate",
        plan_snapshot=plan,
        family_title="Cost narrative family",
        parent_frame="Cost burden framing",
        summary="summary",
        child_narratives=[],
        active_branch_id=None,
        fastest_growing_child=None,
        broadest_source_diversity_child=None,
        mutation_summary="The main branch shows two phrase shifts across source types.",
        mutation_trail=[],
        limitations=[],
        confidence_score=0.62,
        confidence_label="medium",
    )
    receipts = ReceiptsResult(
        investigation_id="inv_debate",
        plan_snapshot=plan,
        claim_receipts=[
            ClaimReceiptReview(
                claim_id="claim_supported",
                claim_text="The narrative spread quickly.",
                claim_side="main",
                support_status="partially_supported",
                support_summary="Some support exists, but it is contested.",
                supporting_receipts=[],
                contradicting_receipts=[],
                missing_evidence_notes=[],
                verification_state="mixed",
                confidence_score=0.55,
                caveats=[],
            ),
            ClaimReceiptReview(
                claim_id="claim_reject",
                claim_text="The narrative was coordinated.",
                claim_side="main",
                support_status="unsupported",
                support_summary="Unsupported.",
                supporting_receipts=[],
                contradicting_receipts=[],
                missing_evidence_notes=[],
                verification_state="pending",
                confidence_score=0.22,
                caveats=[],
            ),
        ],
        counter_claim_receipts=[],
        limitations=[],
        confidence_score=0.58,
        confidence_label="medium",
    )

    result = build_agent_debate(
        "inv_debate",
        plan,
        analyst,
        counter,
        family,
        counterpoints,
        receipts,
        report=None,
    )

    assert result.analyst_position
    assert result.skeptic_response
    assert result.rejected_claims
    assert "unsupported" in result.rejected_claims[0]
    assert result.softened_claims
    assert isinstance(result.softened_claims[0], SoftenedClaim)
    assert result.confidence_label in {"medium", "high"}
