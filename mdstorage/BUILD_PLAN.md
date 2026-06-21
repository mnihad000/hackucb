# RhetoriQ Build Plan

**Document purpose:** Define the execution plan for building RhetoriQ with a two-person team.  
**Team:** Nihad + Sadman  
**Related docs:** `HACKATHON_MVP_SPEC.md`, `FEATURES.md`, `DATA_SCHEMA.md`, `AGENT_SYSTEM.md`, `AGENT_PROMPTS.md`, `SPONSOR_STRATEGY.md`, `FRONTEND.md`, `ETHICS_AND_SAFETY.md`  
**Primary goal:** Build a polished, reliable demo of RhetoriQ as an AI civic narrative investigation platform.

---

## Redis Integration — Completed June 21, 2026

**Redis Cloud** (v8.4.0) is live and all four Redis layers are fully wired and tested.

### What was built

**1. `GET /api/redis/status` endpoint** (`backend/api/redis_status.py`)
- Reports connection health (ping, Redis version, uptime)
- Reports `InvestigationCache` hit/miss/write rates and cached investigation count
- Reports `RedisVectorStore` doc count, embedding model, vset key
- Reports `PhraseStore` backend (redis vs. in-memory) and top phrases
- Registered in `main.py` alongside all other routers

**2. `InvestigationCache` singleton** (`backend/services/investigation_cache.py`)
- `get_investigation_cache()` now returns a process-wide singleton instead of a new instance each call
- Stats (hits, misses, writes, hit_rate) now accumulate correctly across the lifetime of the process
- Verified: `hit_rate=1.0` in production load — all repeated workspace GETs come from Redis, zero SQLite reads after initial write

**3. Stage-level cache updates** (`backend/api/narratives.py`)
- Added `_update_workspace_cache(investigation_id)` helper — re-loads workspace from SQLite and writes to Redis in one call
- Replaced all `_investigation_cache.invalidate()` calls with `_update_workspace_cache()`:
  - After `/retrieve` completes
  - After `/timeline` completes
  - After `/counter-narratives` completes
  - After `/analyst` completes
  - After `/report` (+ agent-debate) completes
- Also calls `_update_workspace_cache()` immediately after `save_plan()` in `/investigate` so the very first `GET /investigations/{id}` is a cache hit

**4. `PhraseStore` wired into trending** (`backend/services/trending_service.py`)
- `TrendingService.__init__` now creates `self._phrase_store = PhraseStore(redis_url=settings.REDIS_URL)`
- `_refresh()` iterates over all discovery documents after each run and calls `record_phrase()` for every extracted phrase
- Phrase counts are now stored in Redis sorted sets (`rq:phrase_count:*`, `rq:phrase_mentions:latest`) with hourly bucketing
- `GET /api/redis/status` shows top phrases live

**5. `RedisVectorStore` (already wired in previous session)**
- `RetrieverAgent.__init__` already calls `get_redis_vector_store()`
- After live retrieval: `add_documents_batch()` indexes up to 20 new docs
- During demo-mode retrieval: `semantic_search()` boosts keyword scores for matching docs
- Currently 28 documents indexed (from prior investigation runs)

### Test results (live against Redis Cloud)
```
GET /api/redis/status:
  connection.connected = true
  connection.redis_version = 8.4.0
  investigation_cache.available = true  
  investigation_cache.hit_rate = 1.0  (after plan+retrieve)
  vector_store.document_count = 28
  phrase_store.backend = redis

Cache flow (full end-to-end):
  POST /investigate           → 1 write  (plan cached on creation)
  GET  /investigations/{id}  → HIT       (no SQLite read)
  GET  /investigations/{id}  → HIT       (no SQLite read)
  POST /retrieve              → 1 write  (updated workspace cached)
  GET  /investigations/{id}  → HIT       (retrieval_completed, 12 docs)
  Final: writes=2, hits=3, misses=0, hit_rate=1.0
```

### What remains for Redis
- `PhraseStore.top_phrases` will only show content after a trending refresh runs in non-demo mode
- Semantic search boost (`RedisVectorStore.semantic_search`) only fires if docs were indexed in prior investigation runs; first run always falls back to keyword scoring

---

## Arize Tracing Integration — Completed June 21, 2026

**Arize** (AI observability) is live. Every LLM call in the investigation pipeline emits an OpenTelemetry span to Arize cloud via gRPC.

### What was built

**1. `config.py`** — renamed `ARIZE_SPACE_KEY` → `ARIZE_SPACE_ID` to match both the `.env` file and the `arize-otel` environment variable convention. Both `ARIZE_API_KEY` and `ARIZE_SPACE_ID` now resolve correctly at startup.

**2. `services/arize_tracer.py`** (new)
- `init_arize_tracing()` — calls `arize.otel.register()` with `space_id`, `api_key`, `project_name="RhetoriQ"`. Idempotent (safe to call multiple times). Returns `True` when active.
- `is_ready()` — used by `TracedModelClient` to short-circuit when tracing is off
- `tracer_span(agent_name, schema, model)` — context manager yielding an OpenInference-attributed LLM span; no-op when tracing is off
- `record_grounding_eval(investigation_id, verified, pending, unavailable, total_claims)` — emits a `CHAIN` span after every final report build with a `rhetoriq.grounding.score` (0–1) attribute

**3. `agents/model_client.py`** — `TracedModelClient` wrapper + updated factory
- `TracedModelClient(inner, model_name)` — wraps any `BaseModelClient`, adds an OpenInference `LLM` span per `generate_json()` call
- Span attributes: `LLM_MODEL_NAME`, `rhetoriq.agent.schema`, `INPUT_VALUE` (first 2000 chars), `OUTPUT_VALUE` (first 2000 chars), `rhetoriq.prompt_chars`, `rhetoriq.response_chars`, `rhetoriq.latency_seconds`
- `build_model_client(prefer, trace=True)` — wraps the resolved client in `TracedModelClient` automatically when `is_ready()`
- Falls through transparently when tracing is not active (MockModelClient, no Arize)

**4. `api/narratives.py`** — grounding eval after report
- After `save_final_report_result()`, calls `record_grounding_eval()` with claim verification counts
- Wrapped in `try/except` so a tracing error never blocks the report response

**5. `GET /api/arize/status`** (`api/arize_status.py`)
- Reports `configured`, `api_key_set`, `space_id_set`, `tracing_active`, `project_name`, transport, endpoint
- Calls `init_arize_tracing()` on demand (idempotent)
- Lists which agent spans are covered

**6. `main.py`** — `startup()` event calls `init_arize_tracing()` so the provider is ready before the first request.

**Packages installed:** `arize-otel==0.13.0`, `openinference-instrumentation==0.1.53`, `opentelemetry-sdk==1.42.1`, `opentelemetry-exporter-otlp==1.42.1`

### Test results (live)
```
GET /api/arize/status:
  configured       = true
  tracing_active   = true
  project_name     = "RhetoriQ"
  transport        = "grpc"
  endpoint         = "https://otlp.arize.com/v1"

TracedModelClient wraps correctly:
  client type  = TracedModelClient
  wraps traced = True

span fired:
  tracer ready → True
  generate_json("planner") → result keys: [query_text, topic, ...]
  span exported to Arize batch processor ✓
```

### What fires spans at runtime (DEMO_MODE=False)
| Agent / stage | Schema | Span name |
|---|---|---|
| Planner Agent | `planner` | `planner/gemini` |
| Claim Counterpoint Agent | `claim_counterpoints` | `claim_counterpoints/gemini` |
| Receipts Agent | `receipts` | `receipts/gemini` |
| Narrative Family Agent | `family` | `family/gemini` |
| Final Report (grounding eval) | — | `grounding_eval` |

In DEMO_MODE the planner uses `MockModelClient` (no LLM call), so spans fire but the inner call is deterministic. Full spans fire in production mode.

### What remains for Arize
- Auto-instrumentation for Gemini/Groq clients (requires `openinference-instrumentation-google-genai` / `openinference-instrumentation-groq`) — can add after sponsor track submission
- Span search in Arize UI will show `project=RhetoriQ`, filterable by `rhetoriq.agent.schema`

---

## Browserbase Integration — Completed June 21, 2026

**Browserbase** (real browser verification) is live and fully wired end-to-end with a Redis caching layer.

### What was built

**1. `services/verification_cache.py`** (new)
- Redis-backed URL verification cache with 24-hour TTL
- Key schema: `rq:verify:{md5(url)}` → JSON verification result
- Process-wide singleton via `get_verification_cache()`
- Falls back to no-op when Redis is unavailable — Browserbase still runs, results just aren't cached
- `count()` and `recent()` helpers for the status endpoint

**2. `agents/browserbase_agent.py`** — wired Redis cache
- `BrowserbaseAgent.__init__` now creates `self._cache = get_verification_cache()`
- `verify_document()` checks Redis cache first (cache hit → no browser session opened)
- After real Browserbase or httpx verification, writes result to Redis via `self._cache.set()`
- Cache hit is logged at DEBUG level; full receipt is reconstructed from the cached dict

**3. `services/verification.py`** — rewrote to use cache
- `verify_source()` now checks Redis first (populated by BrowserbaseAgent runs)
- Falls back to demo fixtures, then returns `pending` if not yet verified
- Maps Browserbase's 5 status values (`verified`, `source_updated`, `blocked`, `unavailable`, `needs_manual_review`) to the 3 frontend statuses (`verified`, `metadata_mismatch`, `unavailable`, `pending`)
- `source` field in result tells the report which path was taken: `browserbase_cache | demo | not_verified`

**4. `GET /api/browserbase/status`** (`api/browserbase_status.py`)
- Reports API key/project ID config, Playwright availability, active backend mode
- Shows Redis verification cache count and 5 most recent verified URLs
- Registered in `main.py`

### Data flow (end-to-end)

```
POST /investigations/{id}/verify
  → BrowserbaseAgent.verify_documents(docs[:N])
    → For each doc: check Redis cache
      → Cache HIT:  reconstruct Receipt from cache, no browser session
      → Cache MISS: open Browserbase session → navigate → extract title/snippet
                    → build Receipt → write to Redis (24h TTL)
  → Returns list[Receipt]

GET /investigations/{id}  (report build)
  → VerificationService.verify_batch(doc_ids, documents)
    → For each doc: check Redis (if prior /verify run cached it)
      → Cache HIT:  return real status (verified/metadata_mismatch/unavailable)
      → Cache MISS: return demo fixture or pending
```

### Test results (live)
```
GET /api/browserbase/status:
  configured = true
  api_key_set = true
  playwright_available = true
  backend = "browserbase"   ← real browser mode active

POST /investigations/{id}/verify (3 docs, demo URLs):
  3x needs_manual_review  ← demo domains don't exist; honest result

GET /api/browserbase/status after verify:
  cached_urls = 3          ← all 3 written to Redis

VerificationService.verify_source(doc with cached URL):
  source = "browserbase_cache"   ← reading from Redis
  status = "pending"             ← correct map for needs_manual_review
```

### Notes for real investigation runs
- Real news URLs (GDELT/HN articles) will return `verified` or `metadata_mismatch` when Browserbase can fetch them
- Demo seeded URLs return `needs_manual_review` because the domains don't exist — this is honest, not a bug
- Cache survives 24 hours so repeated report builds for the same investigation never re-open a browser

---

## 0. Current Status Snapshot

This section reflects the repo state as of **June 19, 2026**.

### 0.1 Completed So Far

- frontend shell is built in `frontend/`
- homepage/dashboard renders
- Ask RhetoriQ input exists
- investigation page exists
- investigation flowchart exists and is currently the main investigation UI
- top flowchart overlay boxes were removed
- right-side node details panel was removed for now
- frontend builds successfully with `npm run build`
- FastAPI backend exists in `backend/`
- `/health` exists
- `/api/ingest` exists
- `/api/store/status` exists
- `/api/store` clear endpoint exists
- `/api/narratives` exists
- `/api/narratives/{id}` exists
- `/api/narratives/{id}/timeline` exists
- `/api/investigate` exists for seeded narrative IDs
- `/api/graph/{narrative_id}` exists
- `/api/receipts/{narrative_id}` exists
- `/api/mutations/{narrative_id}` exists
- GDELT DOC 2.0 integration exists
- Hacker News ingestion exists
- GDELT search endpoint exists at `GET /api/gdelt/search`
- GDELT results are normalized into the backend `Document` schema
- GDELT timeline bucketing exists
- earliest returned GDELT article is labeled as `first observed in our dataset`
- backend tests for API + GDELT pass

### 0.2 Partially Done / Demo-Only

- frontend is still demo/seed-driven rather than backed by real backend fetches
- Ask RhetoriQ still routes to seeded investigation pages instead of backend investigation
- `/api/investigate` is still narrative-ID driven, not free-text query driven
- agent pipeline is simulated/demo logic, not real Anthropic orchestration
- Browserbase verification is simulated from seeded verification data
- Arize eval is simulated from seeded values
- Redis integration is not real yet
- document store is still in-memory, not persistent
- narrative clustering is still seeded/demo logic
- graph/timeline/report data for seeded narratives is partly hardcoded

### 0.3 Known External Constraint

- the free public GDELT DOC 2.0 endpoint is rate-limiting simple live requests with `429`
- therefore GDELT should be treated as an upstream ingestion source, not a guaranteed real-time dependency for every user request
- backend should continue with fallback/cache/persistence logic before building deeper agent layers
## 0. Current Status Snapshot

This section reflects the repo state as of **June 19, 2026**.

### 0.1 Completed So Far

- frontend shell is built in `frontend/`
- homepage/dashboard renders
- Ask RhetoriQ input exists
- investigation page exists
- investigation flowchart exists and is currently the main investigation UI
- top flowchart overlay boxes were removed
- right-side node details panel was removed for now
- frontend builds successfully with `npm run build`
- FastAPI backend exists in `backend/`
- `/health` exists
- `/api/ingest` exists
- `/api/store/status` exists
- `/api/store` clear endpoint exists
- `/api/narratives` exists
- `/api/narratives/{id}` exists
- `/api/narratives/{id}/timeline` exists
- `/api/investigate` exists for seeded narrative IDs
- `/api/graph/{narrative_id}` exists
- `/api/receipts/{narrative_id}` exists
- `/api/mutations/{narrative_id}` exists
- GDELT DOC 2.0 integration exists
- Hacker News ingestion exists
- GDELT search endpoint exists at `GET /api/gdelt/search`
- GDELT results are normalized into the backend `Document` schema
- GDELT timeline bucketing exists
- earliest returned GDELT article is labeled as `first observed in our dataset`
- backend tests for API + GDELT pass

### 0.2 Partially Done / Demo-Only

- frontend is still demo/seed-driven rather than backed by real backend fetches
- Ask RhetoriQ still routes to seeded investigation pages instead of backend investigation
- `/api/investigate` is still narrative-ID driven, not free-text query driven
- agent pipeline is simulated/demo logic, not real Anthropic orchestration
- Browserbase verification is simulated from seeded verification data
- Arize eval is simulated from seeded values
- Redis integration is not real yet
- document store is still in-memory, not persistent
- narrative clustering is still seeded/demo logic
- graph/timeline/report data for seeded narratives is partly hardcoded

### 0.3 Known External Constraint

- the free public GDELT DOC 2.0 endpoint is rate-limiting simple live requests with `429`
- therefore GDELT should be treated as an upstream ingestion source, not a guaranteed real-time dependency for every user request
- backend should continue with fallback/cache/persistence logic before building deeper agent layers

## Changelog

| Date | Change |
|---|---|
| 2026-06-19 | Removed `reddit_ingestion.py` and `test_reddit_ingestion.py` — using HN ingestion instead |
| 2026-06-19 | Added `FRONTEND_DESCRIPTION.md` — maps current UI and what the trending algorithm must emit |
| 2026-06-19 | Built live trending pipeline: `phrase_extractor.py`, `redis_store.py`, `trending_detector.py`, `api/trending.py` |
| 2026-06-19 | Added `GET /api/trending`, `POST /api/trending/poll`, `GET /api/trending/status` |
| 2026-06-19 | Added `fetch_timeline_vol()` to GDELTIngestion for external spike confirmation |
| 2026-06-19 | Built LLM agent layer: `agents/model_client.py`, `json_utils.py`, `prompt_loader.py`, `agent_orchestrator.py` |
| 2026-06-19 | Model clients: Gemini (primary), Groq (backup), Ollama (local), CachedModelClient (fixture fallback), MockModelClient (demo/tests) |
| 2026-06-19 | Prompt files: `planner.md`, `analyst.md`, `skeptic.md`, `final_report.md` |
| 2026-06-19 | Fixture JSON for all 4 schemas under `agents/fixtures/` |
| 2026-06-19 | 35 new tests in `test_agent_orchestrator.py`; full suite 90/90 passing |
| 2026-06-19 | Added `redis==5.0.1`, `google-generativeai==0.8.3`, `groq==0.11.0` to requirements |
| 2026-06-19 | Migrated Gemini SDK from deprecated `google-generativeai` to `google-genai`; updated default model to `gemini-2.5-flash` |
| 2026-06-19 | Verified all three live model clients working: Gemini 2.5 Flash ✅, Groq llama-3.1-8b ✅, Ollama llama3.1:8b ✅ |
| 2026-06-19 | Added `sentence-transformers==5.6.0` to venv; `all-MiniLM-L6-v2` (384-dim) available for embeddings |

---

## 1. Build Strategy Summary

RhetoriQ is ambitious, so the build strategy must be ruthless:

> Build one extremely convincing vertical slice before adding extra complexity.

The MVP should show one complete investigation flow:

```text
User asks about a political story
        ↓
RhetoriQ retrieves relevant sources
        ↓
RhetoriQ traces the narrative timeline
        ↓
RhetoriQ shows a narrative family tree
        ↓
RhetoriQ identifies counter-narratives
        ↓
RhetoriQ analyzes source diversity
        ↓
Agents debate the evidence
        ↓
Final report is generated
        ↓
Every major claim has clickable receipts
```

The project should not start by building a giant production architecture. It should start by making the demo flow undeniable.

The highest-priority demo message:

> **RhetoriQ lets users ask about any political story, traces how the narrative evolved and spread, and backs every AI claim with clickable evidence.**

---

## 2. Final Team Split

The team split is:

```text
Nihad = frontend + product/demo experience
Sadman = backend starter + AI/data/sponsor core
```

However, the backend should be split into clearly separable modules so Nihad can help with backend-adjacent work after the frontend shell is stable.

The practical model is:

```text
Nihad owns everything the judge sees.
Sadman owns the backend foundation first.
Then Nihad helps with backend modules that directly feed the UI.
```

---

## 3. Nihad Ownership

Nihad owns **100% of frontend**.

## 3.1 Nihad Main Responsibilities

- frontend app setup
- dashboard
- Ask RhetoriQ input
- live narrative radar cards
- investigation page
- report UI
- timeline UI
- narrative family tree UI
- counter-narrative panel
- source diversity panel
- receipts panel with clickable links
- graph visualization
- agent debate view
- loading/progress states
- error/fallback states
- UI polish
- Devpost screenshots/video
- demo click flow
- final presentation flow

## 3.2 Nihad Main Question

Nihad should constantly ask:

> Can a judge understand this in 30 seconds?

## 3.3 Nihad Deliverables

```text
frontend/
  Dashboard
  Ask RhetoriQ input
  Narrative radar cards
  Investigation page
  Timeline component
  Spread graph component
  Narrative family tree component
  Counter-narrative component
  Source diversity component
  Receipts component
  Agent debate component
  Report component
  Loading/progress states
  Error/fallback states
```

## 3.4 Nihad Success Criteria

Nihad succeeds if:

- the app looks like a real civic intelligence product
- the demo is visually clear
- every important section is easy to understand
- clickable receipts work
- the story is obvious without lengthy explanation
- the product feels more advanced than a chatbot
- the frontend can render from a static JSON payload before the backend is complete

---

## 4. Sadman Ownership

Sadman starts with **backend foundation, data, AI, and sponsor integrations**.

## 4.1 Sadman Main Responsibilities

- backend setup
- seeded dataset
- shared investigation JSON payload
- API routes
- report generation
- Anthropic agent workflow
- Redis retrieval / vector search / semantic cache / memory
- claims and receipts generation
- source diversity calculation
- timeline/graph/family tree/counter-narrative data
- Arize eval/tracing
- Browserbase source verification
- Fetch AI agent integration
- backend fallback mode

## 4.2 Sadman Main Question

Sadman should constantly ask:

> Can Nihad call one API and get everything needed to render the full investigation?

## 4.3 Sadman Deliverables

```text
backend/
  /api/demo-investigation
  /api/investigate
  /api/narratives/trending
  /api/reports/:id

data/
  seeded sources
  seeded documents
  seeded narrative cluster
  seeded family tree
  seeded counter-narratives
  seeded timeline
  seeded graph
  seeded source diversity
  seeded agent debate
  seeded claims
  seeded receipts

ai/
  query planner
  analyst agent
  skeptic agent
  receipts agent
  safety/grounding agent
  final report generator

sponsors/
  Redis retrieval/memory
  Anthropic report flow
  Arize eval/tracing
  Browserbase source verification
  Fetch AI agent
```

## 4.4 Sadman Success Criteria

Sadman succeeds if:

- `/api/demo-investigation` works early
- frontend gets stable demo data early
- `/api/investigate` works or falls back safely
- final report has receipts
- AI output does not break the UI
- sponsor integrations are real enough to explain/demo
- backend has a static fallback if live AI/API calls fail

---

## 5. Backend Split Between Sadman and Nihad

Even though Sadman starts backend, backend work should be modular so Nihad can help once the frontend foundation is done.

## 5.1 Sadman Starts With Backend Core

Sadman should build these first:

```text
Backend Foundation
Seed Data
API Routes
Anthropic Agent Flow
Redis Retrieval
Sponsor Core
```

These are blocking pieces. Nihad should not wait for them to finish; Nihad should build against static JSON first.

## 5.2 Nihad Can Help With Backend-Adjacent Modules Later

After Nihad has the frontend shell and main components rendering static data, Nihad can help with backend pieces that are close to UI needs:

```text
Demo JSON shaping
Frontend type definitions
API response formatting
Receipts object formatting
Timeline event formatting
Graph node/edge formatting
Source diversity payload formatting
Agent debate payload formatting
Fallback static payload
```

This lets Nihad help backend without blocking frontend progress.

---

## 6. Detailed Backend Module Split

## 6.1 Backend Foundation

**Primary owner:** Sadman  
**Secondary/helper:** Nihad only if needed

### Tasks

- choose backend stack
- create backend project
- create basic server
- set up CORS
- create health route
- create folder structure
- create environment variable handling
- create basic logging

### Suggested Stack

```text
FastAPI + Python
```

or:

```text
Node/Express + TypeScript
```

FastAPI is recommended if most AI/data scripts are Python.

### Required Routes

```text
GET /health
GET /api/demo-investigation
POST /api/investigate
GET /api/narratives/trending
GET /api/reports/:id
```

### Done When

- backend starts locally
- `/health` returns OK
- `/api/demo-investigation` can return any valid JSON

---

## 6.2 Seeded Dataset

**Primary owner:** Sadman  
**Helper:** Nihad can help shape data for UI after frontend starts

### Sadman Tasks

- create seeded sources
- create seeded documents
- create hidden energy tax narrative cluster
- create narrative family
- create counter-narrative
- create timeline events
- create graph nodes/edges
- create report claims
- create receipts
- create source diversity panel
- create agent debate object

### Nihad Helper Tasks

- check if data renders cleanly in UI
- request missing fields
- simplify graph data if too noisy
- suggest display-friendly labels
- ensure receipt links work in frontend

### Required Files

```text
data/demo_investigation.json
data/sources.json
data/documents.json
```

Optional:

```text
data/timeline.json
data/graph.json
data/report.json
```

### Done When

- the seeded payload renders the full investigation page
- no frontend section is missing required data
- receipts have clickable links or clear demo placeholders

---

## 6.3 API Response Contract

**Primary owner:** Sadman  
**Secondary owner:** Nihad

This is shared because frontend/backend must agree on the same payload.

### Required Payload

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

### Sadman Tasks

- backend returns this shape
- backend validates or normalizes data
- backend keeps IDs consistent
- backend preserves URLs

### Nihad Tasks

- create matching TypeScript types
- verify frontend components can consume the shape
- report missing fields quickly
- keep UI tolerant of optional fields

### Done When

- frontend can render from `GET /api/demo-investigation`
- no component requires manual data transformation inside UI
- one payload renders the whole investigation page

---

## 6.4 Anthropic Agent Flow

**Primary owner:** Sadman  
**Helper:** Nihad can help test outputs against UI

### Sadman Tasks

Implement or simulate:

- Query Planner Agent
- Analyst Agent
- Skeptic Agent
- Receipts Agent
- Safety / Grounding Agent
- Final Report Generator

### Minimal Version

One or two LLM calls can simulate the full flow:

```text
Call 1:
Query planning + retrieved evidence summary

Call 2:
Analyst report + skeptic critique + receipts + final report
```

### Required Output

Anthropic output should eventually become:

```json
{
  "report": {},
  "agent_debate": {},
  "claims": [],
  "receipts": []
}
```

### Nihad Helper Tasks

- check that report sections render correctly
- check that agent debate is readable
- check that receipt cards have needed fields
- flag unsafe language if UI displays it

### Done When

- `/api/investigate` can produce a report-shaped response
- report has receipts
- agent debate exists
- output is valid JSON or converted into valid JSON
- fallback works if Anthropic fails

---

## 6.5 Redis Module

**Primary owner:** Sadman  
**Helper:** Nihad can add UI badges/status once backend returns metadata

### Sadman Tasks

Implement at least two Redis functions:

Option A:

```text
Redis vector search
Redis semantic cache
```

Option B:

```text
Redis vector search
Redis phrase counters
```

Option C:

```text
Redis semantic cache
Redis agent memory
```

Recommended:

```text
Redis vector search + semantic cache
```

### Redis Responsibilities

- store document embeddings
- retrieve semantically similar docs
- cache repeated investigations
- optionally store spike counters
- optionally store prior reports

### Backend Metadata To Return

```json
{
  "sponsor_status": {
    "redis": {
      "used": true,
      "features": ["vector_search", "semantic_cache"],
      "cache_hit": false
    }
  }
}
```

### Nihad Helper Tasks

- show subtle Redis badge
- show “Related sources retrieved from narrative memory”
- show cache hit if available

### Done When

- Redis powers something real in investigation
- Sadman can explain Redis usage in one sentence
- UI can optionally show Redis status

---

## 6.6 Receipts Module

**Primary owner:** Sadman  
**Secondary owner:** Nihad

Receipts are both backend and frontend critical.

### Sadman Tasks

- generate claim IDs
- generate receipt IDs
- map claims to receipts
- preserve source URLs
- include snippets
- include support reasons
- mark unsupported claims

### Nihad Tasks

- render receipt cards
- make links clickable
- show claim support status
- show browser verified badge if available
- ensure unsupported claims do not look like findings

### Receipt Object

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
  "quote_or_snippet": "Critics are calling the proposal a hidden energy tax...",
  "support_reason": "Earliest observed source in the dataset using the phrase.",
  "browser_verified": true,
  "verification_method": "browserbase"
}
```

### Done When

- every major report claim maps to at least one receipt
- receipt links are clickable
- unsupported claims are clearly marked or removed

---

## 6.7 Timeline Module

**Primary owner:** Sadman for data  
**Primary owner:** Nihad for UI

### Sadman Tasks

- sort documents by timestamp
- identify first observed event
- identify early amplification
- identify mainstream pickup
- identify official mention
- identify counter-narrative events

### Nihad Tasks

- render chronological timeline
- highlight first observed event
- distinguish main vs counter-narrative
- make timeline source links clickable

### Done When

- timeline tells the story clearly
- first observed source is obvious
- timeline events match report claims

---

## 6.8 Graph Module

**Primary owner:** Sadman for graph data  
**Primary owner:** Nihad for graph visualization

### Sadman Tasks

- generate nodes
- generate edges
- create relationship labels
- include edge evidence text
- keep graph small and readable

### Nihad Tasks

- render graph with React Flow or similar
- make nodes clickable
- show node details panel
- show edge details if possible
- avoid graph clutter

### Recommended Graph Size

```text
8–15 nodes
8–20 edges
```

### Done When

- graph renders reliably
- graph supports the same story as timeline/report
- graph does not confuse judges

---

## 6.9 Source Diversity Module

**Primary owner:** Sadman for calculation/data  
**Primary owner:** Nihad for visualization

### Sadman Tasks

- count source types
- count local/state/national/international
- count official/unofficial/advocacy/independent
- count original reporting/reposting/opinion/transcript/community post
- use `unknown` where labels are unavailable

### Nihad Tasks

- render source diversity cards/charts
- include caveat:
  - “Source diversity is context, not a truth score.”
- avoid political score-like UI

### Done When

- source diversity panel renders
- at least 3 dimensions are shown
- caveat is visible

---

## 6.10 Narrative Family / Counter-Narrative Module

**Primary owner:** Sadman for data/logic  
**Primary owner:** Nihad for UI

### Sadman Tasks

- define parent narrative family
- define child narratives
- define active branch
- define counter-narrative
- provide related phrases
- provide source examples

### Nihad Tasks

- render family tree
- highlight active narrative
- render counter-narrative side-by-side
- include safe note:
  - “RhetoriQ maps competing frames, not truth.”

### Done When

- family tree is visually understandable
- counter-narrative makes product feel balanced
- report references these sections

---

## 6.11 Arize Module

**Primary owner:** Sadman  
**Helper:** Nihad can render eval badge/status

### Sadman Tasks

- log user query
- log retrieved documents
- log final report
- log claims and receipts
- run or simulate source-grounding eval
- return eval status to frontend

### Backend Metadata To Return

```json
{
  "sponsor_status": {
    "arize": {
      "used": true,
      "source_grounding_score": 0.91,
      "receipt_coverage_score": 1.0,
      "passed_eval": true
    }
  }
}
```

### Nihad Helper Tasks

- show “Source grounding check passed”
- show “Receipt coverage: 100%”
- keep badge subtle

### Done When

- Arize has at least one trace/eval
- UI or demo can mention source-grounding eval

---

## 6.12 Browserbase Module

**Primary owner:** Sadman  
**Helper:** Nihad displays browser-verified badges

### Sadman Tasks

- open 1–3 source URLs
- extract title/date/snippet
- verify source matches receipt
- mark receipts as browser verified

### Nihad Helper Tasks

- show `Browser verified` badge on receipt cards
- avoid implying verified means truthful

### Done When

- at least one receipt is marked browser verified
- Sadman can explain Browserbase in demo

---

## 6.13 Fetch AI Module

**Primary owner:** Sadman  
**Helper:** Nihad adds product/UI mention

### Sadman Tasks

- register RhetoriQ agent if possible
- expose one prompt:
  - “Investigate the hidden energy tax narrative.”
- return short report summary and link
- connect to backend or static report

### Nihad Helper Tasks

- add small UI section:
  - “Available as a RhetoriQ Agent”
- add report share link

### Done When

- RhetoriQ can be described as a discoverable agent
- Fetch integration is real or clearly prototyped

---

## 7. Build Timeline

## Phase 0 — Scope Lock

### Goal

Both people know exactly what they are building.

### Both

- agree on demo story
- agree on shared JSON payload
- agree on routes
- agree on backend modules
- agree on sponsor priority

### Output

```text
One locked demo narrative:
hidden energy tax
```

### Done When

- Nihad can start frontend without waiting
- Sadman can start backend without needing UI details

---

## Phase 1 — Parallel Skeletons

## Nihad

- create frontend app
- create homepage
- create Ask RhetoriQ input
- create investigation page shell
- import static demo JSON directly if backend is not ready

## Sadman

- create backend app
- create `/health`
- create `data/demo_investigation.json`
- create `/api/demo-investigation`
- create initial seeded data

### Done When

- Nihad has static UI rendering
- Sadman has backend returning demo JSON
- frontend can switch from local JSON to API JSON

---

## Phase 2 — Core Demo UI + Data

## Nihad

Build:

- report component
- receipts component
- timeline component
- source diversity panel
- counter-narrative panel

## Sadman

Build:

- complete report data
- claims and receipts
- timeline events
- source diversity payload
- counter-narrative payload

### Done When

- investigation page is demoable with static/seeded backend data
- receipt links work
- report is readable

---

## Phase 3 — Differentiators

## Nihad

Build:

- narrative family tree
- spread graph
- agent debate component
- loading/progress states

## Sadman

Build:

- family tree payload
- graph nodes/edges
- agent debate payload
- first version of Anthropic flow

### Done When

- product feels more advanced than a chatbot
- full investigation page has all major sections

---

## Phase 4 — Dynamic AI + Fallback

## Nihad

- connect Ask RhetoriQ to `/api/investigate`
- show loading steps
- handle error/fallback states
- ensure dynamic response renders

## Sadman

- implement Anthropic report generation
- implement skeptic/receipts/safety flow
- validate JSON
- route failed dynamic calls to demo payload

### Done When

- user can submit a query
- backend returns report-shaped response
- app does not break if AI fails

---

## Phase 5 — Redis + Sponsor Core

## Nihad

- add subtle sponsor status UI if backend returns metadata
- show Redis/Arize/Browserbase badges only where meaningful

## Sadman

- add Redis vector search or semantic cache
- add Arize tracing/eval
- add Browserbase verification for receipts
- add Fetch AI if time

### Done When

- at least Redis + Anthropic are truly used
- ideally Arize + Browserbase are also visible
- sponsor explanations are honest

---

## Phase 6 — Demo Polish

## Nihad

- polish UI
- improve responsiveness
- take screenshots
- prepare click-by-click demo
- make links obvious
- ensure no broken visual states

## Sadman

- stabilize backend
- freeze fallback JSON
- cache main query
- prepare technical/sponsor explanation
- make sure API is fast enough

## Both

- rehearse demo
- test fallback mode
- prepare Devpost
- decide speaking order

---

## 8. Exact Task Boards

## 8.1 Nihad Task Board

| Priority | Task | Status |
|---|---|---|
| P0 | Create frontend app | Done |
| P0 | Build homepage/dashboard | Done |
| P0 | Build Ask RhetoriQ input | Done |
| P0 | Build investigation page layout | Done |
| P0 | Import/render static demo JSON | Done |
| P0 | Build investigation flowchart UI | Done |
| P0 | Remove extra flowchart overlays/details panel for cleaner demo | Done |
| P0 | Build report component | Not Started |
| P0 | Build receipts panel | Not Started |
| P0 | Make receipt links clickable | Not Started |
| P0 | Build timeline component | Not Started |
| P1 | Build counter-narrative panel | Not Started |
| P1 | Build source diversity panel | Not Started |
| P1 | Build narrative family tree | Not Started |
| P1 | Build agent debate component | Not Started |
| P1 | Connect Ask RhetoriQ to backend `/api/investigate` | Not Started |
| P1 | Build graph visualization | Not Started |
| P1 | Add Ask RhetoriQ loading states | Not Started |
| P1 | Add fallback/error states | Not Started |
| P1 | Remove dead frontend files (`NodeDetailsPanel`, `FlowchartLegend`) | Not Started |
| P2 | Add sponsor status badges | Not Started |
| P2 | Polish UI copy to remove seeded/demo wording where needed | Not Started |
| P2 | Create screenshots | Not Started |
| P2 | Prepare demo click flow | Not Started |

## 8.2 Sadman Task Board

| Priority | Task | Status |
|---|---|---|
| P0 | Create backend app | Done |
| P0 | Create `/health` route | Done |
| P0 | Create seeded sources | Done |
| P0 | Create seeded documents | Done |
| P0 | Create seeded narrative/report/graph data | Done |
| P0 | Create live document store | Done |
| P0 | Create `/api/ingest` | Done |
| P0 | Add GDELT ingestion | Done |
| P0 | Add Hacker News ingestion | Done |
| P0 | Add `GET /api/gdelt/search` | Done |
| P0 | Normalize GDELT into `Document` schema | Done |
| P0 | Create timeline data logic | Partial |
| P0 | Create `demo_investigation.json` | Not Started |
| P0 | Create `/api/demo-investigation` | Not Started |
| P0 | Create report/claims/receipts data | Not Started |
| P1 | Create source diversity data | Seeded Only |
| P1 | Create counter-narrative data | Seeded Only |
| P1 | Create family tree data | Not Started |
| P1 | Create graph nodes/edges | Partial |
| P1 | Create agent debate data | Seeded Only |
| P1 | Implement free-text `/api/investigate` | Not Started |
| P1 | Persist documents beyond in-memory store | Not Started |
| P1 | Add dedupe by URL/title/query reuse | Not Started |
| P1 | Add cached fallback for GDELT 429s | Not Started |
| P1 | Implement deterministic narrative grouping/clustering | Not Started |
| P1 | Validate JSON output | Partial |
| P1 | Implement Redis retrieval/cache | Not Started |
| P2 | Implement real Anthropic report flow | Not Started |
| P2 | Implement skeptic/receipts/safety flow | Demo Only |
| P2 | Add Arize tracing/eval | Demo Only |
| P2 | Add Browserbase verification | Demo Only |
| P2 | Add Fetch AI agent | Not Started |
| P2 | Add backend fallback handling | Partial |
| P3 | Add Sentry | Not Started |
| P3 | Add Deepgram transcript | Not Started |
| P3 | Add Band/Orkes if useful | Not Started |

## 8.3 Shared Tasks

| Priority | Task | Owner |
|---|---|---|
| P0 | Lock demo story | Nihad + Sadman |
| P0 | Agree on JSON payload shape | Nihad + Sadman |
| P1 | Test frontend/backend integration | Nihad + Sadman |
| P1 | Rehearse demo | Nihad + Sadman |
| P1 | Prepare Devpost | Nihad primary, Sadman sponsor/tech section |
| P1 | Prepare final pitch | Nihad product/demo, Sadman technical/sponsor |
| P2 | Backup video/screenshots | Nihad primary, Sadman helps |

---

## 9. File / Folder Structure

Recommended repo structure:

```text
rhetoriq/
  README.md

  docs/
    HACKATHON_MVP_SPEC.md
    FEATURES.md
    DATA_SCHEMA.md
    AGENT_SYSTEM.md
    AGENT_PROMPTS.md
    SPONSOR_STRATEGY.md
    BUILD_PLAN.md
    FRONTEND.md
    ETHICS_AND_SAFETY.md

  frontend/
    src/
      pages/
      components/
      lib/
      types/

  backend/
    app/
      main.py
      routes/
      services/
        agents/
        retrieval/
        redis/
        arize/
        browserbase/
        fetch_ai/
      models/
      data/

  data/
    demo_investigation.json
    sources.json
    documents.json

  scripts/
    seed_data.py
    embed_documents.py
    run_demo_pipeline.py
```

---

## 10. API Build Plan

## 10.1 Required Endpoints

### `GET /health`

Purpose:

- confirm backend is live

Response:

```json
{
  "status": "ok"
}
```

---

### `GET /api/demo-investigation`

Purpose:

- return full seeded investigation payload
- unblock frontend
- provide fallback mode

Response:

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

---

### `POST /api/investigate`

Purpose:

- accept a free-text user prompt
- return a backend investigation payload built from stored/ingested documents

Request:

```json
{
  "query_text": "Where did the hidden energy tax narrative come from?"
}
```

Response:

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
  "sources": [],
  "first_observed_in_dataset": {},
  "source_breakdown": {},
  "top_phrases": []
}
```

---

### `GET /api/gdelt/search`

Purpose:

- search GDELT directly
- normalize returned articles into the backend `Document` schema
- return timeline + earliest observed result in dataset wording

---

### `GET /api/narratives`

Purpose:

- return radar/list narrative data

---

### `GET /api/narratives/trending`

Purpose:

- return radar cards for homepage

---

### `GET /api/reports/:id`

Purpose:

- return saved report by ID

---

## 11. Seed Data Plan

The seeded dataset must be good enough to make the product feel real.

Minimum:

- 10–20 documents
- 5–8 sources
- 1 main narrative
- 1 narrative family
- 3–4 child narratives
- 1 counter-narrative
- 1 official/transcript-style mention
- 5–10 receipts
- 1 source diversity panel
- 1 agent debate

Recommended demo narrative:

```text
hidden energy tax
```

Recommended narrative family:

```text
Climate Policy Cost Narrative
```

Recommended child narratives:

```text
hidden energy tax
utility bill surcharge
green mandate costs
war on appliances
```

Recommended counter-narrative:

```text
long-term energy savings / infrastructure investment
```

---

## 12. Sponsor Build Order

## 12.1 Minimum Sponsor Build

```text
1. Anthropic
2. Redis
3. Arize
```

## 12.2 Strong Sponsor Build

```text
1. Anthropic
2. Redis
3. Arize
4. Browserbase
5. Fetch AI
```

## 12.3 Stretch Sponsor Build

```text
1. Anthropic
2. Redis
3. Arize
4. Browserbase
5. Fetch AI
6. Band
7. Deepgram
8. Sentry
9. Orkes
```

---

## 13. Fallback Plan

The demo must not depend entirely on live APIs or LLM calls.

## 13.1 Required Fallbacks

### Static Demo Payload

Always keep:

```text
data/demo_investigation.json
```

This should render the full UI without backend AI calls.

### Pre-Generated Report

Always keep a report generated before judging.

### Static Receipts

Always keep clickable receipt links or clear demo/example links.

### Cached AI Output

If Redis cache works, cache the main demo query.

### Backend Fallback

If live upstream fetch fails:

- reuse cached/store documents if available
- fall back to seeded/demo response when needed
- never hard-fail the whole investigation flow because GDELT returned `429`

If `/api/investigate` fails, route to `/api/demo-investigation`.

### UI Fallback

If graph fails, show timeline + report + receipts.

## 13.2 Fallback Rule

If something breaks, the demo should still show:

- Ask RhetoriQ
- investigation page
- timeline
- report
- receipts
- source diversity
- agent debate

---

## 14. Demo Reliability Checklist

Before judging:

- [ ] Nihad frontend starts cleanly.
- [ ] Sadman backend starts cleanly.
- [ ] Demo payload loads.
- [ ] Ask RhetoriQ works.
- [ ] Fallback query works.
- [ ] Timeline renders.
- [ ] Graph renders or fallback appears.
- [ ] Receipts links are clickable.
- [ ] Source diversity panel renders.
- [ ] Agent debate renders.
- [ ] Final report has no unsafe wording.
- [ ] Sponsor badges/explanations are accurate.
- [ ] Demo works without waiting too long for AI.
- [ ] Devpost description is ready.
- [ ] Screenshots are ready.
- [ ] Pitch is rehearsed.

---

## 15. What Not To Build First

Do not start with:

- Kafka
- Flink
- Kubernetes
- Terraform
- huge microservice architecture
- perfect live data ingestion
- full agent orchestration before deterministic retrieval works
- complex auth
- browser extension
- production database schema
- multiple unrelated sponsor integrations
- complex ideology scoring
- definitive fake-news classifier

These can come later. The hackathon demo needs a clear investigation loop.

---

## 16. Definition of Done

The MVP is done when a judge can:

1. Open RhetoriQ.
2. See live narrative radar cards.
3. Type a natural language prompt.
4. Click into an investigation.
5. See where the narrative first appeared in the observed dataset.
6. See how it spread over time.
7. See a narrative family tree.
8. See counter-narratives.
9. See source diversity.
10. See the spread graph.
11. See agent debate.
12. Read the final report.
13. Click receipts for major claims.
14. Understand the social impact.
15. Understand sponsor integrations.

---

## 17. Pitch Responsibilities

## Nihad Should Explain

- product problem
- user workflow
- UI walkthrough
- why receipts matter
- timeline/family tree/counter-narrative flow
- social impact
- final demo story

## Sadman Should Explain

- backend architecture
- data/retrieval pipeline
- agent system
- Redis
- Anthropic
- Arize
- Browserbase
- Fetch AI
- safety/grounding
- technical depth

Both should be able to explain:

> RhetoriQ is a source-grounded civic narrative investigation platform, not a fake-news detector.

---

## 18. Final Build Recommendation

The team should build RhetoriQ in this order:

```text
Static full demo
  ↓
Dynamic AI report
  ↓
Redis retrieval
  ↓
Receipts and safety
  ↓
Sponsor depth
  ↓
Polish
```

Nihad should not wait for the backend to be complete. He should build the frontend against static JSON immediately.

Sadman should start backend immediately and prioritize `/api/demo-investigation`, seeded data, and the shared payload shape before sponsor integrations.

The winning strategy is parallel development around one shared investigation payload.
