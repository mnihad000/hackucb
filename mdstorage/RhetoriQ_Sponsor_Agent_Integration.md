# RhetoriQ Sponsor + Agent Integration Plan

**Project:** RhetoriQ  
**Current runtime models:** Groq + Gemini  
**Claude usage:** Claude Code for development, scaffolding, implementation assistance, tests, prompt iteration, and sponsor evidence  
**Core thesis:** RhetoriQ is a narrative chain-of-custody system for public civic narratives. It traces where a narrative was first observed, how it spread, what counter-narratives formed, and which receipts support every AI claim.

---

## 1. Final MVP Sponsor Stack

Use sponsors by **product role**, not by hype. Each sponsor should own one clear layer so there is no overlap.

| Layer | Tool / Sponsor | Role in RhetoriQ | Status |
|---|---|---|---|
| Runtime LLM reasoning | Groq + Gemini | Fast planning, extraction, clustering, report generation, critique | Current stack |
| Development + Anthropic track evidence | Claude Code | Build agents, tests, prompts, debugging logs, architecture notes | Use heavily |
| Narrative memory + retrieval | Redis | Vector search, agent memory, semantic cache, spike counters | Core |
| Web evidence verification | Browserbase | Open URLs, extract metadata, verify snippets, generate receipts | Core |
| Agent coordination | Band | Analyst, Skeptic, Receipts, and Safety agents collaborate in a shared investigation room | Core sponsor add-on |
| AI quality / grounding eval | Arize | Trace agents, check claim support, overclaim risk, missing receipts | Core sponsor add-on |
| Reliability | Sentry | Log source failures, API crashes, investigation timeouts, frontend errors | Add after core |
| Spoken narrative evidence | Deepgram | Transcribe speeches, hearings, podcasts, debates, and connect spoken phrases to timeline | Optional but strong |
| Public agent distribution | Fetch AI | Expose RhetoriQ as a discoverable civic intelligence agent | Optional, only if not distracting |
| Workflow orchestration | Orkes | Durable investigation workflow | Optional, lower priority because Band already gives visible agent coordination |
| Evidence compression | The Token Company | Compress large source packs before LLM analysis | Optional technical depth |

---

## 2. Sponsor Overlap Rules

Do **not** use multiple sponsors for the same job. This keeps the project clean and judge-friendly.

| Need | Use | Avoid overlap with |
|---|---|---|
| Runtime model calls | Groq + Gemini | Anthropic API unless you decide to switch runtime |
| Code/build support | Claude Code | Runtime model layer |
| Agent coordination | Band | Fetch AI or Orkes for the same internal collaboration |
| Public agent access | Fetch AI | Band, because Band is internal collaboration, Fetch is external distribution |
| Vector retrieval | Redis | Pinecone, Supabase vector, Chroma, extra vector DBs |
| Evidence verification | Browserbase | Simular or custom scraping for the same job |
| AI quality eval | Arize | Sentry, because Sentry is not AI grounding eval |
| App reliability | Sentry | Arize, because Arize is AI behavior quality |
| Speech / audio evidence | Deepgram | Generic voice input |
| Long context compression | The Token Company | Manual truncation only |

---

## 3. Agent Architecture

The MVP should use a visible multi-agent pipeline, but every agent must have a clear purpose.

```text
User prompt or narrative spike
        ↓
Query Planner Agent
        ↓
Source Retrieval Agent
        ↓
Browserbase Evidence Verification Agent
        ↓
Redis Narrative Memory + Vector Search
        ↓
Narrative Analysis Agents
        ↓
Band Investigation Room
        ↓
Arize Report Quality Eval
        ↓
Final Report + Receipts UI
```

---

## 4. Core Agents

### 4.1 Query Planner Agent

**Purpose:** Convert a user question into an investigation plan.

**Model:** Groq or Gemini  
**Sponsor fit:** Runtime model, not sponsor-specific  
**Input:** User query  
**Output:** Structured investigation plan

```json
{
  "topic": "TikTok ban",
  "canonical_phrase": "TikTok ban narrative",
  "intent": "trace_origin_and_spread",
  "entities": ["TikTok", "Congress", "China", "data privacy"],
  "time_window": "recent_or_seeded",
  "requested_outputs": ["timeline", "origin", "counter_narratives", "source_diversity", "receipts"]
}
```

**Why it matters:** Makes RhetoriQ feel intentional instead of chatbot-like.

---

### 4.2 Source Retrieval Agent

**Purpose:** Retrieve relevant articles, transcripts, seeded docs, and web results.

**Model:** Groq or Gemini for query expansion  
**Sponsor fit:** Redis for retrieval memory  
**Tools:** Redis vector search, Tavily/SerpAPI/live source APIs, seeded dataset

**Responsibilities:**

- Expand user query into search variants.
- Retrieve semantically related documents from Redis.
- Pull live or preloaded public sources.
- Return candidate documents for verification.

**Output:**

```json
{
  "documents": [
    {
      "id": "doc_001",
      "title": "Example Article",
      "url": "https://example.com/article",
      "source_name": "Example Outlet",
      "published_at": "2026-06-20T09:14:00Z",
      "snippet": "Relevant excerpt...",
      "retrieval_reason": "Contains exact phrase and related entities"
    }
  ]
}
```

---

### 4.3 Browserbase Evidence Verification Agent

**Purpose:** Verify source pages before RhetoriQ cites them.

**Sponsor:** Browserbase  
**Tools:** Browserbase Browser / Fetch / Stagehand / Browse CLI  
**Input:** Candidate URLs  
**Output:** Verified receipt objects

**Responsibilities:**

- Open the source page.
- Extract title, author, publish date, and relevant snippet.
- Confirm whether the snippet exists on the page.
- Mark pages as `verified`, `blocked`, `changed`, `unavailable`, or `needs_manual_review`.
- Produce a receipt object for UI.

```json
{
  "receipt_id": "receipt_001",
  "source_id": "doc_001",
  "url": "https://example.com/article",
  "title": "Example Article",
  "author": "Unknown",
  "published_at": "2026-06-20T09:14:00Z",
  "verified_status": "verified",
  "evidence_snippet": "The policy was described as a hidden energy tax...",
  "support_reason": "This source contains the exact phrase and is the earliest observed example in our dataset."
}
```

**Demo line:** Browserbase makes receipts real by opening original source pages before the report cites them.

---

### 4.4 Redis Narrative Memory Agent

**Purpose:** Store and retrieve narrative memory.

**Sponsor:** Redis  
**Tools:** Redis vector search, counters, semantic cache, hashes/lists/streams if useful

**Responsibilities:**

- Store document embeddings.
- Retrieve related documents.
- Store prior investigations.
- Track phrase spike counts.
- Cache repeated investigation results.
- Store agent memory and narrative family links.

**Redis keys:**

```text
rhetoriq:doc:{doc_id}
rhetoriq:embedding:{doc_id}
rhetoriq:phrase_counter:{phrase}:{window}
rhetoriq:narrative:{cluster_id}
rhetoriq:family:{family_id}
rhetoriq:investigation:{report_id}
rhetoriq:agent_memory:{agent_name}:{investigation_id}
```

**Demo line:** Redis is RhetoriQ's narrative memory layer, not just a cache.

---

### 4.5 Narrative Cluster Agent

**Purpose:** Group related documents into narrative clusters.

**Model:** Gemini or Groq  
**Sponsor fit:** Redis vector search supports clustering input

**Responsibilities:**

- Group documents by phrase reuse, semantic similarity, shared entities, and chronology.
- Label clusters with readable names.
- Connect child narratives to parent narrative families.

```json
{
  "cluster_id": "cluster_001",
  "title": "Hidden Energy Tax Narrative",
  "canonical_phrase": "hidden energy tax",
  "related_phrases": ["utility bill surcharge", "green mandate costs"],
  "parent_family": "Climate Policy Cost Narrative",
  "document_ids": ["doc_001", "doc_002", "doc_003"]
}
```

---

### 4.6 Timeline Agent

**Purpose:** Build the first-observed and amplification timeline.

**Model:** Gemini or Groq  
**Sponsor fit:** Uses Redis + Browserbase-verified receipts

**Responsibilities:**

- Sort verified sources by timestamp.
- Distinguish first observed source from proven origin.
- Mark exact phrase reuse, semantic mutation, and amplification.

**Important wording rule:** Say **"first observed in our dataset"**, not **"originated from"**, unless there is strong evidence.

---

### 4.7 Counter-Narrative Agent

**Purpose:** Identify competing frames.

**Model:** Gemini or Groq  
**Sponsor fit:** Arize can evaluate whether counter-narratives were included

**Responsibilities:**

- Find opposing or competing narratives.
- Identify sources supporting each side.
- Show which frame appeared first and which grew faster.

```json
{
  "main_narrative": "The bill is a hidden energy tax.",
  "counter_narrative": "The bill funds infrastructure and lowers long-term costs.",
  "main_sources": ["doc_001", "doc_002"],
  "counter_sources": ["doc_010", "doc_011"]
}
```

---

### 4.8 Source Diversity Agent

**Purpose:** Avoid simplistic bias scoring and show source ecosystem diversity.

**Model:** Gemini or Groq  
**Sponsor fit:** Arize can evaluate whether the report included source diversity

**Responsibilities:**

- Count local vs national vs international sources.
- Count official vs unofficial vs advocacy sources.
- Count article vs opinion vs transcript vs community post.
- Avoid claiming truthfulness from source category alone.

---

### 4.9 Spread Graph Agent

**Purpose:** Build document-source-phrase relationship graph.

**Model:** Gemini or Groq  
**Sponsor fit:** Redis stores graph-related metadata

**Node types:**

- Document
- Source
- Speaker
- Organization
- Narrative cluster
- Counter-narrative
- Phrase

**Edge types:**

- Exact phrase reuse
- Semantic similarity
- Shared entity
- Temporal sequence
- Link/reference
- Quote reuse

---

## 5. Band Investigation Room

### 5.1 Band Coordinator Agent

**Purpose:** Send evidence and draft claims into Band so multiple agents can collaborate.

**Sponsor:** Band  
**Minimum requirement:** At least 2 agents collaborating via Band  
**Recommended agents:** Analyst, Skeptic, Receipts, Safety

```text
Band Room: RhetoriQ Investigation Room

Participants:
1. Analyst Agent
2. Skeptic Agent
3. Receipts Agent
4. Safety Agent
```

### 5.2 Analyst Agent

**Purpose:** Propose the main narrative interpretation.

**Input:** Timeline, clusters, source diversity, receipts  
**Output:** Draft findings

```text
The phrase appears across several sources within a short time window, with repeated wording and shared entities.
```

### 5.3 Skeptic Agent

**Purpose:** Challenge overclaims.

**Input:** Draft findings and receipts  
**Output:** Objections, softened wording, rejected claims

```text
Repeated wording is not enough to prove coordination. This should be described as amplification signals, not confirmed coordination.
```

### 5.4 Receipts Agent

**Purpose:** Ensure every major claim has evidence.

**Input:** Draft report  
**Output:** Claim-to-receipt map and missing evidence list

```json
{
  "claims_checked": 9,
  "claims_supported": 8,
  "claims_missing_receipts": 1,
  "unsupported_claims": ["The narrative was coordinated by a single group."]
}
```

### 5.5 Safety Agent

**Purpose:** Remove risky or unsupported political claims.

**Input:** Report draft and skeptic objections  
**Output:** Safe final wording

```text
Replace "proven propaganda" with "source pattern shows signals consistent with amplification, but evidence is insufficient for a definitive conclusion."
```

**Demo line:** Band coordinates our investigation agents before the report is published.

---

## 6. Arize Report Quality Agent

**Purpose:** Evaluate the final report for grounding and quality.

**Sponsor:** Arize  
**Tools:** Arize / Phoenix tracing and evals

**Responsibilities:**

- Log each agent step.
- Evaluate whether claims are grounded in receipts.
- Flag hallucination risk.
- Track unsupported claims rejected by the Skeptic and Receipts agents.
- Provide a visible quality panel.

**Quality panel:**

```json
{
  "grounding_score": 0.92,
  "claims_with_receipts": "8/9",
  "unsupported_claims_rejected": 2,
  "overclaim_risk": "low",
  "counter_narratives_included": true,
  "source_diversity_checked": true
}
```

**Demo line:** Arize shows that our final report improved after grounding checks and overclaim detection.

---

## 7. Deepgram Spoken Narrative Agent

**Purpose:** Detect when online narratives enter spoken media.

**Sponsor:** Deepgram  
**Status:** Optional, but high-impact if demo includes hearing/speech/podcast audio

**Responsibilities:**

- Transcribe speeches, hearings, podcasts, debates, and interviews.
- Extract phrases from transcript.
- Match transcript phrases against Redis narrative memory.
- Add spoken media events to the timeline.

```json
{
  "event_type": "spoken_media_pickup",
  "source_type": "hearing_transcript",
  "timestamp": "2026-06-20T13:20:00Z",
  "detected_phrase": "hidden energy tax",
  "matched_cluster_id": "cluster_001",
  "confidence": 0.84
}
```

**Do not build:** Generic voice search.  
**Do build:** Narrative movement from online text into spoken public media.

---

## 8. Sentry Reliability Layer

**Purpose:** Monitor production failures.

**Sponsor:** Sentry  
**Status:** Add after the core pipeline works

**Track these events:**

```text
source_verification_failed
browserbase_timeout
redis_retrieval_failed
agent_generation_failed
arize_eval_failed
band_room_sync_failed
frontend_report_render_failed
investigation_timeout
```

**Demo line:** Sentry helps us debug failed investigations and unreliable source verification.

---

## 9. Anthropic / Claude Code Usage Plan

We are **not using Anthropic as the runtime model provider** for the MVP. Runtime models are **Groq and Gemini**.

We are using **Claude Code** as a development and implementation tool.

**Use Claude Code for:**

- Scaffolding frontend pages.
- Building backend route handlers.
- Writing agent prompts.
- Creating test cases.
- Debugging Redis, Browserbase, Band, Arize, and Sentry integration.
- Generating seed data.
- Writing Devpost explanation.
- Producing a visible development log.

**Evidence to save for Anthropic track:**

```text
docs/CLAUDE_CODE_BUILD_LOG.md
```

Include:

- What Claude Code helped build.
- What code modules it touched.
- How it helped improve the project.
- What tests or debugging steps it generated.
- What final product impact came from Claude Code.

**Demo line:** We used Claude Code to build and iterate the full RhetoriQ investigation stack under hackathon constraints, while Groq and Gemini power runtime inference.

---

## 10. Optional Fetch AI Public Agent

**Purpose:** Expose RhetoriQ as a discoverable civic intelligence agent.

**Sponsor:** Fetch AI  
**Status:** Optional. Do not use Fetch for internal coordination if Band is already doing that.

**Agent name:** RhetoriQ Civic Intelligence Agent

**User query:**

```text
Where did the TikTok ban narrative come from?
```

**Agent response:**

```text
I found 12 relevant sources, 3 narrative branches, 2 counter-narratives, and 8 verified receipts. Here is the chain-of-custody summary.
```

**Use only if:** The agent can call your backend investigation endpoint and return a useful result without requiring the custom frontend.

---

## 11. Optional Orkes Investigation Workflow

**Purpose:** Make the pipeline durable and explainable.

**Sponsor:** Orkes  
**Status:** Optional. Lower priority than Band and Arize.

**Workflow:**

```text
parse_query
retrieve_sources
verify_sources
cluster_narratives
build_timeline
find_counter_narratives
run_band_debate
run_arize_eval
generate_report
```

**Use only if:** You can show the workflow visibly in the demo.

---

## 12. MVP Pages

### 12.1 Dashboard / Narrative Radar

**Components:**

- Search bar
- Narrative spike cards
- Spike score
- Source count
- First observed timestamp
- Source diversity preview
- Investigate button

### 12.2 Investigation Page

**Components:**

- Executive summary
- Timeline
- Narrative family tree
- Counter-narratives
- Source diversity panel
- Spread graph
- Band investigation room panel
- Arize report quality panel
- Receipts panel

### 12.3 Receipts Drawer

**Components:**

- Claim text
- Supporting source
- Source URL
- Timestamp
- Snippet
- Verification status
- Support reason

---

## 13. Backend Endpoints

```http
POST /api/investigate
GET  /api/investigations/{id}
GET  /api/narratives/radar
POST /api/sources/verify
POST /api/agents/debate
POST /api/evals/grounding
GET  /api/receipts/{report_id}
```

---

## 14. Minimal Data Contracts

### 14.1 Investigation Request

```json
{
  "query_text": "Where did the hidden energy tax narrative come from?",
  "mode": "ask_rhetoriq",
  "time_window": "seeded_or_recent"
}
```

### 14.2 Investigation Report

```json
{
  "report_id": "report_001",
  "title": "Chain of Custody: Hidden Energy Tax Narrative",
  "summary": "The earliest observed source in our dataset used the phrase at 9:14 AM...",
  "first_observed": {
    "source_id": "doc_001",
    "published_at": "2026-06-20T09:14:00Z",
    "wording": "first observed in our dataset"
  },
  "timeline": [],
  "narrative_family": {},
  "counter_narratives": [],
  "source_diversity": {},
  "agent_debate": {},
  "quality_eval": {},
  "receipts": []
}
```

### 14.3 Claim Receipt Map

```json
{
  "claim_id": "claim_001",
  "claim_text": "The phrase appeared in three sources within two hours.",
  "support_status": "supported",
  "receipt_ids": ["receipt_001", "receipt_002", "receipt_003"],
  "arize_eval": {
    "grounded": true,
    "risk": "low"
  }
}
```

---

## 15. Environment Variables

```bash
# Runtime models
GROQ_API_KEY=
GEMINI_API_KEY=

# Redis
REDIS_URL=
REDIS_PASSWORD=

# Embeddings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_LOCAL_ONLY=0
EMBEDDING_CACHE_TTL_SECONDS=86400

# Browserbase
BROWSERBASE_API_KEY=
BROWSERBASE_PROJECT_ID=

# Band
BAND_API_KEY=
BAND_AGENT_ID=
BAND_ROOM_ID=

# Arize / Phoenix
ARIZE_API_KEY=
ARIZE_SPACE_ID=
PHOENIX_COLLECTOR_ENDPOINT=

# Deepgram optional
DEEPGRAM_API_KEY=

# Sentry
SENTRY_DSN=

# Search/data optional
TAVILY_API_KEY=
SERPAPI_API_KEY=

# Optional integration tests
RUN_REAL_EMBEDDING_TESTS=0
RUN_REDIS_TESTS=0
```

---

## 16. Suggested Repository Structure

```text
rhetoriq/
  apps/
    web/
      app/
      components/
      lib/
    api/
      routes/
      agents/
      services/
      schemas/
      prompts/
  data/
    seeded_documents.json
    seeded_narratives.json
    sample_transcripts/
  docs/
    CLAUDE_CODE_BUILD_LOG.md
    SPONSOR_INTEGRATION.md
    DEMO_SCRIPT.md
  tests/
    test_receipts.py
    test_grounding.py
    test_timeline.py
```

---

## 17. Immediate Build Order

### Step 1: Seed one perfect narrative

Use one narrative with 10 to 15 sources:

- 5 main narrative sources
- 3 counter-narrative sources
- 2 transcript/spoken-media sources if using Deepgram
- 2 ambiguous/noisy sources

### Step 2: Build the investigation endpoint

Return a complete static/dynamic investigation object first.

### Step 3: Add Redis

Store documents, embeddings, phrase counts, and investigation memory.

### Step 4: Add Browserbase

Verify source URLs and generate receipt objects.

### Step 5: Add Groq/Gemini agents

Implement Planner, Timeline, Counter-Narrative, Analyst, Skeptic, and Receipts agents.

### Step 6: Add Band

Route Analyst, Skeptic, Receipts, and Safety outputs through a Band room.

### Step 7: Add Arize

Log traces and show grounding eval results.

### Step 8: Add UI panels

Make the product feel complete:

- Timeline
- Family tree
- Graph
- Receipts
- Agent debate
- Quality panel

### Step 9: Add Deepgram if using spoken media

Transcribe audio and add phrase pickup to timeline.

### Step 10: Add Sentry

Track failures and timeout events.

---

## 18. Final Demo Story

**Judge prompt:**

```text
Where did the hidden energy tax narrative come from?
```

**RhetoriQ response:**

1. Shows earliest observed source.
2. Shows phrase spike.
3. Shows related phrase mutations.
4. Shows counter-narratives.
5. Shows source diversity.
6. Shows Browserbase-verified receipts.
7. Shows Band agent debate.
8. Shows Arize grounding score.
9. Shows final cautious report.

**Final pitch:**

```text
RhetoriQ is a chain-of-custody system for public narratives. It does not claim to be a truth machine. It reconstructs how a narrative appeared and spread, verifies the underlying sources, runs a multi-agent debate to prevent overclaiming, and gives every major AI claim a clickable receipt.
```

---

## 19. Final Sponsor Story

```text
Groq and Gemini power our runtime agents.
Claude Code helped us build and iterate the system.
Redis gives RhetoriQ narrative memory and vector retrieval.
Browserbase verifies source pages and creates receipts.
Band coordinates the investigation agents before publication.
Arize evaluates grounding and report quality.
Sentry monitors reliability.
Deepgram optionally connects online narratives to spoken media.
```
