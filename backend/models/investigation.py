from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from models.document import (
    Document,
    SourceClassificationConfidence,
    SourceContentForm,
    SourceIdeology,
    SourceInstitutionKind,
)


PlannerIntent = Literal[
    "origin",
    "spread",
    "counter-narrative",
    "source-ecosystem",
    "general investigation",
]

RetrievalMode = Literal["broad", "narrow"]
InvestigationStatus = Literal[
    "planning_completed",
    "retrieval_completed",
    "source_diversity_completed",
    "timeline_completed",
    "counter_narrative_completed",
    "narrative_family_completed",
    "analyst_completed",
    "claim_counterpoint_completed",
    "receipts_completed",
    "agent_debate_completed",
    "report_completed",
]
InvestigationStage = Literal[
    "planner",
    "retriever",
    "source_diversity",
    "timeline",
    "counter_narrative",
    "narrative_family",
    "analyst",
    "claim_counterpoint",
    "receipts",
    "agent_debate",
    "report",
]
CoverageConfidence = Literal["low", "medium", "high"]
TimelineEventType = Literal[
    "first_observed",
    "early_amplification",
    "broader_pickup",
    "official_mention",
    "counter_narrative_entry",
    "resurfacing",
    "other",
]
NarrativeSide = Literal["main", "counter", "related", "unknown"]
TimelineConfidenceLabel = Literal["low", "medium", "high"]
CounterNarrativeRelationship = Literal["opposing", "reframing", "corrective"]
CounterNarrativeConfidenceLabel = Literal["low", "medium", "high"]
NarrativeGrowthStatus = Literal["emerging", "amplifying", "mainstreaming", "declining", "unknown"]
NarrativeFamilyConfidenceLabel = Literal["low", "medium", "high", "unknown"]
NarrativeFamilyBranchType = Literal["main", "counter", "related", "mutation"]
NarrativeFamilyGenerationMethod = Literal["deterministic", "hybrid_agent"]
ClaimType = Literal["observed_fact", "inference", "uncertainty", "limitation", "recommendation"]
AnalystConfidenceLabel = Literal["low", "medium", "high"]
ClaimCounterpointType = Literal["opposing", "corrective", "reframing"]
ClaimCounterpointConfidenceLabel = Literal["low", "medium", "high"]
ClaimSupportStatus = Literal[
    "supported",
    "partially_supported",
    "unsupported",
    "contradicted",
    "insufficient_evidence",
]
ReceiptVerificationStatus = Literal["verified", "unavailable", "metadata_mismatch", "pending"]
ClaimVerificationState = Literal[
    "verified",
    "mixed",
    "metadata_mismatch",
    "unavailable",
    "pending",
    "not_available",
]
ReceiptsConfidenceLabel = Literal["low", "medium", "high"]
AgentDebateConfidenceLabel = Literal["low", "medium", "high"]
ReportConfidenceLabel = Literal["low", "medium", "high"]
SourceDiversityConfidenceLabel = Literal["low", "medium", "high"]


class InvestigationPlanTimeWindow(BaseModel):
    start: str | None = None
    end: str | None = None
    label: Literal["today", "this_week", "this_month", "recent", "all_time", "custom", "unknown"] = "unknown"


class InvestigationPlan(BaseModel):
    query_text: str
    topic: str
    canonical_phrase: str | None = None
    intent: PlannerIntent
    entities: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    semantic_queries: list[str] = Field(default_factory=list)
    target_source_types: list[str] = Field(default_factory=list)
    requested_outputs: list[str] = Field(default_factory=list)
    time_window: InvestigationPlanTimeWindow = Field(default_factory=InvestigationPlanTimeWindow)
    retrieval_mode: RetrievalMode = "broad"
    risk_notes: list[str] = Field(default_factory=list)
    uncertainty_requirements: list[str] = Field(default_factory=list)


class PlannerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(min_length=3)
    prior_context: dict | None = None


class PlannerResponse(BaseModel):
    investigation_id: str
    status: InvestigationStatus = "planning_completed"
    current_stage: InvestigationStage = "planner"
    query_text: str
    plan: InvestigationPlan
    warnings: list[str] = Field(default_factory=list)


class RecentInvestigationSummary(BaseModel):
    investigation_id: str
    query_text: str
    status: InvestigationStatus
    updated_at: datetime
    report_title: str
    report_summary: str | None = None
    receipt_count: int = 0
    source_count: int = 0


class SearchResult(BaseModel):
    query: str
    title: str
    url: str
    snippet: str | None = None
    rank: int
    provider: str
    provider_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RawPage(BaseModel):
    url: str
    final_url: str
    status_code: int
    content_type: str | None = None
    html: str
    fetched_at: datetime


class FetchFailure(BaseModel):
    url: str
    error_type: str
    message: str
    status_code: int | None = None
    retryable: bool = False


class DuplicateCandidate(BaseModel):
    left_doc_id: str
    right_doc_id: str
    similarity_score: float
    reason: str


class RetrievalRound(BaseModel):
    round_number: int
    queries: list[str] = Field(default_factory=list)
    provider: str
    discovered_results: int = 0
    fetched_pages: int = 0
    accepted_documents: int = 0
    new_documents: int = 0
    warnings: list[str] = Field(default_factory=list)


class CoverageSummary(BaseModel):
    total_documents: int = 0
    unique_sources: int = 0
    source_type_distribution: dict[str, int] = Field(default_factory=dict)
    has_counter_narrative_candidates: bool = False
    has_timeline_coverage: bool = False
    exact_phrase_hits: int = 0
    search_rounds_completed: int = 0


class RetrievalResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    retrieved_document_ids: list[str] = Field(default_factory=list)
    high_relevance_document_ids: list[str] = Field(default_factory=list)
    main_narrative_document_ids: list[str] = Field(default_factory=list)
    counter_narrative_candidate_ids: list[str] = Field(default_factory=list)
    context_document_ids: list[str] = Field(default_factory=list)
    possible_duplicate_pairs: list[DuplicateCandidate] = Field(default_factory=list)
    search_rounds: list[RetrievalRound] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    coverage_summary: CoverageSummary = Field(default_factory=CoverageSummary)
    evidence_coverage_confidence: CoverageConfidence = "low"
    cached: bool = False


class RetrieveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False
    max_rounds: int | None = Field(default=None, ge=1, le=6)


class SourceDiversityFinding(BaseModel):
    id: str
    label: str
    detail: str


class SourceDiversityResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    total_documents: int = 0
    classified_documents: int = 0
    source_type_distribution: dict[str, int] = Field(default_factory=dict)
    geographic_distribution: dict[str, int] = Field(default_factory=dict)
    institution_distribution: dict[SourceInstitutionKind, int] = Field(default_factory=dict)
    content_form_distribution: dict[SourceContentForm, int] = Field(default_factory=dict)
    ideology_distribution: dict[SourceIdeology, int] = Field(default_factory=dict)
    findings: list[SourceDiversityFinding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: SourceDiversityConfidenceLabel
    cached: bool = False


class SourceDiversityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class TimelineEvent(BaseModel):
    id: str
    document_id: str
    timestamp: datetime
    source_name: str
    source_type: str
    title: str
    url: str
    snippet: str | None = None
    event_type: TimelineEventType
    narrative_side: NarrativeSide
    importance_score: float = Field(ge=0.0, le=1.0)
    explanation: str


class TimelineResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    timeline_events: list[TimelineEvent] = Field(default_factory=list)
    first_observed_doc_id: str | None = None
    timeline_summary: str
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: TimelineConfidenceLabel
    cached: bool = False


class TimelineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class CounterNarrative(BaseModel):
    id: str
    title: str
    summary: str
    canonical_phrase: str | None = None
    related_phrases: list[str] = Field(default_factory=list)
    supporting_document_ids: list[str] = Field(default_factory=list)
    first_observed_doc_id: str | None = None
    relationship_to_main_narrative: CounterNarrativeRelationship
    confidence_score: float = Field(ge=0.0, le=1.0)


class CounterNarrativeResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    counter_narratives: list[CounterNarrative] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: CounterNarrativeConfidenceLabel
    cached: bool = False


class CounterNarrativeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class NarrativeFamilyChild(BaseModel):
    id: str
    title: str
    canonical_phrase: str
    branch_type: NarrativeFamilyBranchType = "related"
    related_phrases: list[str] = Field(default_factory=list)
    first_observed_doc_id: str | None = None
    relationship_to_parent: str
    growth_status: NarrativeGrowthStatus = "unknown"
    branch_summary: str
    supporting_document_ids: list[str] = Field(default_factory=list)
    source_count: int = 0
    source_type_count: int = 0
    source_diversity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    growth_score: float = Field(default=0.0, ge=0.0, le=1.0)


class NarrativeMutationStep(BaseModel):
    from_phrase: str
    to_phrase: str
    from_doc_id: str
    to_doc_id: str
    mutation_type: Literal["mutation", "phrase_reuse"]
    similarity_score: float = Field(ge=0.0, le=1.0)
    time_delta_hours: float = Field(ge=0.0)
    source_shift: bool = False
    explanation: str


class NarrativeFamilyResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    family_title: str
    parent_frame: str
    summary: str
    child_narratives: list[NarrativeFamilyChild] = Field(default_factory=list)
    active_branch_id: str | None = None
    fastest_growing_child: str | None = None
    broadest_source_diversity_child: str | None = None
    mutation_summary: str = ""
    mutation_trail: list[NarrativeMutationStep] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: NarrativeFamilyConfidenceLabel
    generation_method: NarrativeFamilyGenerationMethod = "deterministic"
    cached: bool = False


class NarrativeFamilyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class DraftReportSections(BaseModel):
    executive_summary: str
    observed_facts: str
    reasonable_inferences: str
    timeline_summary: str
    counter_narrative_summary: str
    uncertainties: str


class CandidateClaim(BaseModel):
    id: str
    claim_text: str
    claim_type: ClaimType
    supporting_document_ids: list[str] = Field(default_factory=list)
    supporting_evidence_span_ids: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    caveats: list[str] = Field(default_factory=list)


class AnalystResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    draft_report_sections: DraftReportSections
    candidate_claims: list[CandidateClaim] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommended_human_checks: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: AnalystConfidenceLabel
    cached: bool = False


class AnalystRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class ReportCitation(BaseModel):
    document_id: str
    source_name: str
    source_type: str
    title: str
    url: str
    published_at: datetime | None = None
    snippet: str | None = None
    relevance_note: str


class ClaimCounterpointPair(BaseModel):
    claim_id: str
    main_claim_text: str
    counter_claim_text: str
    counter_type: ClaimCounterpointType
    relationship_summary: str
    supporting_document_ids: list[str] = Field(default_factory=list)
    counter_document_ids: list[str] = Field(default_factory=list)
    main_receipts: list["ReportCitation"] = Field(default_factory=list)
    counter_receipts: list["ReportCitation"] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    caveats: list[str] = Field(default_factory=list)


class ClaimCounterpointResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    pairs: list[ClaimCounterpointPair] = Field(default_factory=list)
    unmatched_claim_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: ClaimCounterpointConfidenceLabel
    cached: bool = False


class ClaimCounterpointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class ReceiptEvidence(BaseModel):
    document_id: str
    source_name: str
    source_type: str
    title: str
    url: str
    published_at: datetime | None = None
    snippet: str | None = None
    evidence_span: str
    support_reason: str
    matched_terms: list[str] = Field(default_factory=list)
    verification_status: ReceiptVerificationStatus = "pending"


class ClaimReceiptReview(BaseModel):
    claim_id: str
    claim_text: str
    claim_side: Literal["main", "counter"]
    support_status: ClaimSupportStatus
    support_summary: str
    supporting_receipts: list[ReceiptEvidence] = Field(default_factory=list)
    contradicting_receipts: list[ReceiptEvidence] = Field(default_factory=list)
    missing_evidence_notes: list[str] = Field(default_factory=list)
    verification_state: ClaimVerificationState
    confidence_score: float = Field(ge=0.0, le=1.0)
    caveats: list[str] = Field(default_factory=list)


class ReceiptsResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    claim_receipts: list[ClaimReceiptReview] = Field(default_factory=list)
    counter_claim_receipts: list[ClaimReceiptReview] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: ReceiptsConfidenceLabel
    cached: bool = False


class ReceiptsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class SoftenedClaim(BaseModel):
    claim_id: str
    original: str
    softened: str
    reason: str


class AgentDebateResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    analyst_position: str
    skeptic_response: str
    receipts_check: str
    counter_narrative_note: str
    safety_grounding_decision: str
    final_language_decision: str
    rejected_claims: list[str] = Field(default_factory=list)
    softened_claims: list[SoftenedClaim] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: AgentDebateConfidenceLabel
    band_chat_id: str | None = None
    band_sync_status: Literal["not_configured", "synced", "failed", "skipped"] = "not_configured"
    band_message_count: int = 0
    band_sync_error: str | None = None
    cached: bool = False


class AgentDebateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class FinalReportClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    confidence_score: float = Field(ge=0.0, le=1.0)
    caveats: list[str] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)
    support_status: ClaimSupportStatus | None = None
    support_summary: str | None = None
    supporting_receipts: list[ReceiptEvidence] = Field(default_factory=list)
    contradicting_receipts: list[ReceiptEvidence] = Field(default_factory=list)
    missing_evidence_notes: list[str] = Field(default_factory=list)
    verification_state: ClaimVerificationState | None = None
    counterpoint_summary: str | None = None
    counterpoint_type: ClaimCounterpointType | None = None
    counter_citations: list[ReportCitation] = Field(default_factory=list)


class FinalReportSections(BaseModel):
    headline: str
    executive_summary: str
    observed_facts: str
    reasonable_inferences: str
    timeline_summary: str
    counter_narrative_summary: str
    limitations: str
    recommended_human_checks: str


class FinalReportResult(BaseModel):
    investigation_id: str
    plan_snapshot: InvestigationPlan
    report_title: str
    report_summary: str
    sections: FinalReportSections
    key_claims: list[FinalReportClaim] = Field(default_factory=list)
    evidence_packet: list[ReportCitation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommended_human_checks: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: ReportConfidenceLabel
    cached: bool = False


class FinalReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_refresh: bool = False


class InvestigationWorkspace(BaseModel):
    investigation_id: str
    query_text: str
    status: InvestigationStatus
    current_stage: InvestigationStage
    created_at: datetime
    updated_at: datetime
    plan: InvestigationPlan | None = None
    retrieval: RetrievalResult | None = None
    retrieved_documents: list[Document] = Field(default_factory=list)
    source_diversity: SourceDiversityResult | None = None
    timeline: TimelineResult | None = None
    counter_narratives: CounterNarrativeResult | None = None
    narrative_family: NarrativeFamilyResult | None = None
    analyst: AnalystResult | None = None
    claim_counterpoints: ClaimCounterpointResult | None = None
    receipts: ReceiptsResult | None = None
    agent_debate: AgentDebateResult | None = None
    report: FinalReportResult | None = None
