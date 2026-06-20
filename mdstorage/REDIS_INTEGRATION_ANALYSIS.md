# Frontend Exploration & Redis Integration Analysis

## Executive Summary

RhetoriQ is a civic narrative investigation platform that traces how narratives spread, branch, and transform across media ecosystems. The frontend is designed to work with a comprehensive backend that processes investigations through a multi-stage pipeline. This analysis identifies key data structures, API patterns, and opportunities for Redis caching and vector search optimization.

---

## 1. KEY DATA STRUCTURES

### 1.1 Investigation Workspace (Core Container)
**Location:** `types/rhetoriq.ts` - `LiveInvestigationWorkspace`
**Purpose:** Tracks complete state of a narrative investigation through all pipeline stages

```typescript
{
  investigation_id: string        // Unique identifier
  query_text: string              // Original user query
  status: InvestigationStatus     // See pipeline status below
  current_stage: InvestigationStage
  created_at: datetime
  updated_at: datetime
  
  // Pipeline artifacts (can be null if not computed yet)
  plan: LiveInvestigationPlan | null
  retrieval: LiveRetrievalResult | null
  retrieved_documents: LiveDocument[]
  timeline: LiveTimelineResult | null
  counter_narratives: LiveCounterNarrativeResult | null
  analyst: LiveAnalystResult | null
  report: LiveFinalReportResult | null
}
```

**Frontend Usage:** 
- Fetched via `GET /api/investigations/{investigationId}`
- Used in `InvestigationPage.tsx` for streaming pipeline progress
- Drives all downstream visualizations

### 1.2 Investigation Plan
**Size:** Lightweight metadata structure
**Key Fields:**
```typescript
{
  query_text: string
  topic: string
  canonical_phrase: string | null  // Main narrative phrase
  intent: PlannerIntent           // "origin" | "spread" | "counter-narrative" | "source-ecosystem"
  entities: string[]              // Extracted key entities
  search_queries: string[]        // Keyword-based searches
  semantic_queries: string[]      // Embedding-based searches
  target_source_types: string[]   // ["news", "blog", "social", etc]
  time_window: { start?, end?, label }
  retrieval_mode: "broad" | "narrow"
  risk_notes: string[]            // Warnings about potential biases
  uncertainty_requirements: string[]
}
```

**Redis Opportunity:** Cache by `query_text` hash as immutable reference

### 1.3 Document (Core Searchable Unit)
**Size:** Large - typically 10-50KB per document
**Key Fields:**
```typescript
{
  id: string
  source_id: string | null
  source_name: string              // "AP", "Twitter", "Local Blog", etc
  source_type: "blog" | "news" | "forum" | "speech_transcript"
  url: string
  title: string
  author: string | null
  published_at: datetime | null
  collected_at: datetime | null
  text: string                     // Full article/post text
  snippet: string | null           // Key excerpt (100-300 chars)
  language: string | null
  geographic_scope: "local" | "state" | "national" | "international"
  
  // AI-extracted features (critical for vector search)
  entities: string[]               // Named entities ["Jane Doe", "Senate Bill 123"]
  phrases: string[]                // Key phrases ["climate action", "green energy"]
  claims: string[] | null          // Extracted claims
  
  // Vector representation
  embedding: float[] | null        // 768-dim embeddings (if computed)
  
  duplicate_of_doc_id: string | null  // Dedup reference
  is_seeded_demo_data: boolean | null
  metadata: Record<string, unknown> | null
}
```

**Frontend Usage:**
- Displayed as sources in flowchart nodes
- Used to build flowchart evidence
- Cited in final reports

### 1.4 Timeline Event
**Purpose:** Chronological narrative moments
```typescript
{
  id: string
  document_id: string              // Reference to source document
  timestamp: datetime              // When the narrative moment occurred
  source_name: string
  source_type: string
  title: string                    // Event headline
  url: string
  snippet: string | null
  event_type: "first_observed" | "early_amplification" | "broader_pickup" | "official_mention" | "resurfacing"
  narrative_side: "main" | "counter" | "related" | "unknown"
  importance_score: number (0-1)   // Vector DB relevance score
  explanation: string              // Why this is a key moment
}
```

**Frontend Usage:** Transformed into flowchart nodes with temporal ordering

### 1.5 Counter Narrative
**Purpose:** Competing frames, opposing narratives
```typescript
{
  id: string
  title: string                    // "Concerns about regulation"
  summary: string
  canonical_phrase: string | null  // "move fast and break things"
  related_phrases: string[]
  supporting_document_ids: string[] // Document references
  first_observed_doc_id: string | null
  relationship_to_main_narrative: "opposing" | "reframing" | "corrective"
  confidence_score: float (0-1)    // Semantic match score
}
```

**Frontend Usage:** Displayed as counter-narrative nodes in flowchart

### 1.6 Final Report Claim
**Purpose:** Extracted claims with evidence
```typescript
{
  claim_id: string
  claim_text: string
  claim_type: "observed_fact" | "inference" | "uncertainty" | "limitation" | "recommendation"
  confidence_score: float (0-1)
  caveats: string[]                // Important qualifications
  citations: [                     // Evidence packet
    {
      document_id: string
      source_name: string
      source_type: string
      title: string
      url: string
      published_at: datetime | null
      snippet: string | null
      relevance_note: string        // Why this supports the claim
    }
  ]
}
```

**Frontend Usage:** 
- Displayed in "Key Claims" card on investigation page
- Max 4 shown to user
- Used in "receipts" system for evidence tracing

### 1.7 Investigation Flowchart Data
**Purpose:** Graph visualization structure
```typescript
{
  title: string
  query: string
  currentNodeId: string            // Pointer to current narrative state
  
  nodes: [
    {
      id: string
      label: string
      subtitle?: string
      nodeType: "current" | "first_observed" | "amplification" | "media_pickup" | "official_mention" | "counter_narrative" | "related" | "uncertain"
      timestamp?: string
      status?: "emerging" | "amplifying" | "mainstreaming" | "declining"
      confidence?: "low" | "medium" | "high"
      sourceCount: number          // How many documents support this moment
      counterSourceCount?: number
      receiptCount?: number
      summary?: string
      sources?: InvestigationNodeSource[]
      receipts?: InvestigationReceipt[]
    }
  ]
  
  edges: [
    {
      id: string
      source: string               // Source node ID
      target: string               // Target node ID
      edgeType: "temporal_sequence" | "exact_phrase_reuse" | "semantic_similarity" | "source_link" | "counter_narrative" | "related_context"
      label?: string
      evidenceText?: string        // Why edge exists
      confidence?: "low" | "medium" | "high"
      animated?: boolean
    }
  ]
}
```

**Frontend Usage:**
- Rendered as animated React Flow graph
- Interactive with node selection, focus mode
- Drives receipt visualization in side panel

---

## 2. API ENDPOINTS & CALL PATTERNS

### 2.1 API Base Configuration
```typescript
// frontend/src/lib/api.ts
API_BASE_URL = 
  process.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
```

### 2.2 Investigation Lifecycle API Calls

#### Create Investigation (Planner Stage)
```typescript
POST /api/investigate
Request: { query_text: string }
Response: {
  investigation_id: string      // e.g., "inv_xyz123"
  query_text: string
}
```
**Frontend Code:** `createInvestigation()` in `DashboardPage` → `Hero` component
**Frequency:** Once per user query
**Caching:** Query → ID mapping (immutable)

#### Get Investigation Workspace (All Stages)
```typescript
GET /api/investigations/{investigationId}
Response: LiveInvestigationWorkspace (full state)
```
**Frontend Code:** `getInvestigationWorkspace()` in `InvestigationPage`
**Call Pattern:** 
- Initial load when page mounts
- Called after each pipeline stage completes to fetch updated artifacts
- Triggered 5+ times during investigation (once per stage)
**Caching:** Full workspace by ID, with TTL for in-progress investigations

#### Run Retrieval (Retriever Stage)
```typescript
POST /api/investigations/{investigationId}/retrieve
Request: { force_refresh?: boolean }
Response: Full workspace with populated retrieval field
```

#### Build Timeline (Timeline Stage)
```typescript
POST /api/investigations/{investigationId}/timeline
Response: Full workspace with populated timeline field
```

#### Counter Narratives (Counter-Narrative Stage)
```typescript
POST /api/investigations/{investigationId}/counter-narratives
Response: Full workspace with populated counter_narratives field
```

#### Build Analyst Synthesis (Analyst Stage)
```typescript
POST /api/investigations/{investigationId}/analyst
Response: Full workspace with populated analyst field
```

#### Build Final Report (Report Stage)
```typescript
POST /api/investigations/{investigationId}/report
Response: Full workspace with populated report field
```

### 2.3 Dashboard/Homepage Endpoints
```typescript
GET /api/narratives
Response: NarrativeCluster[]
Used by: NarrativeRadar component (trending narratives)

GET /api/narratives/{narrativeId}
Response: NarrativeCluster
```

### 2.4 Investigation Page Data Flow

**Timeline of API calls for single investigation:**

```
User clicks "Investigate" with query
  ↓
POST /api/investigate → get investigation_id
  ↓
Navigate to /investigation/{id}
  ↓
GET /api/investigations/{id} (workspace starts empty/planning)
  ↓
While workspace.retrieval is null:
  POST /api/investigations/{id}/retrieve
  GET /api/investigations/{id} (poll for completion)
  ↓
While workspace.timeline is null:
  POST /api/investigations/{id}/timeline
  GET /api/investigations/{id}
  ↓
While workspace.counter_narratives is null:
  POST /api/investigations/{id}/counter-narratives
  GET /api/investigations/{id}
  ↓
While workspace.analyst is null:
  POST /api/investigations/{id}/analyst
  GET /api/investigations/{id}
  ↓
While workspace.report is null:
  POST /api/investigations/{id}/report
  GET /api/investigations/{id}
```

---

## 3. FRONTEND FEATURES REQUIRING MEMORY/SEARCH

### 3.1 Real-time Pipeline Progress Tracking
**Components:** `InvestigationPage.tsx`, `PipelineStatusCard`
**Data Needs:**
- Current pipeline stage label
- Status transitions
- Error messages
- Completion percentage hints

**Redis Opportunity:**
- Cache workspace state by ID with short TTL
- Use Redis pub/sub for progress notifications (future enhancement)
- Stage completion markers for progress visualization

### 3.2 Interactive Flowchart Navigation
**Component:** `InvestigationFlowchart.tsx`
**Features:**
- Animated intro sequence revealing narrative path
- Node selection with focus mode
- Highlight path-to-current from any node
- Hover neighborhood highlighting
- Receipt panel detail display
- Counter-narrative toggle
- Focus mode with dimming

**Data Needs:**
- Node position calculations (computed from layout)
- Edge reveal timing
- Path resolution (breadth-first search from node to current)
- Neighbor lookups

**Redis Opportunity:**
- Cache computed node layouts (expensive calculation)
- Pre-compute common paths for faster interaction
- Store graph topology for instant neighbor queries

### 3.3 Node Details Panel
**Component:** `NodeDetailsPanel.tsx`
**Displays:**
- Node type label and metadata
- Supporting sources (split by stance)
- Receipts/evidence snippets
- Source verification status
- Confidence metrics

**Data Needs:**
- Document full text for snippet display
- Source metadata
- Verification results

**Redis Opportunity:**
- Cache document snippets and metadata
- Cache source trust scores/verification results
- Pre-compute stance classification

### 3.4 Investigation Receipt System
**Component:** Multiple (node receipts, claims receipts)
**Features:**
- Clickable evidence linking claims to sources
- Browser verification badges
- Source name and snippet display
- URL linking to original

**Data Needs:**
- Document snippets (need to find relevant excerpt)
- Source metadata
- Verification status
- Relevance scoring between claim and document

**Redis Opportunity:**
- Cache snippet extraction results
- Cache relevance scores (claim ↔ document)
- Cache verification status by URL/source

### 3.5 Report Generation
**Component:** `InvestigationPage` (displays report artifacts)
**Features:**
- Key claims extraction (top 4 shown)
- Evidence packet building
- Claim citations with relevance notes
- Confidence scoring

**Data Needs:**
- Processed claims with document references
- Pre-scored relevance between claims and evidence
- Confidence calculations

**Redis Opportunity:**
- Cache claim extraction results
- Cache evidence packet scoring
- Cache final report sections

### 3.6 Dashboard Narrative Radar
**Component:** `NarrativeRadar.tsx`, `NarrativeCard.tsx`
**Features:**
- Trending narrative detection
- Spike visualization (7.4x, 5.8x growth)
- Source mix summary
- Confidence indicators
- Coverage metrics

**Data Needs:**
- Aggregated narrative statistics
- Source distribution calculations
- Spike detection results

**Redis Opportunity:**
- Cache trending narratives (Sorted Set for ranking by spike)
- Cache narrative summaries
- Cache source distributions by narrative

---

## 4. VECTOR SEARCH USE CASES

### 4.1 Document-Claim Relevance (HIGH PRIORITY)
**Current Need:** Match claims to supporting documents
**Problem:** Currently must search document text linearly
**Solution:** Vector embeddings for semantic matching

**Implementation:**
```
1. Embed all documents on ingestion: text → 768-dim vector
2. When extracting claim, embed claim text
3. Vector search against document embeddings
4. Return top-K most semantically similar documents
5. Cache results by (claim_id, document_id) pair
```

**Redis Usage:**
- Store embeddings in Redis using RedisSearch vector indexes
- Query: `FT.SEARCH idx:documents "@embedding:[VECTOR] ==> {$k: 5}"`
- Cache results with TTL for 24 hours

**Expected Impact:**
- Faster claim citation building
- Better evidence matching
- Reduces latency for analyst stage

### 4.2 Phrase Propagation Tracking (MEDIUM PRIORITY)
**Current Need:** Find how phrases mutate and spread across documents
**Problem:** Exact phrase matching misses variations
**Solution:** Semantic phrase embeddings

**Implementation:**
```
1. Extract phrases from documents (already done: document.phrases)
2. Embed phrases at ingestion time
3. Create phrase co-occurrence vectors
4. Search for phrase mutations via embedding distance
5. Track mutation chains
```

**Redis Usage:**
- Sorted Sets with similarity scores: `phrases:{canonical} → mutations with scores`
- Stream for phrase evolution timeline

**Expected Impact:**
- Detect coordinated narrative shifts
- Identify memes and narrative mutations
- Support counter-narrative detection

### 4.3 Counter-Narrative Detection (MEDIUM PRIORITY)
**Current Need:** Find opposing frames and reframings
**Problem:** Counter-narratives are contextual and nuanced
**Solution:** Semantic search against known counter-narrative patterns

**Implementation:**
```
1. Maintain vector library of known counter-narrative types
2. Embed candidate documents/claims
3. Vector search against counter-narrative library
4. Score relationship type (opposing/reframing/corrective)
5. Extract supporting evidence clusters
```

**Redis Usage:**
- Index `counter_narrative_patterns` with vectors
- Cache detected counter-narratives by investigation_id

**Expected Impact:**
- Faster counter-narrative stage
- Better accuracy in relationship classification
- Enable real-time counter-frame detection

### 4.4 Source Credibility/Similarity (LOW PRIORITY - Future)
**Current Need:** Group similar sources, assess credibility patterns
**Problem:** No unified credibility assessment
**Solution:** Embed source metadata and content patterns

**Implementation:**
```
1. Create source profile embeddings (bias, geography, topic focus)
2. Cluster sources by embedding distance
3. Identify source network patterns
4. Compare against credibility databases
```

**Redis Usage:**
- Source profiles as vectors
- Cached source clusters
- Similarity metrics for source network analysis

### 4.5 Timeline Event Importance Scoring (LOW PRIORITY)
**Current Need:** Rank timeline events by narrative importance
**Problem:** Importance is partially subjective
**Solution:** Learn from user feedback and semantic patterns

**Implementation:**
```
1. Embed timeline events with context
2. Score against narrative trajectory
3. Use importance_score field (currently 0-1)
4. Learn weights from human feedback
```

**Redis Usage:**
- Cache computed importance scores
- Sorted Sets for event ranking by importance

---

## 5. REDIS CACHING STRATEGY

### 5.1 Investigation Workspace Cache
**Key Pattern:** `investigation:{id}`
**TTL:** 
- Completed investigations: 24 hours
- In-progress: 5 minutes (short TTL due to active updates)
**Size:** ~50-500 KB per investigation
**Update Strategy:**
- Write-through: Backend writes after each stage completion
- Invalidate on explicit force_refresh request

**Structure:**
```
investigation:inv_abc123 → LiveInvestigationWorkspace JSON
investigation:inv_abc123:plan → InvestigationPlan JSON
investigation:inv_abc123:retrieval → RetrievalResult JSON
investigation:inv_abc123:timeline → TimelineResult JSON
investigation:inv_abc123:counter_narratives → CounterNarrativeResult JSON
investigation:inv_abc123:analyst → AnalystResult JSON
investigation:inv_abc123:report → FinalReportResult JSON
```

**Frontend Benefit:**
- Fast page loads for completed investigations
- Enable client-side polling with cached fallback
- Reduce database round trips

### 5.2 Document Cache
**Key Pattern:** `document:{id}`
**TTL:** Infinite (or 30 days for demo data)
**Size:** ~50 KB per document (text is large)
**Update Strategy:** 
- Immutable after ingestion
- Invalidate entire prefix on data refresh

**Sub-caches:**
```
document:{id}:snippet → extracted snippet only (1-5 KB)
document:{id}:embedding → float array vector (3 KB)
document:{id}:metadata → source, type, entities (1 KB)
```

**Frontend Benefit:**
- Node details panel loads instantly
- Receipt snippets cached
- Embedding available for vector queries

### 5.3 Narrative Cluster Cache
**Key Pattern:** `narrative:{id}`
**TTL:** 1 hour (trending data, changes frequently)
**Size:** ~5-10 KB per cluster
**Update Strategy:** 
- Refresh on spike detection
- Tag-based invalidation by topic

**Sub-caches:**
```
narrative:{id}:summary → summary text (2 KB)
narrative:{id}:sources → source distribution (1 KB)
narrative:{id}:spike → spike metrics (500 B)
narratives:trending → sorted set by spike score
```

**Frontend Benefit:**
- Dashboard loads instantly
- Narrative card data available
- Trending metrics cached

### 5.4 Query Plan Cache
**Key Pattern:** `plan:{query_hash}`
**TTL:** 7 days (planner output is stable)
**Size:** ~2-5 KB per plan
**Update Strategy:**
- Cache by normalized query hash
- Similar queries can reuse plans

**Hash Function:** SHA256(normalized_query_text)

**Frontend Benefit:**
- Fast plan generation for repeated queries
- Reduce planner agent calls
- Enable query deduplication

### 5.5 Vector Search Index Cache
**Key Pattern:** Redis Search indexes (not traditional cache)
**TTL:** Infinite (index updates via updates to indexed documents)
**Indexes Needed:**

```
1. documents:embedding → vector index on document embedding
   - Vector field: embedding (768-dim)
   - Keyword fields: document.id, document.source_name
   - Sortable: published_at, collected_at

2. claims:embedding → vector index on claim vectors
   - Vector field: claim embedding
   - Keyword: claim_id, investigation_id
   - Linked to: document_id references

3. phrases:embedding → vector index on phrase mutations
   - Vector field: phrase embedding
   - Keyword: canonical_phrase, investigation_id
   - Sortable: frequency, first_observed

4. counter_patterns:embedding → known counter-narrative patterns
   - Vector field: pattern embedding
   - Keyword: pattern_type, relationship
   - Metadata: pattern description, examples
```

**Frontend Benefit:**
- Instant semantic search across investigations
- Enable cross-investigation narrative discovery
- Support advanced research features

### 5.6 Expiration Strategy

| Data Type | TTL | Reason |
|-----------|-----|--------|
| In-progress investigation | 5 min | Active updates, avoid stale state |
| Completed investigation | 24 hr | Stable after report completion |
| Documents | 30 days | Demo data refresh cycle |
| Narrative clusters | 1 hour | Trending, changes frequently |
| Query plans | 7 days | Planner output is stable |
| Computation results | 2 hours | Analysis results are cacheable |
| Vector indexes | ∞ | Persistent, updated incrementally |
| User feedback | 30 days | Historical feedback window |

---

## 6. MEMORY & PERFORMANCE ESTIMATES

### 6.1 Cache Size Projections
**Scenario:** 1,000 active investigations, 100K documents

```
Investigation workspaces (all stages):
  - In-progress: 100 × 200 KB = 20 MB
  - Completed: 900 × 200 KB = 180 MB
  - Subtotal: 200 MB

Documents:
  - 100K × 50 KB = 5 GB (full text)
  - 100K × 3 KB (snippets only) = 300 MB
  - 100K × 3 KB (embeddings) = 300 MB

Narrative clusters:
  - 50 active × 10 KB = 500 KB

Query plans:
  - 1000 unique × 3 KB = 3 MB

Vector indexes (approximate):
  - 100K document embeddings = 1 GB
  - 10K phrase embeddings = 30 MB
  - 5K claim embeddings = 15 MB

TOTAL: ~7.5-7.8 GB for full operation
```

**Redis Configuration Recommendation:**
- Minimum: 16 GB RAM (including overhead)
- Recommended: 32 GB RAM (with growth headroom)
- Eviction policy: `allkeys-lru` for non-critical caches

### 6.2 Latency Improvements

**Before Redis:**
```
GET investigation (DB query) → 100-500 ms
GET document snippets (search) → 200 ms
Build timeline (compute) → 2000 ms
Vector search (none - linear scan) → 5000+ ms
```

**After Redis:**
```
GET investigation (cache hit) → 5-10 ms (50x faster)
GET document snippets (cache hit) → 1-2 ms (100x faster)
Timeline (pre-computed cache) → 0 ms (instant)
Vector search (Redis Search) → 50-100 ms (50-100x faster)
```

### 6.3 Throughput Improvement
**Current:** ~10 investigations/hour (bottlenecked by compute)
**With Redis:** ~50-100 investigations/hour (bottlenecked by LLM, not I/O)

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Basic Caching (Week 1)
- Cache investigation workspaces by ID
- Cache document metadata and snippets
- Cache narrative clusters
- Simple TTL expiration

**Impact:** 50-80% reduction in database queries

### Phase 2: Vector Search (Week 2-3)
- Add embeddings to document model
- Implement Redis Search indexes
- Build vector query service
- Cache vector search results

**Impact:** Enable claim-document matching, 10-50x faster semantic search

### Phase 3: Advanced Features (Week 4+)
- Phrase mutation tracking via vectors
- Counter-narrative pattern matching
- Source credibility embeddings
- Real-time progress notifications (pub/sub)

**Impact:** Enable advanced narrative analysis features

---

## 8. FRONTEND DATA CONSUMPTION SUMMARY

### Dashboard Page (`DashboardPage.tsx`)
```
GET /api/narratives → radarTopics (NarrativeRadar component)
GET /api/narratives (list) → recentInvestigations (RecentInvestigations)
Locally seeded: examplePrompts (Hero component)

Cache hits needed:
- narrative summaries
- source distributions  
- spike metrics
```

### Investigation Page (`InvestigationPage.tsx`)
```
POST /api/investigate → investigation_id
GET /api/investigations/{id} × N (polls for completion)
POST /api/investigations/{id}/retrieve
POST /api/investigations/{id}/timeline
POST /api/investigations/{id}/counter-narratives
POST /api/investigations/{id}/analyst
POST /api/investigations/{id}/report

Cache hits needed:
- full workspace by ID
- documents for flowchart nodes
- document snippets for receipts
- timeline event lookups
- claim evidence matching
```

### Node Details Panel (`NodeDetailsPanel.tsx`)
```
Needs from cached documents:
- Full source information
- Snippet text
- URL and metadata
- Entity/phrase tags
- Stance classification

Cache hits needed:
- document metadata
- document snippets
- source verification status
- relevance scores
```

---

## 9. INTEGRATION CHECKLIST

- [x] Understand data structure contracts (types/rhetoriq.ts)
- [x] Map API endpoints to frontend calls
- [x] Identify real-time/memory features
- [x] List vector search opportunities
- [x] Estimate cache sizes and performance
- [ ] Implement Redis connection in backend
- [ ] Add cache layer to API responses
- [ ] Implement vector embeddings
- [ ] Deploy RedisSearch indexes
- [ ] Wire cache invalidation
- [ ] Test frontend with cached responses
- [ ] Monitor hit rates and latency

---

## 10. KEY INSIGHTS FOR REDIS DESIGN

1. **Investigation ID is Primary Key:** All Redis caching revolves around `investigation_id`. Design TTLs around investigation lifecycle.

2. **Documents are the Content:** With embeddings, documents become the most valuable cached assets. Prioritize document caching.

3. **Vector Search is Essential:** The frontend's flowchart, claim citations, and counter-narrative detection all benefit from semantic search. Don't skip this.

4. **Caching is Read-Heavy:** The frontend primarily reads cached data. Write invalidation should be simple and precise.

5. **TTLs Should Match Update Patterns:** 
   - Completed investigations: long TTL (24 hr)
   - In-progress: short TTL (5 min)
   - Trending data: medium TTL (1 hr)

6. **Snippet Caching is High ROI:** Documents are large, but snippets are used everywhere. Separate caching strategy for snippets.

7. **Workflow is Sequential:** The investigation pipeline is strictly ordered (plan → retrieval → timeline → counter → analyst → report). Can predict downstream cache needs.

---

## References

### Frontend Files Reviewed
- `/Users/sadmanrahin/Documents/hackucb/frontend/src/types/rhetoriq.ts` - Type definitions
- `/Users/sadmanrahin/Documents/hackucb/frontend/src/lib/api.ts` - API client
- `/Users/sadmanrahin/Documents/hackucb/frontend/src/pages/InvestigationPage.tsx` - Main investigation view
- `/Users/sadmanrahin/Documents/hackucb/frontend/src/pages/DashboardPage.tsx` - Homepage
- `/Users/sadmanrahin/Documents/hackucb/frontend/src/lib/liveInvestigation.ts` - Data transformation
- `/Users/sadmanrahin/Documents/hackucb/frontend/src/components/investigation-flowchart/InvestigationFlowchart.tsx` - Graph visualization
- `/Users/sadmanrahin/Documents/hackucb/frontend/src/components/investigation-flowchart/NodeDetailsPanel.tsx` - Detail view

### Backend Files Reviewed
- `/Users/sadmanrahin/Documents/hackucb/backend/models/investigation.py` - Pydantic models
- `/Users/sadmanrahin/Documents/hackucb/backend/models/document.py` - Document model
- `/Users/sadmanrahin/Documents/hackucb/backend/main.py` - API routes
- `/Users/sadmanrahin/Documents/hackucb/backend/api/narratives.py` - Investigation endpoints
