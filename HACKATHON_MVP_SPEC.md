# RhetoriQ Hackathon MVP Spec

**Project name:** RhetoriQ  
**Tagline:** *An AI narrative detective for civic and political information.*  
**Primary track:** Ddoski’s World  
**Core idea:** Help users detect, investigate, trace, and verify political narratives using source-grounded AI.

---

## 1. One-Sentence Pitch

RhetoriQ is an AI narrative detective that lets users investigate political stories in natural language, detects emerging narrative spikes, traces how narratives evolve and spread across sources, and generates evidence-backed reports with clickable receipts.

---

## 2. Product Summary

RhetoriQ helps journalists, researchers, students, civic organizations, and politically curious users understand how political stories move through the public information ecosystem.

The product has two main modes:

1. **Live Narrative Radar**  
   RhetoriQ continuously monitors public civic and political sources and surfaces emerging narratives, phrase spikes, and unusual spread patterns.

2. **Ask RhetoriQ Investigation Mode**  
   Users can type a natural language prompt about any political story, claim, phrase, event, or issue they care about. RhetoriQ turns the prompt into an investigation, retrieves relevant sources, builds a timeline and narrative family tree, identifies counter-narratives, analyzes source diversity, runs a multi-agent debate, and produces a final source-grounded report.

The goal is not to be a partisan truth machine or a basic fact-checker. RhetoriQ is an investigation assistant that organizes public evidence, shows how narratives evolve, and clearly separates observed facts from cautious interpretation.

---

## 3. What We Are Building

For the hackathon MVP, we are building a focused civic narrative investigation platform that can:

1. Accept a natural language investigation prompt from the user.
2. Show live or precomputed narrative spikes.
3. Retrieve relevant public sources.
4. Cluster related stories into narrative groups.
5. Build a narrative family tree showing how related talking points evolve.
6. Detect counter-narratives and competing frames.
7. Build a timeline of first observed appearances and later amplification.
8. Build a graph of source/document relationships.
9. Show a source diversity panel.
10. Run a multi-agent investigation and debate.
11. Generate a source-grounded final report.
12. Provide clickable receipts for every major AI-generated claim.

The MVP should feel like a real product, not just a chatbot or notebook.

---

## 4. What We Are Not Building

We are **not** building:

- a definitive fake-news detector
- a truth-scoring engine
- a partisan bias judge
- a tool that labels people or groups as malicious
- a system that proves astroturfing with certainty
- a full production-scale misinformation monitoring platform
- a massive 10-microservice architecture
- a Kafka/Flink/Kubernetes-heavy system unless the core product is already done
- a product that makes accusations without evidence

RhetoriQ should use cautious, source-grounded language.

Use terms like:

- “first observed in our dataset”
- “signals of coordination”
- “consistent with”
- “may indicate”
- “requires human review”
- “source diversity”
- “confidence and uncertainty”

Avoid terms like:

- “definitely fake”
- “proven propaganda”
- “confirmed astroturfing”
- “truth score”
- “this side is lying”

---

## 5. Target Users

### Primary Users

1. **Journalists**
   - Need to understand where narratives came from and how they spread.
   - Need fast evidence trails before writing stories.

2. **Civic organizations**
   - Need to monitor narratives affecting communities and public policy.

3. **Researchers and students**
   - Need structured tools for studying political communication and information diffusion.

4. **Fact-checkers**
   - Need context around claims before deciding what to fact-check.

5. **Public-interest groups**
   - Need early-warning signals for fast-spreading narratives.

### Secondary Users

1. **General politically curious users**
   - Want to ask “where did this story come from?” in plain English.

2. **Campaign or communications analysts**
   - Could use the system to understand public narrative spread, though the project should remain framed as civic/social-impact technology.

---

## 6. Core Product Modes

### 6.1 Live Narrative Radar

Live Narrative Radar is the monitoring mode.

It should surface narrative cards such as:

- “hidden energy tax”
- “gas stove ban”
- “AI job replacement”
- “open borders agenda”
- “student loan bailout”
- “election integrity concerns”

Each card should show:

- narrative title
- short description
- spike score
- number of related sources
- first observed timestamp
- recent growth rate
- source diversity snapshot
- confidence level
- “Investigate” button

#### User Story

A user opens RhetoriQ and sees that a phrase or story is spiking. They click into the narrative and get a full investigation showing where it appeared, how it spread, which counter-narratives exist, and what evidence supports the report.

---

### 6.2 Ask RhetoriQ Investigation Mode

Ask RhetoriQ is the on-demand investigation mode.

Users can type prompts like:

- “Trace the political story behind the TikTok ban.”
- “Where did the phrase ‘hidden energy tax’ come from?”
- “Why is everyone suddenly talking about gas stove bans?”
- “What narratives are forming around immigration this week?”
- “Find the origin and spread of this claim.”
- “Show me the counter-narratives around this policy debate.”
- “How did this issue move from online discussion into mainstream media?”

RhetoriQ should:

1. Understand the user’s prompt.
2. Convert it into search and investigation queries.
3. Retrieve relevant sources.
4. Cluster sources into narratives and counter-narratives.
5. Build a timeline and graph.
6. Run a multi-agent investigation.
7. Produce a final report with receipts.

#### User Story

A user reads a political headline and wonders where the underlying story came from. They paste the headline or ask a natural language question. RhetoriQ returns an investigation brief with timeline, family tree, counter-narratives, source diversity, and clickable evidence.

---

## 7. Required MVP Features

### 7.1 Narrative Spike Detection

RhetoriQ should detect when a phrase, entity, claim, or narrative appears unusually often compared to a baseline.

For the hackathon, this can be simple and explainable.

Example scoring:

```text
spike_score = current_window_mentions / max(1, historical_average_mentions)
```

Or:

```text
z_score = (current_window_count - historical_mean) / historical_standard_deviation
```

The UI should show:

- current mentions
- baseline mentions
- spike multiplier
- first observed timestamp
- related source count

This feature powers Live Narrative Radar.

---

### 7.2 Ask RhetoriQ Query Understanding

When a user asks a question, the system should identify:

- topic
- possible narrative phrase
- relevant entities
- time window
- source types to search
- whether the user wants origin, spread, counter-narratives, or general context

Example input:

```text
Where did the hidden energy tax narrative come from?
```

Possible parsed output:

```json
{
  "topic": "energy policy",
  "canonical_phrase": "hidden energy tax",
  "intent": "trace_origin_and_spread",
  "entities": ["energy", "tax", "policy"],
  "time_window": "recent",
  "requested_outputs": ["timeline", "origin", "spread_graph", "report"]
}
```

---

### 7.3 Narrative Family Tree

RhetoriQ should show how narratives evolve instead of treating every phrase as isolated.

Example:

```text
Climate Policy Cost Narrative
├── hidden energy tax
├── gas stove ban
├── war on appliances
├── green mandate costs
└── utility bill surcharge
```

The family tree should show:

- parent narrative
- child narratives
- related phrases
- first observed examples
- which branch is growing fastest
- which branch has the broadest source diversity
- how branches are connected semantically

#### Why This Matters

Political narratives often mutate. A broad frame can split into several talking points, and old talking points can resurface during new events. The family tree makes RhetoriQ feel like a true investigation platform rather than a keyword tracker.

---

### 7.4 Counter-Narrative Detection

For each main narrative, RhetoriQ should detect opposing or competing narratives.

Example:

Main narrative:

```text
The bill is a hidden energy tax on working families.
```

Counter-narrative:

```text
The bill lowers long-term costs and funds energy infrastructure.
```

The UI should show:

- main narrative
- counter-narrative
- sources pushing each side
- which side appeared first
- which side is growing faster
- common phrases on each side
- source examples for each side

#### Why This Matters

This prevents the system from appearing one-sided. RhetoriQ should map the narrative contest, not simply amplify one framing.

---

### 7.5 Receipts Mode

Every AI-generated report should include a “Receipts” panel.

For every major claim in the report, the system should show:

- exact supporting source
- clickable source URL
- relevant quote or snippet
- timestamp or publication date
- source type
- why the evidence supports the claim

Example:

```text
Claim:
“The phrase appeared in three sources within two hours.”

Receipts:
1. Local Blog A — 9:14 AM — clickable source link
2. Community Post B — 10:02 AM — clickable source link
3. News Outlet C — 10:47 AM — clickable source link
```

#### Receipt Object

```json
{
  "claim_id": "claim_001",
  "claim_text": "The phrase appeared in three sources within two hours.",
  "evidence": [
    {
      "source_id": "source_001",
      "title": "Local Blog Article",
      "url": "https://example.com/article",
      "published_at": "2026-06-20T09:14:00Z",
      "source_type": "local_news",
      "snippet": "The policy is being described as a hidden energy tax...",
      "support_reason": "This is the earliest observed use of the phrase in the dataset."
    }
  ]
}
```

#### Why This Matters

Receipts Mode is one of the most important trust features. It makes the difference between “AI generated a political answer” and “AI organized evidence I can verify.”

All links in the receipts panel should be clickable in the UI.

---

### 7.6 Bias / Source Diversity Panel

RhetoriQ should avoid simplistic political bias scoring. Instead, it should show source diversity.

The panel can show:

- left / center / right / unknown source distribution, if available
- local vs national sources
- official vs unofficial sources
- independent vs advocacy sources
- original reporting vs reposting
- article vs opinion vs transcript vs community post
- source type diversity over time

Use safer framing:

```text
RhetoriQ measures source diversity and spread patterns, not truthfulness or moral correctness.
```

#### Source Diversity Output Example

```json
{
  "source_diversity": {
    "ideology_distribution": {
      "left": 4,
      "center": 6,
      "right": 7,
      "unknown": 9
    },
    "geographic_distribution": {
      "local": 8,
      "national": 10,
      "international": 1,
      "unknown": 7
    },
    "institutional_distribution": {
      "official": 3,
      "unofficial": 19,
      "advocacy": 4
    },
    "content_type_distribution": {
      "original_reporting": 6,
      "reposting": 9,
      "opinion": 5,
      "transcript": 2,
      "community_post": 4
    }
  }
}
```

#### Why This Matters

Source diversity helps users understand what kind of ecosystem is spreading a narrative without claiming whether the narrative is true or false.

---

### 7.7 Multi-Agent Investigation Room

RhetoriQ should use a multi-agent investigation workflow.

Possible agents:

1. **Radar Agent**
   - Detects emerging spikes and narrative clusters.

2. **Query Planner Agent**
   - Converts user prompts into investigation plans.

3. **Retriever Agent**
   - Finds semantically related articles, posts, transcripts, and source documents.

4. **Timeline Agent**
   - Orders sources chronologically and identifies first observed appearances.

5. **Graph Agent**
   - Builds the spread graph and identifies relationships between documents and sources.

6. **Narrative Family Agent**
   - Groups related narratives into parent-child relationships.

7. **Counter-Narrative Agent**
   - Finds opposing or competing narratives.

8. **Source Diversity Agent**
   - Summarizes the diversity of source types and viewpoints.

9. **Analyst Agent**
   - Synthesizes the investigation into a readable report.

10. **Skeptic Agent**
   - Challenges overclaims and asks whether the evidence is actually strong enough.

11. **Receipts Agent**
   - Ensures every major claim has clickable supporting evidence.

12. **Safety / Grounding Agent**
   - Ensures the final report avoids unsupported claims, defamation, and overconfident language.

#### Why This Matters

This architecture supports sponsor tracks such as Fetch AI and Band because it demonstrates real agent coordination rather than a single generic chatbot.

---

### 7.8 Agent Debate Before Final Report

Before publishing a final report, agents should debate the evidence.

Example flow:

```text
Analyst Agent:
“This appears to show possible coordinated amplification.”

Skeptic Agent:
“The evidence is not strong enough to call it coordinated. We only have repeated language and a short time window.”

Receipts Agent:
“Only three of the five claims have direct source support. The unsupported claims should be softened or removed.”

Counter-Narrative Agent:
“There is an opposing narrative that began appearing around the same time and should be included.”

Final Report:
“The pattern shows signals consistent with coordinated amplification, but the evidence is insufficient to make a definitive claim. Human review is recommended.”
```

The final report should distinguish between:

- observed facts
- reasonable inferences
- uncertainty
- unsupported claims that were rejected
- recommended human checks

#### Why This Matters

Political analysis is high-risk. The debate step makes RhetoriQ more responsible, more transparent, and more impressive.

---

### 7.9 Timeline View

Each investigation should include a timeline showing how the narrative appeared and spread.

Timeline entries should include:

- timestamp
- source name
- source type
- title
- short snippet
- clickable source link
- relationship to narrative
- whether it is main narrative or counter-narrative

Example:

```text
9:14 AM — Local Blog A — first observed phrase use
10:02 AM — Community Post B — repeated same framing
10:47 AM — News Outlet C — broader article using related phrase
1:20 PM — Official Speech Transcript — phrase appears in public remarks
```

---

### 7.10 Spread Graph

The graph should show relationships between documents, sources, phrases, and narratives.

Nodes can represent:

- documents
- outlets
- speakers
- communities
- organizations
- narrative branches
- counter-narratives

Edges can represent:

- semantic similarity
- exact phrase reuse
- shared entities
- source linking
- temporal sequence
- reposting
- quote reuse

Graph edge example:

```json
{
  "source": "doc_001",
  "target": "doc_002",
  "edge_type": "phrase_reuse",
  "weight": 0.82,
  "evidence": "Both sources use the phrase 'hidden energy tax'."
}
```

---

### 7.11 Source-Grounded Investigation Report

The final report should include:

- title
- short executive summary
- user question or detected spike
- first observed source
- narrative family placement
- counter-narratives
- spread timeline summary
- source diversity summary
- major amplifiers
- coordination signals, if any
- counter-signals
- confidence score
- limitations
- recommended human checks
- clickable receipts

Example sections:

```text
1. Summary
2. What We Observed
3. Narrative Family
4. Counter-Narratives
5. Timeline of Spread
6. Source Diversity
7. Possible Spread Pattern
8. Evidence Receipts
9. Confidence and Limitations
10. Recommended Human Checks
```

---

## 8. Core Demo Flow

The demo should be simple and story-driven.

### Demo Path A: Live Radar

1. User opens dashboard.
2. Dashboard shows a detected narrative spike.
3. User clicks “Investigate.”
4. App opens the narrative detail page.
5. User sees:
   - spike chart
   - timeline
   - family tree
   - counter-narrative panel
   - source diversity panel
   - graph
   - multi-agent debate summary
   - final report
   - receipts

### Demo Path B: Ask RhetoriQ

1. User types:

```text
Where did the hidden energy tax narrative come from?
```

2. RhetoriQ creates an investigation plan.
3. RhetoriQ retrieves related sources.
4. Agents analyze origin, spread, counter-narratives, and source diversity.
5. Agents debate the evidence.
6. RhetoriQ generates a report with clickable receipts.

### What Judges Should Understand

Within 30 seconds, judges should understand:

```text
RhetoriQ lets you ask about any political story, traces where the narrative came from, shows how it spread, and backs every AI claim with clickable evidence.
```

---

## 9. Demo Narrative Example

Use a concrete narrative for the demo.

Example:

```text
“hidden energy tax”
```

Story:

A phrase framing an energy policy as a “hidden energy tax” first appears in a local/community source, then spreads to several blogs and news outlets, then appears in a transcript-style public speech. A counter-narrative frames the same policy as infrastructure investment and long-term cost reduction.

RhetoriQ should show:

- first observed source
- phrase spike
- related phrases
- parent narrative: climate policy cost narrative
- child narratives:
  - hidden energy tax
  - utility bill surcharge
  - green mandate costs
- counter-narrative:
  - long-term savings / infrastructure investment
- source diversity:
  - local vs national
  - advocacy vs independent
  - official vs unofficial
  - original reporting vs reposting
- final report with receipts

---

## 10. Data Sources

For the hackathon MVP, use a hybrid data strategy.

### Reliable MVP Sources

1. **Seeded dataset**
   - Required for reliable demo.
   - Should include timestamps, source names, source types, URLs, snippets, and narrative labels.

2. **GDELT / RSS / news-style data**
   - Useful for realism.
   - Can be live or pre-fetched.

3. **Transcript-style sample**
   - Useful for showing political speech pickup.
   - Can be preloaded.

4. **Optional Reddit/community-style sample**
   - Useful for showing niche-to-mainstream spread.
   - Safer to seed than rely on Reddit API during demo.

### MVP Recommendation

Do not depend fully on live APIs. Use a seeded dataset that demonstrates the entire product flow, then add live sources if time allows.

---

## 11. Sponsor Integrations

### 11.1 Must-Have Sponsors

#### Anthropic

Use Anthropic for:

- query understanding
- investigation planning
- multi-agent reasoning
- analyst report generation
- skeptic review
- final source-grounded summary

Demo line:

```text
Anthropic powers the investigation agents that reason over the evidence, debate uncertainty, and generate the final civic intelligence report.
```

#### Redis

Use Redis for:

- vector search
- semantic search over documents
- semantic caching
- phrase counters
- agent memory
- narrative memory
- fast retrieval of prior investigations

Demo line:

```text
Redis powers RhetoriQ’s real-time narrative memory, vector search, spike counters, semantic cache, and agent memory.
```

---

### 11.2 Strong Sponsor Add-Ons

#### Fetch AI

Use Fetch AI for:

- discoverable RhetoriQ agent
- Agentverse registration
- ASI:One query access
- multi-agent workflow packaging

Demo line:

```text
Fetch AI lets us expose RhetoriQ as a discoverable civic intelligence agent that users can query directly.
```

#### Arize

Use Arize for:

- logging agent traces
- evaluating source grounding
- checking hallucination risk
- monitoring report quality
- tracking whether claims have receipts

Demo line:

```text
Arize helps us evaluate whether each AI report is grounded in the retrieved evidence before users rely on it.
```

#### Browserbase

Use Browserbase for:

- opening source URLs
- verifying source pages
- extracting titles, authors, timestamps, and snippets
- capturing evidence provenance

Demo line:

```text
Browserbase lets our agent verify source pages and gather evidence instead of blindly trusting scraped text.
```

#### Band

Use Band if available for:

- multi-agent rooms
- shared context between agents
- agent collaboration and debate

Demo line:

```text
Band helps us coordinate multiple investigation agents in a shared room before producing the final report.
```

---

### 11.3 Optional Sponsors

#### Deepgram

Use Deepgram for:

- transcribing speeches
- transcribing debates
- transcribing hearings
- matching spoken phrases to online narratives

Demo line:

```text
Deepgram lets RhetoriQ detect when online narratives move into spoken political media.
```

#### Sentry

Use Sentry for:

- frontend error monitoring
- backend error monitoring
- failed ingestion jobs
- failed agent investigations

Demo line:

```text
Sentry gives us production-style reliability monitoring for the investigation pipeline.
```

#### Orkes

Use Orkes if the sponsor challenge rewards workflows:

```text
detect spike → retrieve evidence → verify sources → build graph → debate → report
```

---

## 12. High-Level Architecture

The MVP should be lean.

```text
User Prompt or Live Spike
        ↓
Query Understanding / Spike Detection
        ↓
Retrieval from Source Dataset
        ↓
Redis Vector Search + Narrative Memory
        ↓
Narrative Clustering
        ↓
Family Tree + Counter-Narrative Detection
        ↓
Timeline + Spread Graph Construction
        ↓
Multi-Agent Investigation Room
        ↓
Agent Debate + Skeptic Review
        ↓
Receipts Agent + Safety/Grounding Agent
        ↓
Final Report API
        ↓
React Frontend
```

### Recommended Stack

- **Frontend:** React + TypeScript
- **Backend:** FastAPI or Node/Express
- **Vector search / memory / cache:** Redis
- **LLM:** Anthropic Claude
- **Agent orchestration:** simple custom workflow, LangGraph, Fetch AI, or Band
- **Graph visualization:** React Flow, Cytoscape.js, Sigma.js, or vis-network
- **Charts:** Recharts
- **Source verification:** Browserbase
- **Observability/evals:** Arize
- **Error monitoring:** Sentry
- **Deployment:** Vercel, Render, Railway, or similar

---

## 13. MVP Pages

### 13.1 Home / Dashboard

Shows:

- search box for Ask RhetoriQ
- live narrative radar
- active narrative cards
- topic filters
- source diversity preview
- recent investigations

Main UI elements:

- prompt input
- “Investigate” button
- trending narratives list
- spike score
- source count
- confidence label

---

### 13.2 Narrative Investigation Page

Shows:

- user query or detected narrative
- summary card
- spike chart
- timeline
- narrative family tree
- counter-narrative panel
- source diversity panel
- spread graph
- multi-agent debate summary
- final report
- receipts panel

---

### 13.3 Receipts Panel

Shows:

- report claims
- clickable evidence links
- snippets
- timestamps
- source type
- support explanation

Every major claim in the final report should map to at least one receipt.

---

### 13.4 Agent Debate View

Shows a readable summary of the agent debate.

Example:

```text
Analyst Agent:
Possible coordination signals exist because multiple sources reused similar wording.

Skeptic Agent:
The evidence is not strong enough to claim coordination. Similar wording may come from a shared press release or common reaction.

Receipts Agent:
The exact phrase reuse is supported by three sources. The claim about coordination should be softened.

Final Decision:
Use cautious language: “signals consistent with coordinated amplification, but insufficient evidence for a definitive conclusion.”
```

---

## 14. Data Model Overview

Detailed schema will live in `DATA_SCHEMA.md`, but the MVP needs these core objects.

### Document

```json
{
  "id": "doc_001",
  "title": "Example Article",
  "source_name": "Local News A",
  "source_type": "local_news",
  "url": "https://example.com/article",
  "published_at": "2026-06-20T09:14:00Z",
  "text": "Full or partial text...",
  "snippet": "Relevant excerpt...",
  "phrases": ["hidden energy tax"],
  "entities": ["Energy Commission", "Governor"],
  "embedding_id": "embedding_doc_001"
}
```

### Narrative Cluster

```json
{
  "id": "cluster_001",
  "title": "Hidden Energy Tax Narrative",
  "canonical_phrase": "hidden energy tax",
  "related_phrases": ["utility bill surcharge", "green mandate costs"],
  "parent_narrative_id": "family_001",
  "document_ids": ["doc_001", "doc_002"],
  "first_observed_doc_id": "doc_001",
  "spike_score": 7.4,
  "confidence": 0.71
}
```

### Narrative Family

```json
{
  "id": "family_001",
  "title": "Climate Policy Cost Narrative",
  "children": ["cluster_001", "cluster_002", "cluster_003"],
  "summary": "A family of narratives framing climate policy through household cost and government overreach."
}
```

### Counter-Narrative

```json
{
  "id": "counter_001",
  "opposes_cluster_id": "cluster_001",
  "title": "Long-Term Energy Savings Narrative",
  "summary": "A counter-frame arguing that the policy reduces long-term costs and funds infrastructure.",
  "document_ids": ["doc_010", "doc_011"]
}
```

### Investigation Report

```json
{
  "id": "report_001",
  "cluster_id": "cluster_001",
  "summary": "The hidden energy tax framing appears to have spread from local commentary into broader political coverage.",
  "spread_pattern": "reactive amplification",
  "confidence": 0.71,
  "limitations": [
    "The dataset may not include earlier deleted posts.",
    "First observed source is not guaranteed to be the absolute origin."
  ],
  "receipt_ids": ["receipt_001", "receipt_002"]
}
```

---

## 15. Agent Rules

All RhetoriQ agents must follow these rules:

1. Use only retrieved evidence.
2. Cite source IDs or URLs for major claims.
3. Distinguish observation from inference.
4. Say “first observed in our dataset,” not “the true origin.”
5. Do not declare a claim true or false unless specifically supported by external verified sources.
6. Do not accuse people or groups of manipulation.
7. Avoid defamatory language.
8. Include uncertainty.
9. Include counter-evidence or counter-narratives when available.
10. Prefer cautious language.

---

## 16. Final Report Requirements

Every final report must include:

- narrative title
- original user question or detected spike
- executive summary
- first observed source
- narrative family tree placement
- counter-narratives
- source diversity summary
- timeline summary
- spread graph summary
- agent debate summary
- confidence score
- limitations
- recommended human checks
- clickable receipts

The report must clearly separate:

```text
Observed Facts
Reasonable Inferences
Uncertainties
Rejected / Unsupported Claims
Recommended Human Checks
```

---

## 17. Definition of Done

The MVP is done when a judge can:

1. Open the app.
2. See live or seeded narrative cards.
3. Type a natural language investigation prompt.
4. Click into an investigation.
5. See a narrative family tree.
6. See counter-narratives.
7. See a timeline.
8. See a spread graph.
9. See a source diversity panel.
10. See a multi-agent debate summary.
11. Read a final AI investigation report.
12. Click evidence links in Receipts Mode.
13. Understand that the product is civic/social-impact oriented.
14. Understand which sponsor technologies power which parts.

---

## 18. Build Priorities

### Priority 0: Demo Reliability

- seeded dataset
- deterministic demo narrative
- working frontend route
- working final report page

### Priority 1: Core Product

- Ask RhetoriQ input
- narrative retrieval
- investigation report
- receipts
- timeline
- graph

### Priority 2: Differentiators

- narrative family tree
- counter-narratives
- source diversity panel
- multi-agent debate

### Priority 3: Sponsor Depth

- Redis vector search / memory
- Anthropic agent
- Arize evals
- Browserbase verification
- Fetch AI agent
- Band multi-agent room
- Sentry monitoring
- Deepgram speech ingestion

---

## 19. Suggested Build Order

1. Create seeded dataset.
2. Define data schema.
3. Build basic backend API.
4. Build dashboard UI.
5. Build Ask RhetoriQ input.
6. Add Redis document retrieval.
7. Add Anthropic report generation.
8. Add receipts mapping.
9. Add timeline view.
10. Add graph view.
11. Add narrative family tree.
12. Add counter-narrative panel.
13. Add source diversity panel.
14. Add multi-agent debate output.
15. Add Arize traces/evals.
16. Add Browserbase source verification.
17. Add Fetch AI agent.
18. Add Sentry.
19. Add Deepgram if time.
20. Polish demo and Devpost.

---

## 20. Team Roles

### Frontend Lead

Owns:

- dashboard
- Ask RhetoriQ input
- investigation page
- graph visualization
- family tree visualization
- receipts panel
- source diversity panel

### Backend / Data Lead

Owns:

- dataset
- ingestion
- phrase extraction
- entity extraction
- API routes
- timeline data
- graph data
- Redis integration

### AI / Agent Lead

Owns:

- Anthropic prompts
- query planning
- multi-agent workflow
- agent debate
- report generation
- receipts generation
- safety/grounding logic

### Sponsor / Demo Lead

Owns:

- Fetch AI
- Arize
- Browserbase
- Sentry
- Deepgram if used
- Devpost
- pitch script
- demo reliability

---

## 21. Main Demo Message

The demo should repeatedly reinforce this idea:

```text
RhetoriQ lets users ask about any political story, traces how the narrative evolved and spread, and backs every AI claim with clickable evidence.
```

Do not lead with architecture.

Lead with:

1. political story
2. investigation
3. timeline
4. family tree
5. counter-narratives
6. receipts
7. social impact
8. sponsor tech

---

## 22. Ethical Positioning

RhetoriQ should be framed as:

```text
A source-grounded civic investigation assistant for understanding narrative spread.
```

Not:

```text
A fake-news detector.
```

Not:

```text
A political truth engine.
```

Not:

```text
A system that proves coordination or manipulation.
```

### Required Ethics Language

RhetoriQ does not determine truth or assign moral blame. It organizes public evidence, detects spread patterns, shows source diversity, and helps humans investigate political narratives with more transparency.

---

## 23. Success Criteria

RhetoriQ is successful if judges say:

- “I immediately understand what this does.”
- “The receipts make this more trustworthy.”
- “The narrative family tree is cool.”
- “The counter-narratives make it feel balanced.”
- “The agent debate is responsible and impressive.”
- “The sponsor integrations are natural.”
- “This fits social impact.”
- “This feels like more than a chatbot.”

---

## 24. Short Devpost-Ready Summary

RhetoriQ is an AI narrative detective for civic and political information. Users can either monitor live narrative spikes or ask a natural language question about any political story. RhetoriQ retrieves relevant sources, traces where the narrative first appeared in the observed dataset, maps how it spread, identifies related and counter-narratives, analyzes source diversity, runs a multi-agent investigation and debate, and generates a final source-grounded report with clickable receipts for every major claim. The project is designed for journalists, researchers, students, and civic organizations that need transparent tools for understanding how political stories emerge and evolve.

---

## 25. Next Documents To Create

After this file, create:

1. `FEATURES.md`
2. `DATA_SCHEMA.md`
3. `AGENT_SYSTEM.md`
4. `AGENT_PROMPTS.md`
5. `SPONSOR_STRATEGY.md`
6. `BUILD_PLAN.md`
7. `DEMO_SCRIPT.md`
8. `ETHICS_AND_SAFETY.md`
9. `README.md`

This file is the source of truth. Other docs should follow this scope.
