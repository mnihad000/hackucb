from __future__ import annotations

from collections import defaultdict

from agents.claim_counterpoint_agent import build_claim_counterpoints
from agents.receipts_agent import build_receipts as build_receipts_agent
from agents.retriever_agent import RetrieverAgent
from config import get_settings
from models.document import Document
from models.investigation import (
    AgentDebateResult,
    ClaimLedgerResult,
    FinalReportResult,
    GapAnalysisResult,
    GapLedgerResult,
    InvestigationPlan,
    InvestigationWorkspace,
    ProvenanceTraceResult,
    ResearchLoopRunResult,
    ResearchPassSummary,
    RetryHistoryEntry,
    RetrievalLane,
    RetrievalResult,
    SkepticReviewResult,
    ConfidenceDimension,
    ConfidenceDimensions,
    EvidenceBudget,
)
from services.agent_debate_builder import build_agent_debate
from services.band_room import get_band_room_sync
from services.analyst_builder import build_analyst_result
from services.claim_ledger_builder import build_claim_ledger
from services.counter_narrative_builder import build_counter_narratives
from services.final_report_builder import apply_receipts_annotations, build_final_report
from services.gap_analysis_builder import build_gap_analysis
from services.investigation_repository import InvestigationRepository
from services.narrative_family_builder import build_narrative_family
from services.provenance_trace_builder import build_provenance_trace
from services.skeptic_builder import build_skeptic_review
from services.source_diversity_builder import build_source_diversity
from services.source_verification_builder import build_source_verification, verification_map_from_result
from services.timeline_builder import build_timeline
from services.verification import VerificationService


class InvestigationRunner:
    def __init__(
        self,
        repository: InvestigationRepository,
        retriever: RetrieverAgent,
        verifier: VerificationService,
    ) -> None:
        self._repository = repository
        self._retriever = retriever
        self._verifier = verifier
        self._settings = get_settings()

    def _publish_band_stage(
        self,
        investigation_id: str,
        *,
        stage: str,
        role: str,
        content: str,
        confidence_label: str = "",
    ) -> None:
        try:
            result = get_band_room_sync().sync_stage_event(
                investigation_id=investigation_id,
                stage=stage,
                role=role,
                content=content,
                metadata={"confidence_label": confidence_label},
            )
            if result.status == "failed":
                # Band is an observability/collaboration layer; never fail the investigation for it.
                pass
        except Exception:
            pass

    def run(self, investigation_id: str, plan: InvestigationPlan, *, force_refresh: bool = False) -> InvestigationWorkspace:
        if not self._live_models_available():
            run_result = ResearchLoopRunResult(
                investigation_id=investigation_id,
                plan_snapshot=plan,
                final_decision="configuration_missing",
                warnings=["Live Gemini or Groq configuration is required for the supervised research loop."],
                confidence_dimensions=self._empty_confidence_dimensions("Live model configuration missing."),
            )
            self._repository.save_research_loop_run_result(run_result)
            return self._repository.get_investigation_workspace(investigation_id)

        prior_result: RetrievalResult | None = None
        prior_documents: list[Document] | None = None
        pass_history: list[ResearchPassSummary] = []
        retry_history: list[RetryHistoryEntry] = []
        last_gap_analysis: GapAnalysisResult | None = None
        last_skeptic_review: SkepticReviewResult | None = None
        last_provenance: ProvenanceTraceResult | None = None
        last_report: FinalReportResult | None = None
        last_claim_ledger: ClaimLedgerResult | None = None

        for pass_number in range(1, 4):
            lanes, follow_up_queries, requested_source_classes = self._pass_instructions(
                plan,
                last_gap_analysis,
                last_skeptic_review,
            )
            run_plan = plan.model_copy(
                update={
                    "target_source_types": _dedupe([*plan.target_source_types, *requested_source_classes]),
                }
            )
            retrieval = self._retriever.retrieve(
                investigation_id=investigation_id,
                plan=run_plan,
                force_refresh=force_refresh or pass_number > 1,
                lanes=lanes,
                pass_number=pass_number,
                follow_up_queries=follow_up_queries,
                prior_result=prior_result,
                prior_documents=prior_documents,
            )
            self._publish_band_stage(
                investigation_id,
                stage="retrieval",
                role="Retriever Agent",
                content=(
                    f"Pass {pass_number}: retrieved {retrieval.coverage_summary.total_documents} document(s) "
                    f"across {retrieval.coverage_summary.unique_sources} source(s)."
                ),
                confidence_label=retrieval.evidence_coverage_confidence,
            )
            documents = self._repository.get_retrieved_documents(investigation_id)
            source_diversity = build_source_diversity(investigation_id, run_plan, retrieval, documents)
            self._repository.save_source_diversity_result(source_diversity)
            self._publish_band_stage(
                investigation_id,
                stage="source_diversity",
                role="Source Diversity Agent",
                content=(
                    f"Pass {pass_number}: classified {source_diversity.classified_documents} document(s) "
                    f"across {len(source_diversity.source_type_distribution)} source type(s)."
                ),
                confidence_label=source_diversity.confidence_label,
            )
            timeline = build_timeline(investigation_id, run_plan, retrieval, documents)
            self._repository.save_timeline_result(timeline)
            self._publish_band_stage(
                investigation_id,
                stage="timeline",
                role="Timeline Agent",
                content=(
                    f"Pass {pass_number}: built {len(timeline.timeline_events)} timeline event(s); "
                    f"first observed document is {timeline.first_observed_doc_id or 'unknown'}."
                ),
                confidence_label=timeline.confidence_label,
            )
            counter_narratives = build_counter_narratives(investigation_id, run_plan, retrieval, documents)
            self._repository.save_counter_narrative_result(counter_narratives)
            self._publish_band_stage(
                investigation_id,
                stage="counter_narratives",
                role="Counter-Narrative Agent",
                content=(
                    f"Pass {pass_number}: identified {len(counter_narratives.counter_narratives)} "
                    "counter-frame candidate(s)."
                ),
                confidence_label=counter_narratives.confidence_label,
            )
            family = build_narrative_family(investigation_id, run_plan, retrieval, documents, timeline, counter_narratives)
            self._repository.save_narrative_family_result(family)
            self._publish_band_stage(
                investigation_id,
                stage="narrative_family",
                role="Narrative Family Agent",
                content=(
                    f"Pass {pass_number}: grouped narrative family '{family.family_title}' "
                    f"with {len(family.child_narratives)} branch(es)."
                ),
                confidence_label=family.confidence_label,
            )
            analyst = build_analyst_result(investigation_id, run_plan, retrieval, documents, timeline, counter_narratives)
            self._repository.save_analyst_result(analyst)
            self._publish_band_stage(
                investigation_id,
                stage="analyst",
                role="Analyst Agent",
                content=(
                    f"Pass {pass_number}: drafted synthesis with {len(analyst.candidate_claims)} "
                    "candidate claim(s)."
                ),
                confidence_label=analyst.confidence_label,
            )
            provenance = build_provenance_trace(investigation_id, run_plan, retrieval, documents)
            self._repository.save_provenance_trace_result(provenance)
            gap_analysis = build_gap_analysis(
                investigation_id,
                run_plan,
                retrieval,
                documents,
                source_diversity,
                timeline,
                counter_narratives,
                analyst,
                provenance,
                pass_number=pass_number,
            )
            self._repository.save_gap_analysis_result(gap_analysis)
            skeptic_review = build_skeptic_review(
                investigation_id,
                run_plan,
                analyst,
                gap_analysis,
                provenance,
                pass_number=pass_number,
                max_passes=3,
            )
            self._repository.save_skeptic_review_result(skeptic_review)
            self._publish_band_stage(
                investigation_id,
                stage="skeptic_review",
                role="Skeptic Agent",
                content=f"Pass {pass_number}: {skeptic_review.overall_decision}. {skeptic_review.reason}",
                confidence_label=skeptic_review.overall_decision,
            )

            pass_history.append(
                ResearchPassSummary(
                    pass_number=pass_number,
                    lanes_run=lanes,
                    gaps_opened=[gap.gap_id for gap in gap_analysis.missing_evidence if gap.status == "open"],
                    gaps_resolved=[gap.gap_id for gap in gap_analysis.missing_evidence if gap.status == "resolved"],
                    skeptic_decision=skeptic_review.overall_decision,
                    notes=[skeptic_review.reason],
                )
            )
            for lane, queries in follow_up_queries.items():
                retry_history.append(
                    RetryHistoryEntry(
                        pass_number=pass_number,
                        lane=lane,
                        reason=skeptic_review.reason,
                        source_classes=requested_source_classes,
                        queries=queries,
                    )
                )

            prior_result = retrieval
            prior_documents = documents
            last_gap_analysis = gap_analysis
            last_skeptic_review = skeptic_review
            last_provenance = provenance

            if skeptic_review.overall_decision != "retry_required":
                break

        assert prior_result is not None
        assert prior_documents is not None
        assert last_gap_analysis is not None
        assert last_skeptic_review is not None
        assert last_provenance is not None

        claim_counterpoints = build_claim_counterpoints(
            investigation_id,
            run_plan,
            prior_result,
            prior_documents,
            counter_narratives,
            analyst,
        )
        self._repository.save_claim_counterpoint_result(claim_counterpoints)
        self._publish_band_stage(
            investigation_id,
            stage="claim_counterpoints",
            role="Claim Counterpoint Agent",
            content=(
                f"Matched {len(claim_counterpoints.pairs)} counterpoint pair(s); "
                f"{len(claim_counterpoints.unmatched_claim_ids)} claim(s) remain unmatched."
            ),
            confidence_label=claim_counterpoints.confidence_label,
        )
        report = build_final_report(
            investigation_id,
            run_plan,
            prior_result,
            prior_documents,
            timeline,
            counter_narratives,
            family,
            analyst,
            claim_counterpoints,
        )
        source_verification = build_source_verification(
            investigation_id,
            prior_documents,
            cited_document_ids=self._cited_document_ids(report, claim_counterpoints),
        )
        self._repository.save_source_verification_result(source_verification, update_stage=False)
        self._publish_band_stage(
            investigation_id,
            stage="source_verification",
            role="Browserbase Verification Agent",
            content=(
                f"Checked {len(source_verification.receipts)} cited source(s): "
                f"{source_verification.verified_count} verified, "
                f"{source_verification.metadata_mismatch_count} metadata mismatch, "
                f"{source_verification.unavailable_count} unavailable, "
                f"{source_verification.pending_count} pending."
            ),
            confidence_label="source_verification",
        )
        receipts = build_receipts_agent(
            investigation_id,
            run_plan,
            prior_documents,
            report,
            claim_counterpoints,
            self._verification_map(prior_documents, report, claim_counterpoints, source_verification),
        )
        self._repository.save_receipts_result(receipts)
        self._publish_band_stage(
            investigation_id,
            stage="receipts",
            role="Receipts Agent",
            content=(
                f"Reviewed {len(receipts.claim_receipts)} report claim receipt set(s) "
                f"and {len(receipts.counter_claim_receipts)} counter-claim receipt set(s)."
            ),
            confidence_label=receipts.confidence_label,
        )
        claim_ledger = build_claim_ledger(investigation_id, analyst, receipts, last_skeptic_review)
        self._repository.save_claim_ledger_result(claim_ledger)
        gap_ledger = GapLedgerResult(investigation_id=investigation_id, entries=last_gap_analysis.missing_evidence)
        self._repository.save_gap_ledger_result(gap_ledger)

        final_decision = (
            "completed_with_softening"
            if last_skeptic_review.overall_decision == "pass_with_softening"
            else "completed"
        )
        if last_skeptic_review.overall_decision == "retry_required":
            final_decision = "insufficient_evidence"

        report = apply_receipts_annotations(report, receipts)
        report = report.model_copy(
            update={
                "confidence_dimensions": self._confidence_dimensions(
                    prior_result,
                    timeline,
                    last_gap_analysis,
                    last_provenance,
                    receipts,
                    claim_ledger,
                ),
            }
        )
        report = self._filter_report_claims(report, claim_ledger)
        self._repository.save_final_report_result(report)
        self._publish_band_stage(
            investigation_id,
            stage="final_report",
            role="Final Report Agent",
            content=(
                f"Finalized report '{report.report_title}' with {len(report.key_claims)} key claim(s) "
                f"and {report.confidence_label} confidence."
            ),
            confidence_label=report.confidence_label,
        )
        debate = build_agent_debate(
            investigation_id,
            run_plan,
            analyst,
            counter_narratives,
            family,
            claim_counterpoints,
            receipts,
            report,
        )
        try:
            sync = get_band_room_sync()
            sync_result = sync.sync_debate(debate)
            if sync_result.status != "not_configured":
                debate = sync.apply_sync_result(debate, sync_result)
        except Exception:
            pass
        self._repository.save_agent_debate_result(debate)

        research_loop = ResearchLoopRunResult(
            investigation_id=investigation_id,
            plan_snapshot=run_plan,
            pass_history=pass_history,
            retry_history=retry_history,
            active_pass=pass_history[-1].pass_number,
            final_decision=final_decision,
            evidence_budget=EvidenceBudget(
                documents_fetched=len(prior_documents),
                source_classes_covered=len(prior_result.coverage_summary.source_type_distribution),
                retries_used=max(0, len(pass_history) - 1),
                unresolved_gaps_remaining=sum(1 for gap in last_gap_analysis.missing_evidence if gap.status == "open"),
            ),
            confidence_dimensions=report.confidence_dimensions or self._empty_confidence_dimensions("No final confidence dimensions computed."),
            warnings=report.limitations,
        )
        self._repository.save_research_loop_run_result(research_loop)
        return self._repository.get_investigation_workspace(investigation_id)

    def _pass_instructions(
        self,
        plan: InvestigationPlan,
        gap_analysis: GapAnalysisResult | None,
        skeptic_review: SkepticReviewResult | None,
    ) -> tuple[list[RetrievalLane], dict[RetrievalLane, list[str]], list[str]]:
        if gap_analysis is None or skeptic_review is None or skeptic_review.overall_decision != "retry_required":
            return list(plan.retrieval_lanes), {}, []
        follow_up_queries: dict[RetrievalLane, list[str]] = defaultdict(list)
        source_classes: list[str] = []
        lanes: list[RetrievalLane] = []
        for gap in gap_analysis.missing_evidence:
            if gap.status != "open" or gap.recommended_retrieval_lane is None:
                continue
            lanes.append(gap.recommended_retrieval_lane)
            follow_up_queries[gap.recommended_retrieval_lane].extend(gap.follow_up_queries)
            source_classes.extend(gap.recommended_source_classes)
        return _dedupe_lanes(lanes) or list(plan.retrieval_lanes), {lane: _dedupe(queries) for lane, queries in follow_up_queries.items()}, _dedupe(source_classes)

    def _verification_map(
        self,
        documents: list[Document],
        report: FinalReportResult,
        claim_counterpoints,
        source_verification=None,
    ) -> dict[str, str]:
        doc_ids = self._cited_document_ids(report, claim_counterpoints)
        verification_map = verification_map_from_result(source_verification)
        for doc_id in doc_ids:
            verification_map.setdefault(doc_id, "pending")
        return verification_map

    def _cited_document_ids(self, report: FinalReportResult, claim_counterpoints) -> list[str]:
        doc_ids: list[str] = []
        for claim in report.key_claims:
            for citation in [*claim.citations, *claim.counter_citations]:
                doc_ids.append(citation.document_id)
        if claim_counterpoints is not None:
            for pair in claim_counterpoints.pairs:
                for citation in [*pair.main_receipts, *pair.counter_receipts]:
                    doc_ids.append(citation.document_id)
        return list(dict.fromkeys(doc_ids))

    def _confidence_dimensions(
        self,
        retrieval: RetrievalResult,
        timeline,
        gap_analysis: GapAnalysisResult,
        provenance: ProvenanceTraceResult,
        receipts,
        claim_ledger: ClaimLedgerResult,
    ) -> ConfidenceDimensions:
        verification_score = max(0.0, receipts.confidence_score - 0.12 * sum(
            1 for review in receipts.claim_receipts if review.verification_state in {"pending", "metadata_mismatch", "unavailable"}
        ))
        synthesis_score = max(
            0.0,
            min(
                retrieval.coverage_summary.total_documents / 10,
                sum(1 for entry in claim_ledger.entries if entry.survived_to_report) / max(1, len(claim_ledger.entries)),
            ) - (0.08 * sum(1 for gap in gap_analysis.missing_evidence if gap.status == "open")),
        )
        return ConfidenceDimensions(
            coverage_confidence=ConfidenceDimension(
                score=_label_score(retrieval.evidence_coverage_confidence),
                reason=f"{retrieval.coverage_summary.total_documents} retrieved documents across {retrieval.coverage_summary.unique_sources} sources.",
            ),
            chronology_confidence=ConfidenceDimension(
                score=timeline.confidence_score,
                reason=timeline.timeline_summary,
            ),
            contradiction_confidence=ConfidenceDimension(
                score=gap_analysis.scores.contradiction_coverage,
                reason=f"{len(gap_analysis.missing_evidence)} open gap(s) remain after contradiction review.",
            ),
            provenance_confidence=ConfidenceDimension(
                score=provenance.confidence_score,
                reason=provenance.earliest_anchor_summary,
            ),
            verification_confidence=ConfidenceDimension(
                score=round(min(max(verification_score, 0.0), 0.95), 3),
                reason="Verification confidence is penalized when supporting receipts remain pending or mismatched.",
            ),
            synthesis_confidence=ConfidenceDimension(
                score=round(min(max(synthesis_score, 0.0), 0.95), 3),
                reason="Synthesis confidence is capped by unresolved gaps and claim survival.",
            ),
        )

    def _filter_report_claims(self, report: FinalReportResult, claim_ledger: ClaimLedgerResult) -> FinalReportResult:
        ledger_by_claim_id = {entry.claim_id: entry for entry in claim_ledger.entries}
        filtered_claims = [
            claim
            for claim in report.key_claims
            if ledger_by_claim_id.get(claim.claim_id) is None
            or ledger_by_claim_id[claim.claim_id].state not in {"contradicted", "rejected", "unresolved"}
        ]
        return report.model_copy(update={"key_claims": filtered_claims})

    def _live_models_available(self) -> bool:
        return (not self._settings.DEMO_MODE) and bool(
            self._settings.GEMINI_API_KEY or self._settings.GROQ_API_KEY
        )

    def _empty_confidence_dimensions(self, reason: str) -> ConfidenceDimensions:
        return ConfidenceDimensions(
            coverage_confidence=ConfidenceDimension(score=0.0, reason=reason),
            chronology_confidence=ConfidenceDimension(score=0.0, reason=reason),
            contradiction_confidence=ConfidenceDimension(score=0.0, reason=reason),
            provenance_confidence=ConfidenceDimension(score=0.0, reason=reason),
            verification_confidence=ConfidenceDimension(score=0.0, reason=reason),
            synthesis_confidence=ConfidenceDimension(score=0.0, reason=reason),
        )


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
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


def _dedupe_lanes(values: list[RetrievalLane]) -> list[RetrievalLane]:
    output: list[RetrievalLane] = []
    seen: set[RetrievalLane] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _label_score(label: str) -> float:
    if label == "high":
        return 0.82
    if label == "medium":
        return 0.58
    return 0.32
