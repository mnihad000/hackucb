# Building Investigation Agents

## Purpose

This document is the source of truth for the backend investigation-agent architecture.
It is an implementation spec, not a product pitch.

The backend agents are the heart of the system and must be built as a typed evidence workflow, not as freeform chatbots.

Core principle:

- Agents produce structured artifacts.
- No agent is allowed to publish truth claims directly.
- Final backend outputs must be grounded in retrieved evidence and validated receipts.

The target backbone still uses these 8 named investigation stages, but not every stage should be LLM-backed.
The current backend already implements the first 4 stages, and stages 3 and 4 are intentionally deterministic evidence services.

Named backbone stages:

1. `Query Planner Agent`
2. `Retriever Agent`
3. `Timeline Stage`
4. `Counter-Narrative Agent`
5. `Source Diversity Agent`
6. `Analyst Agent`
7. `Skeptic Agent`
8. `Receipts Agent`

Safety and grounding are not a separate ninth agent in this version. They are enforced through shared validation rules, claim review, receipt coverage, and final publication gates.

## Current Implementation Status

Implemented now:

- shared investigation schemas in `backend/models/investigation.py`
- persisted investigation repository in `backend/services/investigation_repository.py`
- `Query Planner Agent` via `POST /api/investigate`
- `Retriever Agent` via `POST /api/investigations/{id}/retrieve`
- deterministic `Timeline Module` via `POST /api/investigations/{id}/timeline`
- deterministic `Counter-Narrative Stage` via `POST /api/investigations/{id}/counter-narratives`
- deterministic `Analyst Stage` via `POST /api/investigations/{id}/analyst`
- deterministic `Final Report Assembly` via `POST /api/investigations/{id}/report`
- cached artifact persistence for plans, retrieval results, retrieved documents, timeline results, counter-narrative results, analyst results, and final report results

Deferred or not needed for the current MVP path:

- `Source Diversity Agent`
- `Skeptic Agent`
- `Receipts Agent`

Important current decision:

- The original stage-3 slot was called `Timeline Agent`.
- In the real backend this is now a deterministic `Timeline Module`, which is the correct design for chronology reconstruction unless later evidence shows an LLM is truly needed for a narrow subtask.

## Core Backend Philosophy

The investigation backend should follow these rules:

1. Retrieval-first, never opinion-first.
2. Deterministic logic before LLM logic.
3. Every important output must be traceable to document IDs and evidence spans.
4. Final report-like output must be assembled from supported claims, not raw model prose.
5. Agent prompts are only one layer of the system. Robustness comes from contracts, validators, retries, fallbacks, provenance, and review loops.

Practical implications:

- A strong prompt alone is not enough.
- Every agent needs strict input and output contracts.
- Every stage should persist artifacts so failures are auditable.
- The system should prefer "insufficient evidence" over a polished hallucination.
- The report is not the source of truth. The claim graph and its evidence links are the source of truth.

## System Architecture

The backend should be organized into three layers.

### 1. Evidence Layer

This layer stores and normalizes the raw material used by every investigation.

It includes:

- raw documents
- normalized source records
- timestamps
- extracted snippets and evidence spans
- embeddings
- verification status
- entity and phrase extraction
- duplicate and near-duplicate markers

Responsibilities:

- preserve original metadata
- preserve URLs exactly
- store source provenance
- expose deterministic retrieval primitives
- never let downstream agents operate on untraceable text blobs

### 2. Investigation Layer

This layer runs the agent workflow and persists every intermediate artifact.

It includes:

- orchestration or state machine logic
- per-agent artifacts
- retries
- audit logs
- caching
- evaluation hooks
- review and publication gating

Responsibilities:

- run the investigation pipeline in the correct order
- parallelize independent branches where safe
- retry or repair invalid agent outputs
- store raw output plus validated output
- prevent unsupported claims from reaching the final report

### 3. Presentation Layer

This layer turns validated investigation artifacts into UI-ready payloads.

It includes:

- timeline
- counter-narratives
- source diversity
- claims
- receipts
- final report summary
- agent debate summary

Responsibilities:

- render approved artifacts
- preserve links and citations
- show limitations and uncertainty
- avoid re-reasoning at render time

### Canonical Pipeline

The original full pipeline idea was:

`User Query -> Planner -> Retriever -> Timeline / Counter-Narrative / Source Diversity (parallel) -> Analyst -> Skeptic -> Receipts -> Final Report Assembly`

Notes:

- `Final Report Assembly` is a backend composition stage, not one of the 8 core AI agents.
- Graph and family tree can be added later as deterministic or hybrid modules without changing the first 8-agent backbone.
- The current live MVP pipeline is: `User Query -> Planner -> Retriever -> Timeline Module -> Counter-Narrative Stage -> Analyst Stage -> Final Report Assembly`.
- The current persisted investigation artifacts are: `InvestigationPlan`, `RetrievalResult`, retrieved `Document[]`, `TimelineResult`, `CounterNarrativeResult`, `AnalystResult`, and `FinalReportResult`.
- `Source Diversity`, `Skeptic`, and `Receipts` are currently deferred rather than required for the MVP backend.

## Shared Data Contracts

All agents must read and write typed artifacts. Unknown fields should stay `unknown`; they must not be guessed.

Claims must always include `claim_type`.
Every claim must track `supporting_document_ids`.
Origin language must always use `first observed in our dataset`.

### `Document`

Purpose:
- canonical normalized unit of evidence

Required fields:
- `id`
- `source_id`
- `source_name`
- `source_type`
- `title`
- `url`
- `published_at`
- `text`
- `snippet`
- `phrases`
- `entities`
- `verification_status`

Produced by:
- ingestion and normalization services

Consumed by:
- Retriever, Timeline, Counter-Narrative, Source Diversity, Analyst, Skeptic, Receipts

### `Source`

Purpose:
- canonical metadata record for an outlet, account, site, institution, or originating source

Required fields:
- `id`
- `name`
- `source_type`
- `geographic_scope`
- `institutional_type`
- `ideology_label`
- `content_types_seen`
- `reliability_notes`

Produced by:
- ingestion or enrichment services

Consumed by:
- Retriever, Source Diversity, Analyst, Receipts

### `InvestigationPlan`

Purpose:
- machine-readable plan that defines what the investigation should retrieve and answer

Required fields:
- `query_text`
- `topic`
- `canonical_phrase`
- `intent`
- `entities`
- `search_queries`
- `semantic_queries`
- `target_source_types`
- `requested_outputs`
- `time_window`
- `retrieval_mode`
- `risk_notes`
- `uncertainty_requirements`

Produced by:
- Query Planner Agent

Consumed by:
- Retriever, Analyst

### `TimelineEvent`

Purpose:
- normalized event in the narrative spread chronology

Required fields:
- `id`
- `document_id`
- `timestamp`
- `event_type`
- `narrative_side`
- `importance_score`
- `explanation`

Produced by:
- Timeline Agent

Consumed by:
- Analyst, Skeptic, final report assembly

### `CounterNarrative`

Purpose:
- structured representation of a competing or opposing frame

Required fields:
- `id`
- `title`
- `summary`
- `canonical_phrase`
- `related_phrases`
- `supporting_document_ids`
- `first_observed_doc_id`
- `relationship_to_main_narrative`
- `confidence_score`

Produced by:
- Counter-Narrative Agent

Consumed by:
- Analyst, Skeptic, final report assembly

### `SourceDiversitySummary`

Purpose:
- structured ecosystem summary of the sources involved in an investigation

Required fields:
- `total_sources`
- `source_type_distribution`
- `geographic_distribution`
- `institutional_distribution`
- `content_type_distribution`
- `ideology_distribution`
- `notes`
- `limitations`

Produced by:
- Source Diversity Agent

Consumed by:
- Analyst, Skeptic, final report assembly

### `CandidateClaim`

Purpose:
- draft claim produced during synthesis before review

Required fields:
- `id`
- `claim_text`
- `claim_type`
- `supporting_document_ids`
- `supporting_evidence_span_ids`
- `confidence_score`
- `caveats`

Produced by:
- Analyst Agent

Consumed by:
- Skeptic, Receipts

### `ReviewedClaim`

Purpose:
- post-skeptic claim state used for receipt mapping and final assembly

Required fields:
- `id`
- `claim_text`
- `claim_type`
- `review_status`
- `supporting_document_ids`
- `supporting_evidence_span_ids`
- `confidence_score`
- `caveats`
- `skeptic_notes`

Produced by:
- Skeptic Agent

Consumed by:
- Receipts, final report assembly

### `Receipt`

Purpose:
- claim-to-evidence mapping object used to justify a single surviving claim

Required fields:
- `id`
- `claim_id`
- `document_id`
- `source_id`
- `source_name`
- `url`
- `published_at`
- `source_type`
- `quote_or_snippet`
- `support_reason`
- `support_status`

Produced by:
- Receipts Agent

Consumed by:
- final report assembly, UI

### `AgentRun`

Purpose:
- audit record for a single agent execution

Required fields:
- `run_id`
- `investigation_id`
- `agent_name`
- `status`
- `input_ref`
- `output_ref`
- `model_name`
- `prompt_version`
- `started_at`
- `completed_at`
- `warnings`
- `retry_count`

Produced by:
- orchestration layer

Consumed by:
- observability, debugging, evaluation

### `InvestigationState`

Purpose:
- top-level state object for a full investigation

Required fields:
- `investigation_id`
- `query_text`
- `status`
- `current_stage`
- `completed_stages`
- `failed_stages`
- `artifact_refs`
- `publish_ready`

Produced by:
- orchestration layer

Consumed by:
- API, UI, monitoring

## Deterministic Services vs AI Agents

Do not over-agentize the stack.

Some tasks should remain deterministic modules because they are more reliable, easier to test, and cheaper to run.

### Deterministic Modules

These should be implemented as backend services, not conversational agents:

- ingestion
- deduplication
- timestamp sorting
- lexical retrieval
- vector retrieval
- reranking
- edge and rule computation
- receipt linking by IDs
- schema validation
- confidence band normalization
- URL preservation
- provenance storage
- timeline ordering
- timeline event labeling when the rule set is explicit and testable

### AI Agents

These are appropriate uses of LLM-backed agents:

- planning
- interpretation of spread
- counter-framing analysis
- source ecosystem interpretation
- synthesis
- skepticism
- claim-to-evidence reasoning

Guideline:

- If a task can be expressed as "count, sort, filter, dedupe, normalize, validate", do it deterministically.
- If a task requires "interpret, compare framing, synthesize, critique language, reason about ambiguous evidence", use an agent.

## The 8 Agents

Each agent must expose the same engineering surface:

- `Purpose`
- `Inputs`
- `Processing Logic`
- `Output Contract`
- `Validation Rules`
- `Failure Modes`
- `Build Notes`

## 1. Query Planner Agent

Status:
- implemented

### Purpose

- Convert a natural-language user question into a structured investigation plan.
- Never answer the user directly.

### Inputs

- raw user query
- optional prior investigation context
- optional known entities and topics

### Processing Logic

1. Parse the query and classify intent:
   - `origin`
   - `spread`
   - `counter-narrative`
   - `source-ecosystem`
   - `general investigation`
2. Extract canonical phrase if present.
3. Extract entities, time windows, and target source types.
4. Generate lexical search queries.
5. Generate semantic retrieval queries.
6. Generate output requirements for downstream agents.
7. Generate safety notes and uncertainty requirements.
8. Decide retrieval breadth:
   - `broad` when the topic is ambiguous, emerging, or new
   - `narrow` when the investigation targets a known cluster with usable prior memory

### Output Contract

Return an `InvestigationPlan` with:

- `query_text`
- `topic`
- `canonical_phrase`
- `intent`
- `entities`
- `search_queries`
- `semantic_queries`
- `target_source_types`
- `requested_outputs`
- `time_window`
- `retrieval_mode`
- `risk_notes`
- `uncertainty_requirements`

### Validation Rules

- Must not include factual conclusions.
- Must not speculate about origin or coordination.
- Must return machine-readable plan data only.
- If phrase extraction is uncertain, the plan must say so explicitly.

### Failure Modes

- ambiguous query
- no canonical phrase
- over-narrow retrieval plan
- planner answers instead of planning

### Build Notes

- Start with a strict schema and fixture-driven tests.
- Add query rewrite tests before connecting to live retrieval.
- Reject outputs that contain user-facing conclusions.
- Current state:
  - implemented in `backend/agents/planner_agent.py`
  - request and response contract is live on `POST /api/investigate`
  - persisted artifact is `InvestigationPlan`

## 2. Retriever Agent

Status:
- implemented

### Purpose

- Assemble the best evidence packet for the investigation.

### Inputs

- `InvestigationPlan`
- document store
- vector index
- keyword index
- optional prior investigations

### Processing Logic

1. Run lexical retrieval using search queries.
2. Run semantic retrieval using semantic queries.
3. Merge candidate sets.
4. Rerank by narrative relevance, not raw keyword overlap alone.
5. Deduplicate near-identical documents.
6. Ensure inclusion of:
   - main narrative candidates
   - counter-narrative candidates
   - source diversity context documents
   - early and first-observed timeline candidates
7. Preserve source metadata, IDs, and URLs exactly.
8. Surface gaps in evidence coverage.

### Output Contract

Return:

- `retrieved_document_ids`
- `high_relevance_document_ids`
- `possible_duplicate_pairs`
- `retrieval_notes`
- `warnings`
- `evidence_coverage_confidence`

### Validation Rules

- No fabricated documents.
- No rewritten timestamps.
- No dropped or altered URLs.
- Incomplete coverage must be marked explicitly.

### Failure Modes

- too many same-source duplicates
- counter-narratives absent because retrieval is too narrow
- high lexical relevance but low narrative relevance
- timeline coverage too shallow for first-observed analysis

### Build Notes

- Keep this agent tool-heavy and LLM-light.
- Use heuristics, retrieval scoring, and reranking first.
- Use an LLM only for marginal selection or explanation tasks.
- Current state:
  - implemented in `backend/agents/retriever_agent.py`
  - uses provider-agnostic search, HTTP fetch, deterministic normalization, scoring, dedupe, and persistence
  - persisted artifact is `RetrievalResult`

## 3. Timeline Stage

Status:
- implemented as deterministic module, not AI agent

### Purpose

- Reconstruct how the narrative appears and spreads over time.

### Inputs

- retrieved documents
- timestamps
- phrase matches
- entity matches
- optional narrative cluster hints

### Processing Logic

1. Sort documents by timestamp.
2. Identify the earliest observed occurrence in the retrieved dataset.
3. Label key events where supported:
   - `first_observed`
   - `early_amplification`
   - `broader_pickup`
   - `official_mention`
   - `resurfacing`
   - `counter_narrative_entry`
4. Attach evidence-grounded explanations for each event.
5. Downgrade confidence when timestamps are missing, fuzzy, or conflicting.
6. Record limitations when chronology is incomplete.

### Output Contract

Return:

- ordered `TimelineEvent[]`
- `first_observed_doc_id`
- `timeline_summary`
- `limitations`
- `confidence_score`

### Validation Rules

- Must always use `first observed in our dataset`.
- Must never claim true origin.
- Must not invent chronology from weak or incomplete evidence.

### Failure Modes

- missing timestamps
- multiple near-identical earliest docs
- false chronology caused by publication-date noise
- event labels that rely on guesswork instead of timestamps

### Build Notes

- Keep ordering deterministic.
- Do not use an LLM unless the deterministic rules become demonstrably insufficient.
- Add tests for timestamp ties and missing timestamp behavior.
- Current state:
  - implemented in `backend/services/timeline_builder.py`
  - request and response contract is live on `POST /api/investigations/{id}/timeline`
  - persisted artifact is `TimelineResult`
  - current logic is fully deterministic and cached

## 4. Counter-Narrative Agent

Status:
- implemented as deterministic evidence stage

### Purpose

- Identify competing or opposing frames around the same issue.

### Inputs

- main narrative phrase or topic
- retrieved documents
- phrase overlap
- entity overlap
- stance candidates

### Processing Logic

1. Bucket same-topic documents into:
   - supportive
   - opposing
   - reframing
   - neutral context
2. Identify opposing phrases and alternative frames.
3. Group counter-documents into one or more counter-narratives.
4. Estimate first observed timing and source count for each counter-frame.
5. Summarize the relationship to the main narrative without judging truth.

### Output Contract

Return `CounterNarrative[]` containing:

- `id`
- `title`
- `summary`
- `canonical_phrase`
- `related_phrases`
- `supporting_document_ids`
- `first_observed_doc_id`
- `relationship_to_main_narrative`
- `confidence_score`

### Validation Rules

- Must not invent opposition where only neutral context exists.
- Must not judge which side is true.
- Must cite document IDs for every counter-frame.

### Failure Modes

- false positives from adjacent but non-opposing topics
- collapsing several distinct rebuttals into one bucket
- missing counter-narratives because retrieval was biased
- mistaking factual correction context for fully formed counter-framing

### Build Notes

- Treat stance detection as structured classification.
- Use clustering over extracted framing phrases before summarization.
- Add tests for "no counter-narrative present" as a first-class case.
- Current state:
  - implemented in `backend/services/counter_narrative_builder.py`
  - request and response contract is live on `POST /api/investigations/{id}/counter-narratives`
  - persisted artifact is `CounterNarrativeResult`
  - current logic is deterministic and evidence-first, not ideology-first

## 5. Source Diversity Agent

Status:
- not started

### Purpose

- Summarize the source ecosystem without moralizing it.

### Inputs

- retrieved documents
- source metadata
- optional source labels from ingestion or enrichment

### Processing Logic

1. Count source types.
2. Count geographic spread.
3. Count institutional categories.
4. Count content-type mix.
5. Count ideology labels only when explicitly available.
6. Produce a plain-language contextual summary of the ecosystem.
7. Highlight missing or incomplete labels honestly.

### Output Contract

Return `SourceDiversitySummary` with:

- `total_sources`
- `source_type_distribution`
- `geographic_distribution`
- `institutional_distribution`
- `content_type_distribution`
- `ideology_distribution`
- `notes`
- `limitations`

### Validation Rules

- Missing labels must remain `unknown`.
- No truth or reliability scoring.
- No partisan judgment language.

### Failure Modes

- treating sparse labels as complete
- overinterpreting ideology metadata
- confusing source diversity with truthfulness
- summarizing weak metadata as strong ecosystem conclusions

### Build Notes

- Use deterministic aggregation for counts.
- Use the LLM only for the contextual summary of what the counts imply.
- Add tests for unknown-heavy datasets.

## 6. Analyst Agent

Status:
- not started

### Purpose

- Synthesize the investigation into a draft analysis from upstream artifacts only.

### Inputs

- user query
- investigation plan
- retrieved documents
- timeline
- counter-narratives
- source diversity
- optional graph or family metadata later

### Processing Logic

1. Produce an executive summary.
2. Separate what is observed from what is inferred.
3. Describe spread pattern cautiously.
4. Include counter-narratives and ecosystem context.
5. Generate candidate claims tagged as:
   - `observed_fact`
   - `inference`
   - `uncertainty`
   - `limitation`
   - `recommendation`
6. Attach supporting document IDs and evidence spans to each claim.
7. Produce recommended human checks.

### Output Contract

Return:

- `draft_report_sections`
- `CandidateClaim[]`
- `limitations`
- `recommended_human_checks`
- `confidence_score`

### Validation Rules

- Must not exceed the evidence.
- Must not publish unsupported coordination or origin claims.
- Must explicitly separate observed facts from inference.
- Claims must be reviewable at claim granularity.

### Failure Modes

- overconfident spread interpretation
- mixing analysis with unsupported accusation
- prose that cannot be mapped back to evidence
- claim set too vague for downstream receipt mapping

### Build Notes

- This agent should be claim-producing, not just paragraph-writing.
- Downstream review must happen on claims, not only prose.
- Add regression tests around "possible coordination" wording.

## 7. Skeptic Agent

Status:
- not started

### Purpose

- Red-team the Analyst output before it becomes user-visible.

### Inputs

- analyst draft
- candidate claims
- retrieved documents
- timeline
- counter-narratives
- source diversity

### Processing Logic

1. Challenge every high-impact claim.
2. Flag:
   - overclaims
   - weak evidence
   - missing caveats
   - unsupported origin language
   - unsupported coordination or manipulation claims
   - one-sided omission of counter-narratives
3. Recommend softened replacements or claim removal.
4. Produce a reviewed claim set with explicit statuses.

### Output Contract

Return:

- `ReviewedClaim[]`
- `removed_claim_ids`
- `softened_claim_rewrites`
- `added_cautions`
- `overall_recommendation`

### Validation Rules

- Must not invent new evidence.
- Must not add stronger claims than the Analyst.
- Must be stricter on higher-risk claims.
- Must preserve useful supported observations where possible.

### Failure Modes

- rubber-stamping analyst output
- vague criticism with no actionable revision
- failing to catch origin or coordination overreach
- removing too many claims without preserving evidence-backed value

### Build Notes

- This agent is mandatory.
- Evaluate it heavily with adversarial test cases.
- Treat this stage as the main overclaim defense before publication.

## 8. Receipts Agent

Status:
- not started

### Purpose

- Ensure every surviving major claim has concrete supporting evidence.

### Inputs

- reviewed claims
- retrieved documents
- snippets and evidence spans
- source metadata

### Processing Logic

1. Map each reviewed claim to one or more supporting documents.
2. Choose the best supporting snippet or span.
3. Preserve source name, URL, publication time, and source type.
4. Mark each claim as:
   - `supported`
   - `partially_supported`
   - `unsupported`
   - `contradicted`
   - `needs_human_review`
5. Reject claims that cannot be backed by concrete evidence.
6. Produce coverage summary for final assembly.

### Output Contract

Return:

- `Receipt[]`
- `claim_support_statuses`
- `unsupported_claim_ids`
- `receipt_coverage_summary`

### Validation Rules

- No fabricated snippets.
- URLs must remain intact.
- Unsupported claims cannot remain as confident findings.
- Every receipt must reference a real document in the evidence packet.

### Failure Modes

- shallow claim-to-document matching
- chosen snippet does not actually support the claim
- orphan receipts pointing to missing document IDs
- overgenerous "supported" labels for weak evidence

### Build Notes

- This agent must operate on claim granularity.
- Use rule-based span matching first, then LLM reasoning only when needed.
- Add tests for contradicted and partially supported cases, not just supported ones.

## Shared Validation and Publication Rules

These rules apply across all 8 agents and replace the need for a separate safety agent in this first architecture.

1. No stage may claim absolute origin.
2. Origin language must be `first observed in our dataset`.
3. No stage may accuse people or organizations of manipulation without strong evidence.
4. Unsupported claims must be removed, downgraded, or marked for human review.
5. Final report assembly may only use reviewed claims that survive Skeptic and Receipts.
6. Missing metadata must remain `unknown`.
7. Every important final claim must have at least one valid receipt.
8. The pipeline must permit `insufficient evidence` as a valid outcome.

## Orchestration and Build Order

Do not try to build all 8 agents at once.

Original build order:

1. shared schemas and validation utilities
2. `Query Planner Agent`
3. `Retriever Agent`
4. `Timeline Stage`
5. `Counter-Narrative Agent`
6. `Source Diversity Agent`
7. `Analyst Agent`
8. `Skeptic Agent`
9. `Receipts Agent`
10. final report assembler using reviewed claims and receipts

Current progress against that order:

1. shared schemas and validation utilities: done
2. `Query Planner Agent`: done
3. `Retriever Agent`: done
4. `Timeline Stage`: done
5. `Counter-Narrative Agent`: done
6. `Source Diversity Agent`: deferred
7. `Analyst Agent`: done
8. `Skeptic Agent`: deferred
9. `Receipts Agent`: deferred
10. final report assembler: done

Recommended remaining build sequence from the current codebase:

1. optional `Source Diversity Agent`
2. optional `Skeptic Agent`
3. optional `Receipts Agent`

### Stage 1: Shared Schemas and Validation Utilities

Current status:
- done

Must already exist:
- nothing beyond the base backend

Use fixtures:
- seeded documents
- seeded sources
- one seeded narrative investigation packet

Test before moving on:
- schema validation
- serialization
- required field enforcement
- forbidden-language checks

Do not build yet:
- live retrieval
- final report generation

### Stage 2: Query Planner Agent

Current status:
- done

Must already exist:
- schemas
- planner fixtures

Use fixtures:
- 10 to 20 representative user queries

Test before moving on:
- intent classification
- phrase extraction
- safe non-answering behavior
- machine-readable output

Actual outcome:

- planner is already live on free-text query input
- planner output is persisted as `InvestigationPlan`

### Stage 3: Retriever Agent

Current status:
- done

Must already exist:
- planner outputs
- indexed seeded document set

Use fixtures:
- seeded narrative corpus with known relevant and irrelevant documents

Test before moving on:
- lexical and semantic merge quality
- deduplication
- URL preservation
- counter-narrative inclusion

Actual outcome:

- retriever already uses real web-search provider integration
- HTTP fetch and normalization are already in the critical path
- retrieval output is persisted as `RetrievalResult` plus normalized `Document[]`

### Stage 4: Timeline Stage

Current status:
- done

Must already exist:
- retrieved evidence packet

Use fixtures:
- seeded docs with known timestamps and known first-observed expectations

Test before moving on:
- ordering
- first-observed language
- missing timestamp handling
- event labeling

Actual outcome:

- implemented as deterministic timeline service
- timeline output is persisted as `TimelineResult`
- legacy demo timeline route remains separate

### Stage 5: Counter-Narrative Agent

Current status:
- done

Must already exist:
- retrieved documents
- stance-related fixtures

Use fixtures:
- one corpus with a clear counter-narrative
- one corpus with no real counter-narrative

Test before moving on:
- counter-frame detection
- false-positive control
- document citation coverage

Do not build yet:
- broader narrative family clustering

Actual outcome:

- implemented as deterministic counter-frame builder over retrieved evidence
- counter-narrative output is persisted as `CounterNarrativeResult`
- endpoint is live on `POST /api/investigations/{id}/counter-narratives`

### Stage 6: Source Diversity Agent

Current status:
- next

Must already exist:
- source metadata normalization

Use fixtures:
- mixed-source seeded corpora with partial labels

Test before moving on:
- count accuracy
- unknown handling
- summary tone safety

Do not build yet:
- reliability scoring

### Stage 7: Analyst Agent

Current status:
- pending

Must already exist:
- plan
- evidence packet
- timeline
- counter-narratives
- source diversity

Use fixtures:
- fully seeded investigation packets

Test before moving on:
- observed vs inferred separation
- candidate claim tagging
- supporting document attachment
- limitation generation

Do not build yet:
- direct user-facing publishing

### Stage 8: Skeptic Agent

Current status:
- pending

Must already exist:
- analyst outputs
- adversarial test fixtures

Use fixtures:
- seeded analyst drafts with intentional overclaims

Test before moving on:
- overclaim softening
- claim removal
- origin safety
- coordination-language downgrades

Do not build yet:
- full UI rendering decisions

### Stage 9: Receipts Agent

Current status:
- pending

Must already exist:
- reviewed claims
- evidence spans
- document packet

Use fixtures:
- claims with known support cases
- partial support cases
- contradiction cases

Test before moving on:
- receipt validity
- snippet correctness
- missing-doc rejection
- support-status labeling

Do not build yet:
- open-ended final report prose generation

### Stage 10: Final Report Assembler

Current status:
- pending

Must already exist:
- reviewed claims
- valid receipts
- upstream summaries

Use fixtures:
- complete audited investigation packets

Test before moving on:
- only approved claims appear
- unsupported claims are excluded or clearly marked
- receipt references stay intact

Do not build yet:
- anything that bypasses the reviewed claim path

## Validation, Testing, and Acceptance

### Testing Requirements

The backend must include tests for:

- schema validation for every agent output
- retrieval relevance
- timeline ordering
- counter-narrative presence and absence
- source diversity aggregation
- skeptic regression for overclaim softening
- receipts support-status classification
- full pipeline behavior when one stage fails but the investigation remains auditable

### Minimum Acceptance Criteria

The 8-agent backbone is acceptable only if:

- every stage writes structured output
- every claim has downstream traceability
- no final claim can bypass Skeptic and Receipts review
- origin language is always safe
- unsupported claims are visibly rejected, not silently retained
- final artifacts remain reproducible from stored evidence and run metadata

## Assumptions and Defaults

- The current backend domain is civic and political narrative investigation, where overclaiming risk is high.
- Graph and family tree can be added later as deterministic or semi-structured modules.
- They are not part of this first 8-stage backbone.
- Planner and Retriever are already live against free-text query input and real web retrieval.
- Timeline is already live as a deterministic module and should stay that way unless deterministic coverage proves inadequate.
- Remaining stages should still be built against stable typed artifacts first, then exercised against live investigations.
- Gemini or any other model provider is not yet required for the current planner, retriever, or timeline critical path.

Explicit default guidance:

- Do not try to build all 8 agents at once.
- Build one agent, validate its schema and fixtures, then move to the next.
- Robustness comes from contracts and review loops, not from a giant prompt.
