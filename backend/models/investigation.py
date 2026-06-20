from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from models.document import Document


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
    "timeline_completed",
    "counter_narrative_completed",
    "analyst_completed",
    "report_completed",
]
InvestigationStage = Literal["planner", "retriever", "timeline", "counter_narrative", "analyst", "report"]
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
ClaimType = Literal["observed_fact", "inference", "uncertainty", "limitation", "recommendation"]
AnalystConfidenceLabel = Literal["low", "medium", "high"]
ReportConfidenceLabel = Literal["low", "medium", "high"]


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


class FinalReportClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    confidence_score: float = Field(ge=0.0, le=1.0)
    caveats: list[str] = Field(default_factory=list)
    citations: list[ReportCitation] = Field(default_factory=list)


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
    timeline: TimelineResult | None = None
    counter_narratives: CounterNarrativeResult | None = None
    analyst: AnalystResult | None = None
    report: FinalReportResult | None = None
