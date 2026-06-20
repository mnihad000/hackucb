# RhetoriQ Data Schema

**Document purpose:** Define the core data objects used across RhetoriQ.  
**Audience:** backend engineers, frontend engineers, AI agents, sponsor integration agents, and future contributors.  
**Related docs:** `HACKATHON_MVP_SPEC.md`, `FEATURES.md`

---

## 1. Schema Philosophy

RhetoriQ depends on many connected concepts:

- documents
- sources
- narratives
- narrative families
- counter-narratives
- timelines
- graphs
- source diversity
- agent debates
- reports
- receipts

This file defines the shared data model so the frontend, backend, Redis layer, AI agents, and demo dataset all use the same language.

The most important rule:

> Every AI-generated claim in RhetoriQ should be traceable back to evidence through receipts.

---

## 2. Core Object Overview

| Object | Purpose |
|---|---|
| `Source` | Represents the outlet, platform, organization, speaker, or origin that produced a document |
| `Document` | Represents one article, post, transcript, speech segment, RSS item, or source artifact |
| `NarrativeCluster` | A group of documents that express the same or similar narrative |
| `NarrativeFamily` | A parent-level narrative frame containing related child narratives |
| `CounterNarrative` | An opposing or competing frame connected to a narrative cluster |
| `InvestigationQuery` | The user prompt or live spike that starts an investigation |
| `InvestigationPlan` | The AI-generated plan for how to investigate a query |
| `TimelineEvent` | One chronological event in a narrative’s spread |
| `GraphNode` | A node in the narrative spread graph |
| `GraphEdge` | A relationship between two graph nodes |
| `SourceDiversityPanel` | Summary of source type, ideological, institutional, geographic, and content diversity |
| `AgentRun` | A single agent’s contribution to the investigation |
| `AgentDebate` | Structured debate between agents before final report |
| `Receipt` | Evidence supporting a specific report claim |
| `ReportClaim` | One major claim in the final report |
| `InvestigationReport` | Final source-grounded output shown to the user |

---

## 3. Global Conventions

## 3.1 ID Conventions

Use predictable prefixes:

```text
src_        Source
doc_        Document
cluster_    NarrativeCluster
family_     NarrativeFamily
counter_    CounterNarrative
query_      InvestigationQuery
plan_       InvestigationPlan
event_      TimelineEvent
node_       GraphNode
edge_       GraphEdge
diversity_  SourceDiversityPanel
agent_      AgentRun
debate_     AgentDebate
claim_      ReportClaim
receipt_    Receipt
report_     InvestigationReport
```

Example:

```json
{
  "id": "doc_001"
}
```

## 3.2 Timestamp Conventions

All timestamps should be ISO 8601 strings.

Example:

```json
"published_at": "2026-06-20T09:14:00Z"
```

Use UTC internally when possible.

Display local time in the frontend if needed.

## 3.3 Confidence Conventions

Confidence should use both numeric and label formats.

```json
{
  "confidence_score": 0.71,
  "confidence_label": "medium"
}
```

Allowed confidence labels:

```text
low
medium
high
unknown
```

## 3.4 Source Link Conventions

If a source has a URL, store it as `url`.

All user-visible evidence links should be clickable.

```json
{
  "url": "https://example.com/article"
}
```

## 3.5 Safety Language Conventions

Use cautious labels:

```text
first_observed
signals
consistent_with
possible
likely
uncertain
requires_human_review
```

Avoid definitive labels unless directly supported:

```text
proven
confirmed_fake
definitely_astroturfed
propaganda
truth_score
```

---

## 4. Enums

## 4.1 `SourceType`

```ts
type SourceType =
  | "national_news"
  | "local_news"
  | "international_news"
  | "community_post"
  | "social_media"
  | "blog"
  | "newsletter"
  | "official_statement"
  | "speech"
  | "transcript"
  | "hearing"
  | "press_release"
  | "think_tank"
  | "advocacy_group"
  | "campaign"
  | "podcast"
  | "video"
  | "other"
  | "unknown";
```

## 4.2 `IdeologyLabel`

Use only if available from known metadata or a clearly labeled dataset. Do not invent ideological labels without source support.

```ts
type IdeologyLabel =
  | "left"
  | "center_left"
  | "center"
  | "center_right"
  | "right"
  | "mixed"
  | "unknown";
```

## 4.3 `InstitutionType`

```ts
type InstitutionType =
  | "official"
  | "unofficial"
  | "independent"
  | "advocacy"
  | "campaign"
  | "media"
  | "community"
  | "academic"
  | "corporate"
  | "unknown";
```

## 4.4 `ContentType`

```ts
type ContentType =
  | "original_reporting"
  | "reposting"
  | "opinion"
  | "analysis"
  | "transcript"
  | "speech"
  | "press_release"
  | "community_post"
  | "social_post"
  | "audio_transcript"
  | "video_transcript"
  | "unknown";
```

## 4.5 `NarrativeStatus`

```ts
type NarrativeStatus =
  | "emerging"
  | "amplifying"
  | "mainstreaming"
  | "institutionalized"
  | "declining"
  | "resurfacing"
  | "unknown";
```

## 4.6 `SpreadPattern`

```ts
type SpreadPattern =
  | "grassroots"
  | "reactive_amplification"
  | "top_down"
  | "influencer_driven"
  | "media_driven"
  | "official_to_media"
  | "community_to_media"
  | "potentially_coordinated"
  | "insufficient_evidence"
  | "unknown";
```

## 4.7 `ClaimSupportStatus`

```ts
type ClaimSupportStatus =
  | "supported"
  | "partially_supported"
  | "unsupported"
  | "contradicted"
  | "needs_human_review";
```

## 4.8 `AgentRole`

```ts
type AgentRole =
  | "radar_agent"
  | "query_planner_agent"
  | "retriever_agent"
  | "timeline_agent"
  | "graph_agent"
  | "narrative_family_agent"
  | "counter_narrative_agent"
  | "source_diversity_agent"
  | "analyst_agent"
  | "skeptic_agent"
  | "receipts_agent"
  | "safety_grounding_agent";
```

---

## 5. Source

A `Source` represents the entity or platform that produced a document.

Examples:

- news outlet
- local blog
- official government office
- advocacy group
- community forum
- public speech source
- transcript provider

### TypeScript Shape

```ts
interface Source {
  id: string;
  name: string;
  source_type: SourceType;
  homepage_url?: string;
  ideology_label?: IdeologyLabel;
  institution_type?: InstitutionType;
  geographic_scope?: "local" | "state" | "national" | "international" | "unknown";
  country?: string;
  region?: string;
  city?: string;
  description?: string;
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "src_001",
  "name": "Local Energy Watch",
  "source_type": "blog",
  "homepage_url": "https://example.com",
  "ideology_label": "unknown",
  "institution_type": "independent",
  "geographic_scope": "local",
  "country": "US",
  "region": "California",
  "city": "Sacramento",
  "description": "Local blog covering state energy politics.",
  "metadata": {
    "manually_labeled": true
  }
}
```

---

## 6. Document

A `Document` represents one article, post, transcript, speech segment, RSS item, or source artifact.

### TypeScript Shape

```ts
interface Document {
  id: string;
  source_id: string;
  source_name: string;
  source_type: SourceType;
  title: string;
  url?: string;
  author?: string;
  published_at: string;
  collected_at?: string;
  text: string;
  snippet?: string;
  language?: string;
  content_type?: ContentType;
  ideology_label?: IdeologyLabel;
  geographic_scope?: "local" | "state" | "national" | "international" | "unknown";
  entities: string[];
  phrases: string[];
  claims?: string[];
  embedding_id?: string;
  duplicate_of_doc_id?: string | null;
  is_seeded_demo_data?: boolean;
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "doc_001",
  "source_id": "src_001",
  "source_name": "Local Energy Watch",
  "source_type": "blog",
  "title": "New Energy Rule Could Raise Household Costs",
  "url": "https://example.com/local-energy-watch",
  "author": "Staff Writer",
  "published_at": "2026-06-20T09:14:00Z",
  "collected_at": "2026-06-20T09:20:00Z",
  "text": "Critics are calling the proposal a hidden energy tax on working families...",
  "snippet": "Critics are calling the proposal a hidden energy tax on working families...",
  "language": "en",
  "content_type": "analysis",
  "ideology_label": "unknown",
  "geographic_scope": "local",
  "entities": ["Energy Commission", "Governor"],
  "phrases": ["hidden energy tax", "working families"],
  "claims": ["The policy could raise household energy costs."],
  "embedding_id": "embedding_doc_001",
  "duplicate_of_doc_id": null,
  "is_seeded_demo_data": true,
  "metadata": {
    "demo_cluster": "hidden_energy_tax"
  }
}
```

---

## 7. InvestigationQuery

An `InvestigationQuery` represents the event that starts an investigation.

It can come from:

- user prompt
- live spike
- clicked narrative card
- uploaded transcript
- browser extension in the future

### TypeScript Shape

```ts
interface InvestigationQuery {
  id: string;
  query_text: string;
  query_type: "user_prompt" | "live_spike" | "clicked_narrative" | "uploaded_content" | "unknown";
  created_at: string;
  user_intent?: "trace_origin" | "trace_spread" | "find_counter_narratives" | "summarize_context" | "general_investigation";
  topic?: string;
  canonical_phrase?: string;
  entities?: string[];
  requested_outputs?: string[];
  time_window?: {
    start?: string;
    end?: string;
    label?: string;
  };
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "query_001",
  "query_text": "Where did the hidden energy tax narrative come from?",
  "query_type": "user_prompt",
  "created_at": "2026-06-20T12:00:00Z",
  "user_intent": "trace_origin",
  "topic": "energy policy",
  "canonical_phrase": "hidden energy tax",
  "entities": ["energy", "tax", "policy"],
  "requested_outputs": ["timeline", "family_tree", "counter_narratives", "source_diversity", "report", "receipts"],
  "time_window": {
    "label": "recent"
  },
  "metadata": {
    "source": "ask_rhetoriq"
  }
}
```

---

## 8. InvestigationPlan

An `InvestigationPlan` is generated by the Query Planner Agent.

It explains how RhetoriQ will investigate the query.

### TypeScript Shape

```ts
interface InvestigationPlan {
  id: string;
  query_id: string;
  generated_at: string;
  search_queries: string[];
  semantic_queries: string[];
  target_entities: string[];
  target_phrases: string[];
  source_types_to_include: SourceType[];
  investigation_steps: string[];
  expected_outputs: string[];
  safety_notes: string[];
}
```

### JSON Example

```json
{
  "id": "plan_001",
  "query_id": "query_001",
  "generated_at": "2026-06-20T12:00:05Z",
  "search_queries": [
    "\"hidden energy tax\"",
    "\"energy tax\" \"working families\"",
    "\"green mandate costs\""
  ],
  "semantic_queries": [
    "political framing around energy policy as hidden household tax",
    "counter narrative around energy policy lowering long term costs"
  ],
  "target_entities": ["Energy Commission", "Governor"],
  "target_phrases": ["hidden energy tax", "utility bill surcharge", "green mandate costs"],
  "source_types_to_include": ["blog", "local_news", "national_news", "official_statement", "transcript"],
  "investigation_steps": [
    "Retrieve related documents.",
    "Cluster main narrative and related variants.",
    "Find counter-narratives.",
    "Build chronological timeline.",
    "Build source graph.",
    "Generate report with receipts."
  ],
  "expected_outputs": ["timeline", "graph", "family_tree", "source_diversity", "report", "receipts"],
  "safety_notes": [
    "Do not claim absolute origin.",
    "Use 'first observed in our dataset'.",
    "Avoid unsupported coordination claims."
  ]
}
```

---

## 9. NarrativeCluster

A `NarrativeCluster` groups documents expressing the same or similar narrative.

### TypeScript Shape

```ts
interface NarrativeCluster {
  id: string;
  title: string;
  summary: string;
  canonical_phrase: string;
  related_phrases: string[];
  parent_family_id?: string;
  document_ids: string[];
  counter_narrative_ids?: string[];
  first_observed_doc_id?: string;
  first_observed_at?: string;
  latest_observed_at?: string;
  source_count: number;
  spike_score?: number;
  status?: NarrativeStatus;
  spread_pattern?: SpreadPattern;
  confidence_score?: number;
  confidence_label?: "low" | "medium" | "high" | "unknown";
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "cluster_001",
  "title": "Hidden Energy Tax Narrative",
  "summary": "A framing that describes an energy policy as a hidden tax on working families.",
  "canonical_phrase": "hidden energy tax",
  "related_phrases": ["utility bill surcharge", "green mandate costs", "backdoor energy tax"],
  "parent_family_id": "family_001",
  "document_ids": ["doc_001", "doc_002", "doc_003", "doc_004"],
  "counter_narrative_ids": ["counter_001"],
  "first_observed_doc_id": "doc_001",
  "first_observed_at": "2026-06-20T09:14:00Z",
  "latest_observed_at": "2026-06-20T15:30:00Z",
  "source_count": 26,
  "spike_score": 7.4,
  "status": "amplifying",
  "spread_pattern": "reactive_amplification",
  "confidence_score": 0.71,
  "confidence_label": "medium",
  "metadata": {
    "demo_primary": true
  }
}
```

---

## 10. NarrativeFamily

A `NarrativeFamily` represents a broad parent frame that contains related child narratives.

### TypeScript Shape

```ts
interface NarrativeFamily {
  id: string;
  title: string;
  summary: string;
  parent_frame: string;
  child_cluster_ids: string[];
  related_phrases: string[];
  first_observed_at?: string;
  active_cluster_id?: string;
  fastest_growing_cluster_id?: string;
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "family_001",
  "title": "Climate Policy Cost Narrative",
  "summary": "A family of narratives that frame climate or energy policy around household costs, government mandates, and affordability concerns.",
  "parent_frame": "climate policy as household cost burden",
  "child_cluster_ids": ["cluster_001", "cluster_002", "cluster_003"],
  "related_phrases": ["hidden energy tax", "gas stove ban", "green mandate costs", "war on appliances"],
  "first_observed_at": "2026-06-19T08:00:00Z",
  "active_cluster_id": "cluster_001",
  "fastest_growing_cluster_id": "cluster_001",
  "metadata": {
    "display_as_tree": true
  }
}
```

---

## 11. CounterNarrative

A `CounterNarrative` represents an opposing or competing frame.

### TypeScript Shape

```ts
interface CounterNarrative {
  id: string;
  opposes_cluster_id: string;
  title: string;
  summary: string;
  canonical_phrase?: string;
  related_phrases: string[];
  document_ids: string[];
  first_observed_doc_id?: string;
  first_observed_at?: string;
  source_count: number;
  growth_score?: number;
  confidence_score?: number;
  confidence_label?: "low" | "medium" | "high" | "unknown";
}
```

### JSON Example

```json
{
  "id": "counter_001",
  "opposes_cluster_id": "cluster_001",
  "title": "Long-Term Energy Savings Narrative",
  "summary": "A counter-frame arguing that the policy funds infrastructure and lowers long-term household energy costs.",
  "canonical_phrase": "long-term energy savings",
  "related_phrases": ["infrastructure investment", "lower future costs", "grid modernization"],
  "document_ids": ["doc_010", "doc_011", "doc_012"],
  "first_observed_doc_id": "doc_010",
  "first_observed_at": "2026-06-20T10:30:00Z",
  "source_count": 11,
  "growth_score": 3.2,
  "confidence_score": 0.68,
  "confidence_label": "medium"
}
```

---

## 12. TimelineEvent

A `TimelineEvent` represents one event in the narrative’s spread.

### TypeScript Shape

```ts
interface TimelineEvent {
  id: string;
  cluster_id: string;
  document_id: string;
  timestamp: string;
  source_name: string;
  source_type: SourceType;
  title: string;
  url?: string;
  snippet: string;
  event_type:
    | "first_observed"
    | "early_amplification"
    | "mainstream_pickup"
    | "official_mention"
    | "counter_narrative"
    | "resurfacing"
    | "other";
  narrative_side: "main" | "counter" | "related" | "unknown";
  importance_score?: number;
  explanation?: string;
}
```

### JSON Example

```json
{
  "id": "event_001",
  "cluster_id": "cluster_001",
  "document_id": "doc_001",
  "timestamp": "2026-06-20T09:14:00Z",
  "source_name": "Local Energy Watch",
  "source_type": "blog",
  "title": "New Energy Rule Could Raise Household Costs",
  "url": "https://example.com/local-energy-watch",
  "snippet": "Critics are calling the proposal a hidden energy tax on working families...",
  "event_type": "first_observed",
  "narrative_side": "main",
  "importance_score": 0.95,
  "explanation": "Earliest observed use of the canonical phrase in the dataset."
}
```

---

## 13. GraphNode

A `GraphNode` represents a node in the spread graph.

### TypeScript Shape

```ts
interface GraphNode {
  id: string;
  label: string;
  node_type:
    | "document"
    | "source"
    | "speaker"
    | "organization"
    | "narrative"
    | "narrative_family"
    | "counter_narrative"
    | "phrase"
    | "entity";
  ref_id?: string;
  source_type?: SourceType;
  timestamp?: string;
  url?: string;
  snippet?: string;
  importance_score?: number;
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "node_doc_001",
  "label": "Local Energy Watch",
  "node_type": "document",
  "ref_id": "doc_001",
  "source_type": "blog",
  "timestamp": "2026-06-20T09:14:00Z",
  "url": "https://example.com/local-energy-watch",
  "snippet": "Critics are calling the proposal a hidden energy tax...",
  "importance_score": 0.95,
  "metadata": {
    "is_first_observed": true
  }
}
```

---

## 14. GraphEdge

A `GraphEdge` represents a relationship between graph nodes.

### TypeScript Shape

```ts
interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type:
    | "semantic_similarity"
    | "exact_phrase_reuse"
    | "shared_entity"
    | "source_link"
    | "reposting"
    | "quote_reuse"
    | "temporal_sequence"
    | "counter_narrative_relationship"
    | "family_child_relationship";
  weight?: number;
  evidence_text?: string;
  receipt_ids?: string[];
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "edge_001",
  "source_node_id": "node_doc_001",
  "target_node_id": "node_doc_002",
  "edge_type": "exact_phrase_reuse",
  "weight": 0.82,
  "evidence_text": "Both documents use the phrase 'hidden energy tax on working families'.",
  "receipt_ids": ["receipt_001", "receipt_002"],
  "metadata": {
    "time_delta_minutes": 48
  }
}
```

---

## 15. SourceDiversityPanel

A `SourceDiversityPanel` summarizes what kinds of sources are involved.

It should provide context, not truth judgment.

### TypeScript Shape

```ts
interface SourceDiversityPanel {
  id: string;
  cluster_id: string;
  generated_at: string;
  total_sources: number;
  ideology_distribution?: Record<IdeologyLabel, number>;
  geographic_distribution?: {
    local: number;
    state: number;
    national: number;
    international: number;
    unknown: number;
  };
  institutional_distribution?: Record<InstitutionType, number>;
  content_type_distribution?: Record<ContentType, number>;
  source_type_distribution?: Record<SourceType, number>;
  original_vs_repost?: {
    original_reporting: number;
    reposting_or_reuse: number;
    unknown: number;
  };
  notes: string[];
  limitations: string[];
}
```

### JSON Example

```json
{
  "id": "diversity_001",
  "cluster_id": "cluster_001",
  "generated_at": "2026-06-20T12:10:00Z",
  "total_sources": 26,
  "ideology_distribution": {
    "left": 4,
    "center": 6,
    "right": 7,
    "unknown": 9
  },
  "geographic_distribution": {
    "local": 8,
    "state": 2,
    "national": 10,
    "international": 1,
    "unknown": 5
  },
  "institutional_distribution": {
    "official": 3,
    "unofficial": 9,
    "independent": 5,
    "advocacy": 4,
    "media": 5,
    "unknown": 0
  },
  "content_type_distribution": {
    "original_reporting": 6,
    "reposting": 9,
    "opinion": 5,
    "transcript": 2,
    "community_post": 4
  },
  "source_type_distribution": {
    "blog": 4,
    "local_news": 8,
    "national_news": 6,
    "official_statement": 3,
    "community_post": 5
  },
  "original_vs_repost": {
    "original_reporting": 6,
    "reposting_or_reuse": 9,
    "unknown": 11
  },
  "notes": [
    "The narrative appears across both local and national sources.",
    "Several sources use similar wording, but shared wording alone does not prove coordination."
  ],
  "limitations": [
    "Ideology labels may be incomplete or unavailable.",
    "Source diversity describes the dataset, not the entire media ecosystem."
  ]
}
```

---

## 16. AgentRun

An `AgentRun` captures one agent’s contribution.

### TypeScript Shape

```ts
interface AgentRun {
  id: string;
  report_id?: string;
  query_id: string;
  agent_role: AgentRole;
  started_at: string;
  completed_at?: string;
  status: "pending" | "running" | "completed" | "failed";
  input_summary: string;
  output_summary?: string;
  output_json?: Record<string, unknown>;
  cited_document_ids?: string[];
  cited_receipt_ids?: string[];
  errors?: string[];
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "agent_001",
  "query_id": "query_001",
  "agent_role": "skeptic_agent",
  "started_at": "2026-06-20T12:08:00Z",
  "completed_at": "2026-06-20T12:08:12Z",
  "status": "completed",
  "input_summary": "Review analyst draft for overclaims.",
  "output_summary": "The phrase reuse evidence is real, but the report should not claim definitive coordination.",
  "output_json": {
    "overclaims_found": [
      "The draft says the narrative was coordinated. Evidence only supports signals consistent with coordination."
    ],
    "recommended_revisions": [
      "Change 'coordinated campaign' to 'signals consistent with coordinated amplification'."
    ]
  },
  "cited_document_ids": ["doc_001", "doc_002", "doc_003"],
  "cited_receipt_ids": ["receipt_001", "receipt_002"],
  "errors": [],
  "metadata": {
    "model": "claude"
  }
}
```

---

## 17. AgentDebate

An `AgentDebate` stores the structured debate before final report generation.

### TypeScript Shape

```ts
interface AgentDebate {
  id: string;
  query_id: string;
  cluster_id: string;
  report_id?: string;
  generated_at: string;
  analyst_position: string;
  skeptic_response: string;
  receipts_check: string;
  counter_narrative_note?: string;
  safety_grounding_decision: string;
  final_language_decision: string;
  rejected_claims: string[];
  softened_claims: string[];
  required_receipt_ids: string[];
}
```

### JSON Example

```json
{
  "id": "debate_001",
  "query_id": "query_001",
  "cluster_id": "cluster_001",
  "report_id": "report_001",
  "generated_at": "2026-06-20T12:09:00Z",
  "analyst_position": "The short time window and repeated phrase reuse may indicate coordinated amplification.",
  "skeptic_response": "The evidence is not strong enough to claim coordination. Shared wording could come from a public press release or common reaction.",
  "receipts_check": "Three claims are supported by receipts. One claim about intent is unsupported and should be removed.",
  "counter_narrative_note": "A counter-narrative about long-term energy savings appeared shortly after the main narrative.",
  "safety_grounding_decision": "Avoid definitive accusations. Use cautious language.",
  "final_language_decision": "Use 'signals consistent with coordinated amplification' instead of 'coordinated campaign'.",
  "rejected_claims": [
    "The narrative was intentionally coordinated by specific actors."
  ],
  "softened_claims": [
    "The spread pattern shows signals consistent with coordinated amplification."
  ],
  "required_receipt_ids": ["receipt_001", "receipt_002", "receipt_003"]
}
```

---

## 18. ReportClaim

A `ReportClaim` is one major claim in the final report.

Each major claim should have at least one receipt.

### TypeScript Shape

```ts
interface ReportClaim {
  id: string;
  report_id: string;
  claim_text: string;
  claim_type:
    | "observed_fact"
    | "reasonable_inference"
    | "uncertainty"
    | "limitation"
    | "recommendation";
  support_status: ClaimSupportStatus;
  receipt_ids: string[];
  confidence_score?: number;
  confidence_label?: "low" | "medium" | "high" | "unknown";
}
```

### JSON Example

```json
{
  "id": "claim_001",
  "report_id": "report_001",
  "claim_text": "The phrase 'hidden energy tax' first appears in the observed dataset in a Local Energy Watch article at 9:14 AM.",
  "claim_type": "observed_fact",
  "support_status": "supported",
  "receipt_ids": ["receipt_001"],
  "confidence_score": 0.93,
  "confidence_label": "high"
}
```

---

## 19. Receipt

A `Receipt` is evidence supporting a report claim.

### TypeScript Shape

```ts
interface Receipt {
  id: string;
  claim_id: string;
  document_id: string;
  source_id: string;
  source_name: string;
  source_type: SourceType;
  title: string;
  url?: string;
  published_at: string;
  quote_or_snippet: string;
  support_reason: string;
  extracted_at?: string;
  browser_verified?: boolean;
  verification_method?: "dataset" | "browserbase" | "manual" | "unknown";
}
```

### JSON Example

```json
{
  "id": "receipt_001",
  "claim_id": "claim_001",
  "document_id": "doc_001",
  "source_id": "src_001",
  "source_name": "Local Energy Watch",
  "source_type": "blog",
  "title": "New Energy Rule Could Raise Household Costs",
  "url": "https://example.com/local-energy-watch",
  "published_at": "2026-06-20T09:14:00Z",
  "quote_or_snippet": "Critics are calling the proposal a hidden energy tax on working families...",
  "support_reason": "This is the earliest observed source in the dataset using the phrase 'hidden energy tax'.",
  "extracted_at": "2026-06-20T12:07:00Z",
  "browser_verified": true,
  "verification_method": "browserbase"
}
```

---

## 20. InvestigationReport

An `InvestigationReport` is the final user-facing output.

### TypeScript Shape

```ts
interface InvestigationReport {
  id: string;
  query_id: string;
  cluster_id: string;
  generated_at: string;
  title: string;
  user_question?: string;
  executive_summary: string;
  first_observed: {
    document_id: string;
    source_name: string;
    url?: string;
    published_at: string;
    confidence_label: "low" | "medium" | "high" | "unknown";
  };
  narrative_family_id?: string;
  counter_narrative_ids: string[];
  timeline_event_ids: string[];
  graph_node_ids: string[];
  graph_edge_ids: string[];
  source_diversity_panel_id?: string;
  agent_debate_id?: string;
  spread_pattern: SpreadPattern;
  confidence_score: number;
  confidence_label: "low" | "medium" | "high" | "unknown";
  observed_facts: string[];
  reasonable_inferences: string[];
  uncertainties: string[];
  rejected_or_unsupported_claims: string[];
  limitations: string[];
  recommended_human_checks: string[];
  claim_ids: string[];
  receipt_ids: string[];
  report_markdown?: string;
  metadata?: Record<string, unknown>;
}
```

### JSON Example

```json
{
  "id": "report_001",
  "query_id": "query_001",
  "cluster_id": "cluster_001",
  "generated_at": "2026-06-20T12:10:00Z",
  "title": "Hidden Energy Tax Narrative Investigation",
  "user_question": "Where did the hidden energy tax narrative come from?",
  "executive_summary": "In the observed dataset, the phrase 'hidden energy tax' first appears in a local energy politics blog before spreading to community posts, local news, and later national political coverage. The spread pattern is consistent with reactive amplification, but the evidence is insufficient to make a definitive coordination claim.",
  "first_observed": {
    "document_id": "doc_001",
    "source_name": "Local Energy Watch",
    "url": "https://example.com/local-energy-watch",
    "published_at": "2026-06-20T09:14:00Z",
    "confidence_label": "high"
  },
  "narrative_family_id": "family_001",
  "counter_narrative_ids": ["counter_001"],
  "timeline_event_ids": ["event_001", "event_002", "event_003"],
  "graph_node_ids": ["node_doc_001", "node_doc_002", "node_doc_003"],
  "graph_edge_ids": ["edge_001", "edge_002"],
  "source_diversity_panel_id": "diversity_001",
  "agent_debate_id": "debate_001",
  "spread_pattern": "reactive_amplification",
  "confidence_score": 0.71,
  "confidence_label": "medium",
  "observed_facts": [
    "The phrase appears in multiple sources within the observed time window.",
    "The earliest observed source in the dataset is a local blog post at 9:14 AM.",
    "A counter-narrative about long-term savings appears later in the dataset."
  ],
  "reasonable_inferences": [
    "The pattern is consistent with reactive amplification.",
    "Similar wording across sources may indicate shared framing or a common source."
  ],
  "uncertainties": [
    "Earlier sources may exist outside the dataset.",
    "Shared wording alone does not prove coordination."
  ],
  "rejected_or_unsupported_claims": [
    "The system does not claim that specific actors intentionally coordinated the narrative."
  ],
  "limitations": [
    "The dataset is incomplete.",
    "Ideology labels may be unknown or approximate.",
    "First observed does not mean true origin."
  ],
  "recommended_human_checks": [
    "Verify source timestamps.",
    "Check whether sources cite each other.",
    "Search for relevant press releases.",
    "Look for earlier deleted or archived posts."
  ],
  "claim_ids": ["claim_001", "claim_002", "claim_003"],
  "receipt_ids": ["receipt_001", "receipt_002", "receipt_003"],
  "report_markdown": "## Summary\nIn the observed dataset...",
  "metadata": {
    "model": "claude",
    "demo_primary": true
  }
}
```

---

## 21. API Response Shapes

## 21.1 `POST /api/investigate`

### Request

```json
{
  "query_text": "Where did the hidden energy tax narrative come from?"
}
```

### Response

```json
{
  "query": {
    "id": "query_001",
    "query_text": "Where did the hidden energy tax narrative come from?"
  },
  "report_id": "report_001",
  "status": "completed"
}
```

---

## 21.2 `GET /api/reports/{report_id}`

### Response

```json
{
  "report": {},
  "cluster": {},
  "family": {},
  "counter_narratives": [],
  "timeline": [],
  "graph": {
    "nodes": [],
    "edges": []
  },
  "source_diversity": {},
  "agent_debate": {},
  "claims": [],
  "receipts": []
}
```

---

## 21.3 `GET /api/narratives/trending`

### Response

```json
{
  "narratives": [
    {
      "id": "cluster_001",
      "title": "Hidden Energy Tax Narrative",
      "summary": "A framing that describes an energy policy as a hidden tax.",
      "spike_score": 7.4,
      "source_count": 26,
      "status": "amplifying",
      "first_observed_at": "2026-06-20T09:14:00Z",
      "confidence_label": "medium"
    }
  ]
}
```

---

## 21.4 `GET /api/narratives/{cluster_id}`

### Response

```json
{
  "cluster": {},
  "family": {},
  "counter_narratives": [],
  "timeline": [],
  "graph": {
    "nodes": [],
    "edges": []
  },
  "source_diversity": {}
}
```

---

## 22. Seeded Demo Dataset Requirements

The seeded dataset should include enough data to demonstrate:

- one main narrative
- one narrative family
- at least three child narratives
- at least one counter-narrative
- at least 10 documents
- at least 5 sources
- at least 1 first-observed source
- at least 1 mainstream pickup
- at least 1 official/transcript-style mention
- at least 5 receipts
- at least one agent debate

### Recommended Demo Narrative

```text
Hidden Energy Tax
```

### Recommended Narrative Family

```text
Climate Policy Cost Narrative
```

### Recommended Child Narratives

```text
hidden energy tax
utility bill surcharge
green mandate costs
war on appliances
```

### Recommended Counter-Narrative

```text
long-term energy savings / infrastructure investment
```

---

## 23. Frontend Data Needs

The frontend needs these combined objects for the main investigation page:

```ts
interface InvestigationPageData {
  report: InvestigationReport;
  query: InvestigationQuery;
  cluster: NarrativeCluster;
  family?: NarrativeFamily;
  counter_narratives: CounterNarrative[];
  timeline: TimelineEvent[];
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  source_diversity?: SourceDiversityPanel;
  agent_debate?: AgentDebate;
  claims: ReportClaim[];
  receipts: Receipt[];
  documents: Document[];
  sources: Source[];
}
```

---

## 24. Backend Storage Notes

Possible storage options:

### Redis

Use Redis for:

- vector embeddings
- semantic search
- phrase counters
- semantic cache
- prior investigation memory
- fast narrative card retrieval

### PostgreSQL or SQLite

Use relational storage for:

- documents
- sources
- reports
- claims
- receipts
- timeline events
- graph objects

### Static JSON

For the hackathon demo, it is acceptable to start with static JSON files for:

- seeded documents
- seeded timelines
- seeded graphs
- seeded source diversity panel
- seeded agent debate

Then progressively replace static data with live pipeline results.

---

## 25. Data Quality Rules

1. Every `Document` should have a source.
2. Every `TimelineEvent` should point to a document.
3. Every `ReportClaim` should have at least one receipt unless it is explicitly marked unsupported or uncertain.
4. Every `Receipt` should point to a document and source.
5. Every `InvestigationReport` should include limitations.
6. Every “origin” claim must use “first observed in our dataset.”
7. Every source diversity panel should include limitations.
8. Ideology labels should be `unknown` unless supported by metadata.
9. Do not fabricate URLs for real sources.
10. Demo URLs may use clearly fake example domains if data is synthetic.

---

## 26. Minimal JSON Bundle for Demo

If the team needs a single JSON payload for the frontend, use this shape:

```json
{
  "query": {},
  "report": {},
  "cluster": {},
  "family": {},
  "counter_narratives": [],
  "timeline": [],
  "graph": {
    "nodes": [],
    "edges": []
  },
  "source_diversity": {},
  "agent_debate": {},
  "claims": [],
  "receipts": [],
  "documents": [],
  "sources": []
}
```

This should be enough to render the entire investigation page.

---

## 27. Final Schema Checklist

Before building, confirm:

- [ ] Source schema exists.
- [ ] Document schema exists.
- [ ] InvestigationQuery schema exists.
- [ ] InvestigationPlan schema exists.
- [ ] NarrativeCluster schema exists.
- [ ] NarrativeFamily schema exists.
- [ ] CounterNarrative schema exists.
- [ ] TimelineEvent schema exists.
- [ ] GraphNode schema exists.
- [ ] GraphEdge schema exists.
- [ ] SourceDiversityPanel schema exists.
- [ ] AgentRun schema exists.
- [ ] AgentDebate schema exists.
- [ ] ReportClaim schema exists.
- [ ] Receipt schema exists.
- [ ] InvestigationReport schema exists.
- [ ] API response shapes are agreed on.
- [ ] Frontend has one combined investigation payload.
- [ ] Receipts are clickable.
- [ ] Every major claim can be traced to evidence.
