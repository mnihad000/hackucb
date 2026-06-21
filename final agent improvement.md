# Final Agent Improvement Plan

## Objective

Turn the investigation core into a system that actually behaves like a compact research pod:

- it plans
- it gathers
- it challenges
- it retries with purpose
- it keeps claim-by-claim memory
- it surfaces uncertainty honestly
- it shows visible agent-to-agent handoffs instead of a dressed-up stage chain

This document replaces the earlier improvement plan with a stricter final-state spec based on a code review of the current implementation.

## Current Status After The Research Loop Upgrade

The project is materially better than the original linear stage pipeline. It now has:

- a backend-owned `InvestigationRunner`
- persisted gap, skeptic, claim-ledger, provenance, and loop artifacts
- lane-aware retrieval
- a bounded multi-pass loop
- workspace visibility for passes, gaps, provenance, and claim states

That is a real architectural step forward.

It is not the final form yet.

The remaining gap is qualitative, not cosmetic: the system still often looks like agents more than it truly operates like agents.

## Strict Code Review Findings

These are the final blockers to treat as core-system issues, not optional polish.

### 1. The orchestrator exists, but the main reasoning roles are still heuristic

The loop is real, but `Gap Analyst`, `Skeptic`, provenance review, and final synthesis are still mostly deterministic builders instead of live-model roles with structured outputs and adversarial reasoning.

Consequence:

- the system loops, but it does not yet think in a meaningfully agentic way
- retries are guided by thresholds more than by substantive argument
- the frontend can show "agents," but the backend is still doing rule-based artifact assembly for major judgment calls

### 2. The skeptic does not yet have real rejection authority

The skeptic currently softens or retries, but it is not behaving like a true adjudicator that can reliably reject an overclaimed conclusion and keep it out of the final synthesis.

Consequence:

- the "skeptic" is still closer to a caution layer than a governing authority
- the system can still drift toward analyst-led output instead of adjudicated output

### 3. Claim governance is not strict enough

The claim ledger exists, but its state logic is not yet the single source of truth for what may appear in the report.

Consequence:

- claim states can still be derived too late or from mixed sources
- report eligibility is not governed as tightly as it should be
- a final report can still feel post-hoc filtered rather than truly claim-ledger-controlled

### 4. Gap tracking is not truly stateful across passes

The system stores gaps, but the final design still needs actual gap lifecycle tracking rather than mostly pass-local gap snapshots.

Consequence:

- "resolved" versus "still open" is weaker than it should be
- pass history is informative, but not yet a rigorous work-log of evidence repair
- the system cannot fully explain how a gap evolved from discovery to closure

### 5. Retries are lane-scoped, not claim-scoped

Retries currently target lanes and missing source classes, but the deepest version of this system needs retries attached to specific claims, hypotheses, and unresolved tensions.

Consequence:

- follow-up retrieval is useful, but still broader than necessary
- the system does not yet show that one agent challenged one exact claim and sent retrieval back for a narrow repair mission

### 6. Provenance is still anchor-first rather than chain-first

The provenance layer identifies earliest anchors and duplicate clusters, but it does not yet construct a robust citation chain or lineage graph.

Consequence:

- "first observed" is better tracked than "likely originated from"
- source ancestry remains shallow
- origin investigations still risk feeling careful but incomplete

### 7. Confidence is dimensioned, but not yet conservative enough

Confidence dimensions now exist, which is good. The last step is to make final confidence strictly governed by the weakest critical dimension and claim survival outcomes, not by a partially separate report-level score.

Consequence:

- the system is safer than before, but can still look more confident than its weakest evidence warrants

### 8. The report is still too analyst-shaped

The report should be the final product of a claim-controlled synthesis stage after skeptic approval, not mostly the analyst draft with later annotations and filtering.

Consequence:

- the final answer can still inherit analyst framing too early
- the final synthesizer is not yet a distinct, governed role

### 9. The "agent debate" is still presentation-heavy

The project now exposes richer artifacts, but it still does not persist a true inter-agent conversation or handoff trail.

Consequence:

- users can see outputs from multiple roles
- users still cannot really see the agents briefing, challenging, revising, and handing work to one another

### 10. Compatibility is additive, but not fully unified

The new run loop is the preferred path, but the older per-stage compatibility routes still reflect the older artifact worldview more than a unified investigation state machine.

Consequence:

- backward compatibility is preserved
- the architecture is not yet conceptually clean

## Final Product Principle

The end-state should not be:

- "a bunch of named agents"
- "a flashy UI around a sequential pipeline"
- "a smarter report generator"

The end-state should be:

`a supervised, claim-driven research loop with visible inter-agent coordination`

That means three things must be true at the same time:

1. Every important judgment role is genuinely model-backed or explicitly absent.
2. Claims and gaps are first-class control objects, not just report annotations.
3. Users can inspect why the system kept digging, softened language, or refused to conclude.

## Final Architecture

## Core Roles

Limit the core system to these six roles:

1. Planner
2. Retriever
3. Gap Analyst
4. Skeptic / Adjudicator
5. Frame Mapper
6. Final Synthesizer

Everything else should remain support infrastructure:

- receipts
- verification
- duplicate clustering
- provenance extraction
- timeline extraction
- source profiling
- semantic grouping

Those are services, not "agents."

## Role Contracts

### 1. Planner

Purpose:
Create an investigation brief that defines the work and the stopping rules.

Planner output must include:

- `primary_question`
- `canonical_phrase`
- `intent`
- `subquestions`
- `rival_hypotheses`
- `disconfirming_evidence_criteria`
- `must_have_source_classes`
- `retrieval_lanes`
- `stop_conditions`

Planner authority:

- may define the brief
- may define what evidence would count
- may not conclude truth
- may not soften or reject claims

### 2. Retriever

Purpose:
Gather evidence packets through explicit lanes and targeted retry missions.

Retriever lanes:

- `discovery`
- `corroboration`
- `contradiction`
- `provenance`
- `official`
- `community`

Retriever authority:

- may gather documents
- may propose candidate evidence links
- may not decide claim truth
- may not resolve gaps by itself

Retriever output must carry per-document metadata:

- `retrieval_lane`
- `retrieval_query`
- `pass_number`
- `relevance_score`
- `contradiction_signal`
- `source_uniqueness_score`
- `primary_source_likelihood`
- `date_confidence`
- `quality_band`
- `duplicate_cluster_id`
- provenance hints

### 3. Gap Analyst

Purpose:
Read the evidence packet and issue machine-actionable evidence deficits.

Gap Analyst output must be live-model-backed in the real path. No silent heuristic substitute should impersonate this role.

Gap Analyst output must include:

- `gap_id`
- `gap_type`
- `severity`
- `related_claim_ids`
- `recommended_lane`
- `recommended_source_classes`
- `follow_up_queries`
- `resolved_in_pass`
- `status`

Gap Analyst authority:

- may diagnose missing evidence
- may request targeted retrieval
- may flag weak claims
- may not approve final synthesis

### 4. Skeptic / Adjudicator

Purpose:
Challenge overclaiming and decide whether the loop continues, softens, rejects, or stops.

Skeptic decisions:

- `pass`
- `pass_with_softening`
- `retry_required`
- `claim_rejected`

Skeptic authority:

- may reject claims
- may require targeted retry
- may downgrade language
- may terminate with `insufficient_evidence`
- may block final synthesis until adjudication criteria are met

This authority is non-negotiable. Without it, the skeptic is decorative.

### 5. Frame Mapper

Purpose:
Track narrative mutation, branch structure, and competing frame divergence.

Frame Mapper authority:

- may map branch relationships
- may identify semantic drift
- may distinguish phrase mutation from evidence change
- may inform skepticism and synthesis
- may not settle claim truth alone

### 6. Final Synthesizer

Purpose:
Produce the final report only from claims that survived adjudication.

Final Synthesizer authority:

- may write the final report
- may present uncertainty and caveats
- may not re-approve rejected claims
- may not elevate unresolved claims into confident conclusions

## Agent Communication Layer

This is the most important addition needed for the system to feel like real agents doing deep dives and communicating.

Add persisted inter-agent artifacts:

### `AgentTurn`

Represents one role acting in one pass.

Fields:

- `turn_id`
- `investigation_id`
- `pass_number`
- `role`
- `input_artifact_refs`
- `output_artifact_ref`
- `instructions_received`
- `instructions_issued`
- `decision_summary`
- `confidence_delta`
- `claim_ids_touched`
- `gap_ids_touched`
- `created_at`

### `HandoffMemo`

Represents one agent briefing another.

Fields:

- `memo_id`
- `from_role`
- `to_role`
- `pass_number`
- `subject`
- `body`
- `claim_ids`
- `gap_ids`
- `requested_action`
- `status`

### `ClaimTask`

Represents a specific research task attached to a claim.

Fields:

- `task_id`
- `claim_id`
- `created_by_role`
- `assigned_to_role`
- `reason`
- `queries`
- `required_source_classes`
- `status`
- `resolved_by_pass`

### `DecisionRecord`

Represents a final or intermediate adjudication.

Fields:

- `decision_id`
- `role`
- `scope`
- `target_id`
- `decision`
- `reason`
- `evidence_refs`
- `supersedes_decision_id`

These objects make the system visibly collaborative rather than merely multi-output.

## Supervisory Loop

Keep the loop bounded to 3 passes maximum.

The loop should be:

1. Planner creates the brief.
2. Retriever runs all selected lanes in pass 1.
3. Gap Analyst scores the packet and emits structured gaps plus claim tasks.
4. Skeptic reviews claims, gaps, stop conditions, and either:
   - passes
   - softens
   - rejects
   - requires targeted retry
5. Retriever executes only approved retry tasks in pass 2.
6. Gap Analyst reassesses only the unresolved deficits.
7. Skeptic adjudicates again.
8. Pass 3 runs only if the remaining open problems are specific and addressable.
9. Final Synthesizer writes only from adjudicated claims.

## Claim-Driven Control Model

The claim, not the document packet, should become the main control unit after pass 1.

Every candidate claim should have:

- a stable `claim_id`
- an origin role
- a current state
- a support set
- a counter set
- a verification state
- unresolved questions
- assigned retrieval tasks
- language constraints

Allowed claim states:

- `proposed`
- `supported`
- `partially_supported`
- `contradicted`
- `unresolved`
- `rejected`
- `softened`

Required behavior:

- only `supported`, `partially_supported`, and `softened` claims may survive to the report
- `softened` claims must carry mandatory language constraints
- `rejected` claims must remain visible in the workspace
- `unresolved` claims may appear only inside limitations or open questions
- the final synthesizer may not bypass the ledger

## Gap Lifecycle Model

Gaps must become stateful across passes.

Each gap needs lifecycle support:

- `open`
- `in_progress`
- `resolved`
- `accepted_unresolved`
- `superseded`

Each gap should also store:

- `created_in_pass`
- `last_reviewed_in_pass`
- `resolved_in_pass`
- `resolution_reason`
- `resolution_evidence_refs`

This prevents fake "resolution" and lets the user inspect real evidence repair.

## Retrieval Must Become Claim-Scoped On Retry

Pass 1 can stay lane-driven.

Passes 2 and 3 should become claim-scoped and task-scoped:

- each retry should be tied to one or more `claim_ids`
- each retry should cite the exact skeptic or gap-analyst memo that triggered it
- each retry should declare what success would look like
- each retry should be scored against whether it repaired the intended claim gap

This is how the system starts to feel like agents are actually sending one another back out for targeted work.

## Provenance Must Become Chain-Aware

Origin investigations need more than earliest anchors.

Add explicit provenance structures:

- `publication_first_seen`
- `earliest_dated_anchor`
- `earliest_cited_origin`
- `official_origin_anchor`
- `upstream_citation_edges`
- `duplicate_cluster_ancestry`
- `press_release_lineage`
- `true_origin_unknown`

The system should distinguish:

- first observed in retrieved corpus
- earliest dated retrieved source
- likely upstream source
- official source of record
- unresolved origin

This difference must be visible in both the ledger and the report language.

## Syndication And Independence Discipline

Duplicate handling needs to become independence handling.

Add cluster classes:

- `identical_copy`
- `near_identical_copy`
- `shared_upstream_citation`
- `press_release_lineage`
- `quote_recycling`

Per-cluster outputs should include:

- cluster type
- likely upstream node
- member documents
- independent-source count
- confidence penalty

This should directly affect:

- claim support scoring
- contradiction scoring
- provenance confidence
- final synthesis confidence

## Verification As A Governor, Not A Decoration

Verification must influence outcome, not just annotation.

Required rules:

- a claim cannot be `supported` if its core support is mostly `pending`, `mismatched`, or `unavailable`
- verified contradiction should outweigh weak unverified support
- final confidence must be capped when core receipts remain weak
- the report should explicitly mark when strongest support is still unverified

## Stop Conditions Must Be Structured

Do not infer stop-condition satisfaction from loose text matching.

Represent stop conditions as explicit typed rules.

Examples:

### `origin`

- `needs_earliest_anchor`
- `needs_earlier_variant_attempt`
- `needs_provenance_path_or_uncertainty`
- `needs_first_observed_disclaimer_if_origin_unproven`

### `spread`

- `needs_multi_class_timeline`
- `needs_diffusion_signal`
- `needs_contradiction_search_attempt`

### `counter_narrative`

- `needs_direct_opposing_cluster`
- `needs_same_claim_alignment`

### `source_ecosystem`

- `needs_source_diversity`
- `needs_duplicate_awareness`
- `needs_independent_non_amplifying_source`

The skeptic should evaluate these through structured fields, not by pattern-matching prose.

## Final Confidence Framework

Keep these dimensions:

1. `coverage_confidence`
2. `chronology_confidence`
3. `contradiction_confidence`
4. `provenance_confidence`
5. `verification_confidence`
6. `synthesis_confidence`

But add strict governing rules:

- overall report confidence must be capped by the weakest critical dimension
- if provenance or verification is weak on an origin-style claim, the total confidence may not exceed medium
- if any surviving claim is only `softened`, final language must remain qualified
- if unresolved critical gaps remain, final decision should prefer `insufficient_evidence` over a polished low-confidence report

## Final Report Rules

The report should be a synthesis product, not a dressed analyst draft.

Required rules:

- the final synthesizer reads the claim ledger, skeptic reviews, provenance trace, and receipts
- rejected claims do not appear as findings
- unresolved claims appear only as limitations or unanswered questions
- softened claims must use enforced language templates
- origin findings must differentiate retrieved-corpus first-seen from actual origin
- the report should include a short "why we stopped" section tied to stop conditions

## UI Requirements For "Actual Agents"

If the system should feel like real agents, users need to see the handoffs.

The workspace should expose:

- investigation brief
- active and completed passes
- retrieval lanes used
- agent turn log
- handoff memos
- claim tasks
- open and resolved gaps
- claim ledger with state transitions
- softened and rejected claims
- provenance chain summary
- duplicate cluster summary
- verification state of top receipts
- final stop-condition decision

The user should be able to answer:

- who asked for this retry
- which claim it was meant to repair
- what evidence came back
- why the skeptic still objected or cleared it

That is the threshold where the system feels genuinely agentic.

## Model Strategy

Live model access should be mandatory for the reasoning roles in the upgraded path:

- Planner
- Gap Analyst
- Skeptic / Adjudicator
- Frame Mapper
- Final Synthesizer

Deterministic or cheaper support logic is appropriate for:

- clustering
- duplicate detection
- source labeling
- date extraction
- verification preprocessing
- timeline assembly

Fail-closed rule:

- if required reasoning-role models are unavailable, return an explicit configuration or insufficient-capability state
- do not silently replace core reasoning roles with heuristic stand-ins while presenting them as agents

## Compatibility And API Discipline

Keep current routes for backward compatibility.

But the architecture should converge on one truth:

- `POST /api/investigations/{id}/run` is the canonical path
- `GET /api/investigations/{id}` is the canonical workspace view
- legacy stage endpoints should read from persisted run state when possible
- when recomputation is requested, it should be framed as substage recomputation against the persisted investigation packet, not as a separate old pipeline

## Anti-Patterns To Explicitly Forbid

Do not regress into any of these:

- fake "agent" names over deterministic summaries
- report claims that bypass the claim ledger
- retries that are not tied to specific gaps or claims
- gap resolution without recorded supporting evidence
- optimistic confidence that ignores weak verification or provenance
- treating multiple syndicated copies as independent corroboration
- describing "origin" when the system only has "first observed in retrieved corpus"
- allowing the analyst draft to dominate the final report after skeptic objection

## Test Requirements For Final Potential

The final pass on the core system should include tests for:

- planner brief generation and stop-condition structuring
- claim-scoped retry task generation
- gap lifecycle transitions across passes
- skeptic claim rejection and softening authority
- report exclusion of rejected and unresolved claims
- mandatory language softening on softened claims
- provenance chain assembly and unresolved-origin handling
- syndication cluster penalties affecting claim support
- confidence capping by weakest critical dimension
- persisted `AgentTurn`, `HandoffMemo`, and `ClaimTask` visibility in the workspace
- compatibility behavior of legacy stage endpoints against persisted run state

## Final Definition Of Success

The core system has reached its final potential when it can do all of this in one coherent run:

1. interpret a vague user investigation prompt into a disciplined brief
2. retrieve across multiple evidence lanes
3. identify exact claim and evidence deficits
4. send targeted retry missions for those deficits
5. preserve a visible handoff trail between roles
6. reject or soften claims with explicit reasons
7. distinguish spread, origin, mutation, and counter-framing
8. trace provenance with honest uncertainty
9. produce a final report that is clearly governed by adjudicated evidence
10. show the user why it stopped

## Final Recommendation

The last core upgrade should not be "more features."

It should be:

`make the reasoning roles real, make claim control strict, and make the agent handoffs visible`

If those three things are implemented cleanly, the project will stop feeling like a good staged investigation demo and start feeling like an actual multi-agent research system.
