export type ExamplePrompt = {
  id: string;
  label: string;
  query: string;
};

export type InvestigationConfidence = "low" | "medium" | "high" | "unknown";

export type InvestigationStatus =
  | "emerging"
  | "amplifying"
  | "mainstreaming"
  | "declining"
  | "unknown";

export type RadarTopic = {
  id: string;
  title: string;
  summary: string;
  spike: string;
  sourceCount: number;
  firstObserved: string;
  status: string;
  sourceMix: string;
  confidence: "Low" | "Medium" | "High";
};

export type TrendingFeedState = "warming" | "ready" | "stale" | "error";

export type LiveTrendingTimelinePoint = {
  timestamp: string;
  count: number;
};

export type LiveTrendingTopic = {
  id: string;
  title: string;
  canonical_phrase: string;
  summary: string;
  related_phrases: string[];
  status: string;
  confidence_label: "Low" | "Medium" | "High";
  confidence_score: number;
  source_count: number;
  publisher_count: number;
  first_observed_at: string;
  latest_observed_at: string;
  source_diversity_snapshot: Record<string, number>;
  timeline: LiveTrendingTimelinePoint[];
  velocity_score: number;
  persistence_runs: number;
  provider_mix: Record<string, number>;
  supporting_document_ids: string[];
};

export type LiveTrendingFeed = {
  state: TrendingFeedState;
  generated_at?: string | null;
  fresh_until?: string | null;
  last_completed_run_at?: string | null;
  last_reseed_at?: string | null;
  warning?: string | null;
  topics: LiveTrendingTopic[];
};

export type LiveTrendingInvestigationResponse = {
  investigation_id: string;
  reused_existing: boolean;
  topic_id: string;
  canonical_phrase: string;
};

export type RecentInvestigation = {
  id: string;
  title: string;
  summary: string;
  updatedAt: string;
  receiptCount: number;
  focus: string;
};

export type InvestigationStub = {
  id: string;
  title: string;
  kicker: string;
  summary: string;
  status: string;
  firstObserved: string;
};

export type InvestigationReceipt = {
  id: string;
  claimId?: string;
  sourceName: string;
  title: string;
  url?: string;
  quoteOrSnippet: string;
  supportReason: string;
  browserVerified?: boolean;
};

export type InvestigationNodeSource = {
  id: string;
  name: string;
  type: string;
  title: string;
  url?: string;
  publishedAt?: string;
  snippet?: string;
  stance?: "supporting" | "opposing" | "context" | "unknown";
  counterType?: "opposing" | "corrective" | "reframing";
};

export type InvestigationNode = {
  id: string;
  label: string;
  subtitle?: string;
  nodeType:
    | "current"
    | "first_observed"
    | "amplification"
    | "media_pickup"
    | "official_mention"
    | "counter_narrative"
    | "related"
    | "uncertain";
  timestamp?: string;
  status?: InvestigationStatus;
  confidence?: InvestigationConfidence;
  sourceCount: number;
  counterSourceCount?: number;
  receiptCount?: number;
  summary?: string;
  sources?: InvestigationNodeSource[];
  receipts?: InvestigationReceipt[];
};

export type InvestigationEdge = {
  id: string;
  source: string;
  target: string;
  edgeType:
    | "temporal_sequence"
    | "exact_phrase_reuse"
    | "semantic_similarity"
    | "source_link"
    | "counter_narrative"
    | "related_context"
    | "uncertain";
  label?: string;
  evidenceText?: string;
  confidence?: InvestigationConfidence;
  animated?: boolean;
};

export type InvestigationFlowchartData = {
  title: string;
  query: string;
  currentNodeId: string;
  nodes: InvestigationNode[];
  edges: InvestigationEdge[];
};

export type NodeState =
  | "current"
  | "main"
  | "counter"
  | "related"
  | "uncertain"
  | "selected"
  | "dimmed";

export type InvestigationExperience = {
  id: string;
  title: string;
  kicker: string;
  summary: string;
  status: string;
  firstObserved: string;
  confidence: "Low" | "Medium" | "High";
  generatedAt: string;
  sourceCount: number;
  receiptCount: number;
  flowchartData: InvestigationFlowchartData;
};

export type InvestigationStage =
  | "planner"
  | "retriever"
  | "source_diversity"
  | "timeline"
  | "counter_narrative"
  | "narrative_family"
  | "analyst"
  | "claim_counterpoint"
  | "receipts"
  | "agent_debate"
  | "report";

export type InvestigationPipelineStatus =
  | "planning_completed"
  | "retrieval_completed"
  | "source_diversity_completed"
  | "timeline_completed"
  | "counter_narrative_completed"
  | "narrative_family_completed"
  | "analyst_completed"
  | "claim_counterpoint_completed"
  | "receipts_completed"
  | "agent_debate_completed"
  | "report_completed";

export type LiveInvestigationPlan = {
  query_text: string;
  topic: string;
  canonical_phrase: string | null;
  intent: string;
  entities: string[];
  search_queries: string[];
  semantic_queries: string[];
  target_source_types: string[];
  requested_outputs: string[];
  time_window: {
    start: string | null;
    end: string | null;
    label: string;
  };
  retrieval_mode: "broad" | "narrow";
  risk_notes: string[];
  uncertainty_requirements: string[];
};

export type LiveCoverageSummary = {
  total_documents: number;
  unique_sources: number;
  source_type_distribution: Record<string, number>;
  has_counter_narrative_candidates: boolean;
  has_timeline_coverage: boolean;
  exact_phrase_hits: number;
  search_rounds_completed: number;
};

export type LiveRetrievalResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  retrieved_document_ids: string[];
  high_relevance_document_ids: string[];
  main_narrative_document_ids: string[];
  counter_narrative_candidate_ids: string[];
  context_document_ids: string[];
  warnings: string[];
  coverage_summary: LiveCoverageSummary;
  evidence_coverage_confidence: InvestigationConfidence;
  cached: boolean;
};

export type LiveDocument = {
  id: string;
  source_id: string | null;
  source_name: string;
  source_type: string;
  url: string;
  title: string;
  author: string | null;
  published_at: string | null;
  collected_at: string | null;
  text: string;
  snippet: string | null;
  language: string | null;
  content_type: string | null;
  geographic_scope: string | null;
  entities: string[];
  phrases: string[];
  claims: string[] | null;
  duplicate_of_doc_id: string | null;
  is_seeded_demo_data: boolean | null;
  metadata: Record<string, unknown> | null;
  source_profile?: LiveSourceProfile | null;
};

export type LiveSourceProfile = {
  institution_kind: "official" | "media" | "advocacy" | "independent" | "community" | "unknown";
  content_form:
    | "original_reporting"
    | "reposting"
    | "opinion"
    | "transcript"
    | "community_post"
    | "unknown";
  ideology: "left" | "center" | "right" | "unknown";
  classification_method: "registry" | "heuristic" | "unknown";
  classification_confidence: "low" | "medium" | "high";
};

export type LiveSourceDiversityFinding = {
  id: string;
  label: string;
  detail: string;
};

export type LiveSourceDiversityResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  total_documents: number;
  classified_documents: number;
  source_type_distribution: Record<string, number>;
  geographic_distribution: Record<string, number>;
  institution_distribution: Record<string, number>;
  content_form_distribution: Record<string, number>;
  ideology_distribution: Record<string, number>;
  findings: LiveSourceDiversityFinding[];
  limitations: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveTimelineEvent = {
  id: string;
  document_id: string;
  timestamp: string;
  source_name: string;
  source_type: string;
  title: string;
  url: string;
  snippet: string | null;
  event_type: string;
  narrative_side: "main" | "counter" | "related" | "unknown";
  importance_score: number;
  explanation: string;
};

export type LiveTimelineResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  timeline_events: LiveTimelineEvent[];
  first_observed_doc_id: string | null;
  timeline_summary: string;
  limitations: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveCounterNarrative = {
  id: string;
  title: string;
  summary: string;
  canonical_phrase: string | null;
  related_phrases: string[];
  supporting_document_ids: string[];
  first_observed_doc_id: string | null;
  relationship_to_main_narrative: string;
  confidence_score: number;
};

export type LiveCounterNarrativeResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  counter_narratives: LiveCounterNarrative[];
  notes: string[];
  limitations: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveNarrativeFamilyChild = {
  id: string;
  title: string;
  canonical_phrase: string;
  related_phrases: string[];
  first_observed_doc_id: string | null;
  relationship_to_parent: string;
  growth_status: InvestigationStatus;
  branch_summary: string;
  supporting_document_ids: string[];
  source_count: number;
  source_type_count: number;
  source_diversity_score: number;
  growth_score: number;
};

export type LiveNarrativeFamilyResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  family_title: string;
  parent_frame: string;
  summary: string;
  child_narratives: LiveNarrativeFamilyChild[];
  fastest_growing_child: string | null;
  broadest_source_diversity_child: string | null;
  limitations: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence | "unknown";
  cached: boolean;
};

export type LiveAnalystCandidateClaim = {
  id: string;
  claim_text: string;
  claim_type: string;
  supporting_document_ids: string[];
  supporting_evidence_span_ids: string[];
  confidence_score: number;
  caveats: string[];
};

export type LiveAnalystResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  draft_report_sections: {
    executive_summary: string;
    observed_facts: string;
    reasonable_inferences: string;
    timeline_summary: string;
    counter_narrative_summary: string;
    uncertainties: string;
  };
  candidate_claims: LiveAnalystCandidateClaim[];
  limitations: string[];
  recommended_human_checks: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveReportCitation = {
  document_id: string;
  source_name: string;
  source_type: string;
  title: string;
  url: string;
  published_at: string | null;
  snippet: string | null;
  relevance_note: string;
};

export type LiveReceiptEvidence = {
  document_id: string;
  source_name: string;
  source_type: string;
  title: string;
  url: string;
  published_at: string | null;
  snippet: string | null;
  evidence_span: string;
  support_reason: string;
  matched_terms: string[];
  verification_status: "verified" | "unavailable" | "metadata_mismatch" | "pending";
};

export type LiveClaimCounterpointPair = {
  claim_id: string;
  main_claim_text: string;
  counter_claim_text: string;
  counter_type: "opposing" | "corrective" | "reframing";
  relationship_summary: string;
  supporting_document_ids: string[];
  counter_document_ids: string[];
  main_receipts: LiveReportCitation[];
  counter_receipts: LiveReportCitation[];
  confidence_score: number;
  caveats: string[];
};

export type LiveClaimCounterpointResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  pairs: LiveClaimCounterpointPair[];
  unmatched_claim_ids: string[];
  limitations: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveClaimReceiptReview = {
  claim_id: string;
  claim_text: string;
  claim_side: "main" | "counter";
  support_status:
    | "supported"
    | "partially_supported"
    | "unsupported"
    | "contradicted"
    | "insufficient_evidence";
  support_summary: string;
  supporting_receipts: LiveReceiptEvidence[];
  contradicting_receipts: LiveReceiptEvidence[];
  missing_evidence_notes: string[];
  verification_state:
    | "verified"
    | "mixed"
    | "metadata_mismatch"
    | "unavailable"
    | "pending"
    | "not_available";
  confidence_score: number;
  caveats: string[];
};

export type LiveReceiptsResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  claim_receipts: LiveClaimReceiptReview[];
  counter_claim_receipts: LiveClaimReceiptReview[];
  limitations: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveSoftenedClaim = {
  claim_id: string;
  original: string;
  softened: string;
  reason: string;
};

export type LiveAgentDebateResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  analyst_position: string;
  skeptic_response: string;
  receipts_check: string;
  counter_narrative_note: string;
  safety_grounding_decision: string;
  final_language_decision: string;
  rejected_claims: string[];
  softened_claims: LiveSoftenedClaim[];
  limitations: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveFinalReportClaim = {
  claim_id: string;
  claim_text: string;
  claim_type: string;
  confidence_score: number;
  caveats: string[];
  citations: LiveReportCitation[];
  support_status:
    | "supported"
    | "partially_supported"
    | "unsupported"
    | "contradicted"
    | "insufficient_evidence"
    | null;
  support_summary: string | null;
  supporting_receipts: LiveReceiptEvidence[];
  contradicting_receipts: LiveReceiptEvidence[];
  missing_evidence_notes: string[];
  verification_state:
    | "verified"
    | "mixed"
    | "metadata_mismatch"
    | "unavailable"
    | "pending"
    | "not_available"
    | null;
  counterpoint_summary: string | null;
  counterpoint_type: "opposing" | "corrective" | "reframing" | null;
  counter_citations: LiveReportCitation[];
};

export type LiveFinalReportResult = {
  investigation_id: string;
  plan_snapshot: LiveInvestigationPlan;
  report_title: string;
  report_summary: string;
  sections: {
    headline: string;
    executive_summary: string;
    observed_facts: string;
    reasonable_inferences: string;
    timeline_summary: string;
    counter_narrative_summary: string;
    limitations: string;
    recommended_human_checks: string;
  };
  key_claims: LiveFinalReportClaim[];
  evidence_packet: LiveReportCitation[];
  limitations: string[];
  recommended_human_checks: string[];
  confidence_score: number;
  confidence_label: InvestigationConfidence;
  cached: boolean;
};

export type LiveInvestigationWorkspace = {
  investigation_id: string;
  query_text: string;
  status: InvestigationPipelineStatus;
  current_stage: InvestigationStage;
  created_at: string;
  updated_at: string;
  plan: LiveInvestigationPlan | null;
  retrieval: LiveRetrievalResult | null;
  retrieved_documents: LiveDocument[];
  source_diversity: LiveSourceDiversityResult | null;
  timeline: LiveTimelineResult | null;
  counter_narratives: LiveCounterNarrativeResult | null;
  narrative_family: LiveNarrativeFamilyResult | null;
  analyst: LiveAnalystResult | null;
  claim_counterpoints: LiveClaimCounterpointResult | null;
  receipts: LiveReceiptsResult | null;
  agent_debate: LiveAgentDebateResult | null;
  report: LiveFinalReportResult | null;
};
