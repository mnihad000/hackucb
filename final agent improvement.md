# Final Agent Improvement Plan

## Goal

Upgrade the current investigation system from a staged artifact pipeline into a compact but credible research pod.

The target is not "enterprise workflow software." The target is a system that feels visibly smarter, more adversarial, more evidence-aware, and more trustworthy when tracing narratives, origins, spread, counter-frames, and claim support.

This plan assumes the current backend already has these useful foundations:

- a planner
- a retriever with multi-round search
- timeline, source-diversity, counter-narrative, analyst, claim-counterpoint, receipts, and report stages
- persisted investigation workspaces

The main weakness today is not lack of components. The main weakness is that the components mostly run in sequence and summarize the same packet, instead of actively improving the packet.

## Diagnosis Of Current State

Today the system is strong enough to look like a multi-stage investigation, but not strong enough to reliably behave like one.

The main gaps are:

1. Most stages are downstream artifact builders, not active collaborators.
2. Retrieval is the only stage doing real external evidence gathering.
3. Later stages rarely force new retrieval based on weak evidence.
4. The "debate" layer is mostly a deterministic summary, not a true skeptic with authority.
5. Verification is not yet central enough to shape conclusions before final synthesis.
6. Stop conditions are mostly operational, not epistemic.

The result is:

- good narrative demos
- decent report assembly
- limited adversarial pressure
- insufficient coverage repair when the first retrieval packet is weak

## Design Principle

Do not solve this by adding many agents with overlapping jobs.

Solve it by creating a small supervised loop where later reasoning stages can:

- diagnose evidence gaps
- request targeted retries
- reject weak claims
- soften language before the final report

The best version of this system is a research pod with 6 core roles and a 2-3 pass loop.

## Target Architecture

## Core Roles

### 1. Planner

Purpose:
Turn the user query into an investigation brief rather than just a search plan.

Planner output should include:

- primary investigation question
- canonical phrase or topic
- intent: origin, spread, counter-frame, source ecosystem, general investigation
- 3-5 subquestions
- 2-3 rival hypotheses
- disconfirming evidence criteria
- must-have source classes
- retrieval lanes to activate
- stop conditions

This is more robust than a normal plan because it defines what would count as enough evidence and what would count as failure.

### 2. Retriever

Purpose:
Gather the evidence packet through explicit lanes, not generic repeated searching.

The retriever should no longer behave like one broad search step with follow-up expansion. It should search through lanes:

1. Discovery lane
Find broad relevant coverage and candidate anchors.

2. Corroboration lane
Find independent support from different publishers and source types.

3. Contradiction lane
Find rebuttals, fact checks, counter-frames, and hostile interpretations.

4. Provenance lane
Find the earliest observed version, republished variants, source chains, and citation cascades.

5. Official lane
Find press releases, agency statements, hearings, transcripts, campaign pages, court filings, company statements, or other primary-source anchors.

6. Community lane
Find forums, blogs, local outlets, and community spread if the question is about diffusion rather than just top-down media coverage.

The retriever should tag every document with:

- retrieval lane
- query used
- round number
- similarity to main phrase
- contradiction signal
- source uniqueness
- primary-source likelihood
- date confidence

### 3. Gap Analyst

Purpose:
Read the current evidence packet and diagnose what is still missing.

This is the most important missing role in the current system.

The Gap Analyst should score:

- chronology coverage
- source diversity coverage
- contradiction coverage
- primary-source coverage
- claim support density
- duplication contamination
- evergreen/reference contamination
- confidence in "origin" versus only "first observed in retrieved corpus"

Its output should be machine-actionable:

- missing evidence list
- weak claims list
- missing source classes
- retry priority
- explicit follow-up retrieval instructions

Example outputs:

- Need one earlier dated source than June 18.
- Need one official source and one independent hostile source.
- Need proof that three publishers are not syndicating the same wire copy.
- Need to distinguish phrase mutation from true narrative spread.

### 4. Skeptic / Adjudicator

Purpose:
Actively challenge overclaiming and decide whether the investigation is allowed to conclude.

This is not a UI debate summary. This is a gating stage.

The Skeptic should inspect:

- whether claims outrun evidence
- whether chronology implies causality without proof
- whether counter-evidence was actually searched for
- whether duplicated coverage is being mistaken for consensus
- whether primary-source anchors exist
- whether the packet is good enough for the stated intent

The Skeptic should be able to return:

- pass
- pass with softened language
- retry required
- claim rejected

The Skeptic needs authority. If it cannot trigger another retrieval pass, it becomes decorative.

### 5. Frame Mapper

Purpose:
Map related branches, phrase mutation, and competing frames.

This role is close to your current narrative-family stage, but it should become more central.

It should answer:

- what branches exist
- which branch is dominant
- what phrases mutated
- which changes are semantic drift versus real evidence change
- where the counter-frame diverges from the main frame

This becomes especially valuable for political and media narratives where the same event gets reframed across communities.

### 6. Final Synthesizer

Purpose:
Write the final narrative only after the evidence packet survives challenge.

The Final Synthesizer should not decide what is true on its own.
Its job is to:

- assemble the final report
- preserve uncertainty honestly
- separate observed facts from reasonable inferences
- surface rejected claims and softened claims
- make the final answer legible without pretending certainty

## Supervisory Loop

The system should run as a bounded loop, not an open-ended agent swarm.

Use a 3-pass maximum:

### Pass 1: Plan

Planner creates:

- core question
- subquestions
- rival hypotheses
- required lanes
- must-have evidence checklist

### Pass 1: Retrieve

Retriever executes all activated lanes and builds the first evidence packet.

### Pass 1: Diagnose

Gap Analyst scores coverage and surfaces missing evidence.

### Pass 1: Challenge

Skeptic decides:

- enough to proceed
- enough only with softened language
- not enough, retry required

### Pass 2: Targeted Retrieval

Retriever runs only the missing lanes or missing source classes.

No blind repetition. Every retry must be justified by diagnosed gaps.

### Pass 2: Re-score

Gap Analyst and Skeptic reassess.

### Pass 3: Final Targeted Retrieval If Needed

Only if the missing evidence is still specific and addressable.

Otherwise the system should stop and explicitly say the evidence remains incomplete.

### Final Synthesis

Only after the packet clears the stop conditions.

## Stop Conditions

The current system mostly stops because it has enough documents or retrieval rounds.
The upgraded system should stop because it has met evidence thresholds for the specific question type.

Examples:

### For origin questions

Require:

- earliest dated anchor in corpus
- at least one attempt to find earlier variants
- at least one provenance path or explicit note that provenance remains unclear
- explicit warning if "origin" is really only "first observed in retrieved corpus"

### For spread questions

Require:

- timeline coverage across at least 2 source classes
- at least one broader-pickup or diffusion indicator
- at least one contradiction or competing frame search

### For counter-narrative questions

Require:

- at least one clear opposing or corrective cluster
- evidence that it addresses the same claim, not just a nearby topic

### For source ecosystem questions

Require:

- source diversity across publisher types
- duplicate/syndication awareness
- at least one independent non-amplifying source

## Evidence Quality Framework

The system should classify evidence before it synthesizes it.

Every document should be scored on:

1. Relevance
2. Independence
3. Date confidence
4. Source uniqueness
5. Primary-source strength
6. Counter-evidence value
7. Mutation-tracking value
8. Verification status

Suggested quality bands:

- Tier A: primary or strong direct reporting
- Tier B: independent secondary reporting
- Tier C: commentary, derivative reporting, or contextual discussion
- Tier D: low-trust, low-date-confidence, or ambiguous relevance

Final reporting should visibly weight Tier A and Tier B more heavily.

## Robustness Features To Add

These are the logic upgrades that make the system investigation-worthy rather than just more theatrical.

### 1. Coverage Gaps As First-Class Objects

Do not just store warnings.
Persist a structured list:

- gap_id
- gap_type
- severity
- related_claim_ids
- recommended_retrieval_lane
- resolved_in_round

This makes the workspace look intelligent and lets the frontend show why the system kept digging.

### 2. Claim Ledger

Track every candidate claim across the pipeline:

- proposed
- supported
- partially supported
- contradicted
- unresolved
- rejected
- softened

This gives the user a real sense that the system investigated claims rather than merely authored paragraphs.

### 3. Duplicate And Syndication Detection

You need to avoid fake consensus.

Detect:

- identical wire copy
- near-identical headlines
- same press release repeated across outlets
- same source cited by many secondary pieces

The system should reduce confidence when apparent plurality comes from one origin.

### 4. Provenance Tracing

For origin-style investigations, add explicit source-chain tracing:

- who published first in corpus
- who cites whom
- whether coverage traces back to a press release, social post, hearing, or article

Even a simple first-pass provenance graph would make the system feel far more serious.

### 5. Adversarial Retrieval

For every strong claim, search for:

- debunking
- criticism
- alternative framing
- legal or official contradiction
- earlier contradictory precedent

This should be automatic, not user-dependent.

### 6. Verification Before Final Confidence

Do not let report confidence stay high if verification state is weak.

Confidence should be penalized when:

- many core citations are pending
- page metadata mismatches live page data
- strong claims rely on unavailable sources

### 7. Time-Aware Claim Discipline

The system must distinguish:

- current event
- evergreen topic
- historical explainer
- reference page

This matters for both trending and investigation flows.

### 8. Retrieval Budgeting

Do not search endlessly.
Use a bounded evidence budget:

- documents fetched
- source classes covered
- retries used
- unresolved gaps remaining

This keeps the system practical while still feeling rigorous.

## Recommended Minimal Agent Set

Do not exceed 6 core roles for now:

1. Planner
2. Retriever
3. Gap Analyst
4. Skeptic / Adjudicator
5. Frame Mapper
6. Final Synthesizer

Other functions like receipts, verification, source-diversity summaries, and claim-counterpoints should remain as supporting services or subroutines, not headline "agents."

That is cleaner, more believable, and easier to explain.

## How Existing Components Map Into The New System

### Keep And Upgrade

- Planner: keep, but expand into subquestions, rival hypotheses, and stop conditions.
- Retriever: keep, but split into explicit retrieval lanes and targeted retries.
- Narrative family: keep, but reposition as Frame Mapper.
- Receipts: keep, but treat as evidence-audit infrastructure rather than a standalone intelligence agent.

### Keep But Reframe

- Analyst: turn into Final Synthesizer or a synthesis service after the packet is approved.
- Agent debate: replace with a true Skeptic / Adjudicator stage.

### Add

- Gap Analyst
- structured claim ledger
- structured gap ledger
- provenance tracing

## User Experience Improvements

The system becomes much more impressive if users can see the thinking structure.

The workspace should show:

- investigation brief
- rival hypotheses
- evidence lanes used
- current evidence score
- unresolved gaps
- retry history
- claims that survived
- claims that were softened
- claims that were rejected
- verification state of top citations

This creates the feeling of a live research pod rather than a hidden chain of API calls.

## Recommended Model Strategy

Do not use the same model strength everywhere.

Use a stronger model for:

- Planner
- Gap Analyst
- Skeptic / Adjudicator
- Final Synthesizer

Use cheaper models or deterministic logic for:

- clustering
- phrase grouping
- source labeling
- receipt preprocessing
- duplicate detection
- timeline extraction

This keeps the system impressive without becoming expensive.

## Confidence Framework

Every major stage should produce both a score and a reasoned basis for that score.

Suggested dimensions:

1. coverage confidence
2. chronology confidence
3. contradiction confidence
4. provenance confidence
5. verification confidence
6. synthesis confidence

Final report confidence should be the minimum or a conservative blend, not an optimistic average.

That prevents polished reports from masking weak evidence.

## Failure Modes The System Must Explicitly Handle

The upgraded system should be able to say:

- We found the earliest item in the retrieved corpus, not the true origin.
- We found broad repetition, but not independent corroboration.
- We found a counter-frame, but it does not directly address the same claim.
- We found many recent pages, but they mostly derive from one upstream source.
- We found relevant documents, but too few are verified or date-confident.
- We cannot responsibly conclude more without more evidence.

That honesty is part of the product quality.

## Phased Rollout

### Phase 1: Credible Research Loop

Implement:

- Gap Analyst
- Skeptic / Adjudicator
- targeted retry loop
- structured stop conditions

This is the highest-leverage upgrade.

### Phase 2: Stronger Evidence Discipline

Implement:

- claim ledger
- gap ledger
- duplicate/syndication detection
- provenance tracing
- verification-aware confidence penalties

This is where the system starts to feel serious.

### Phase 3: UI And Product Polish

Implement:

- workspace visibility for retries and gaps
- claim survival and rejection display
- evidence-lane visualization
- provenance and mutation views

This is what makes the intelligence legible to users.

## What "Good" Looks Like

A strong final system should be able to do this:

1. Receive a free-form investigation prompt.
2. Break it into subquestions and rival hypotheses.
3. Retrieve evidence across multiple lanes.
4. Detect what is still missing.
5. Run one or two targeted evidence-repair passes.
6. Reject or soften weak claims.
7. Distinguish origin, spread, and framing drift.
8. Produce a report that feels careful, adversarial, and well-grounded.

That is already impressive and cool.
It is also materially more robust than the current architecture without becoming bloated.

## Final Recommendation

Do not market the next version as "more agents."

Market it internally as:

"a supervised research loop with adversarial evidence review."

That is the actual upgrade path.

The most important implementation priority is:

Add a Gap Analyst and a real Skeptic with authority to trigger targeted retrieval retries.

That one change turns the system from a sequential summarizer into an investigation engine.
