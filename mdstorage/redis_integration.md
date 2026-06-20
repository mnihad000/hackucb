# Redis Integration Plan for RhetoriQ

**Project:** RhetoriQ Civic AI Narrative Intelligence
**Redis Sponsor Track:** Using Redis Beyond Caching
**Focus:** Agent memory, vector search, context retrieval via Redis Stack (RedisJSON + RediSearch)

---

## Executive Summary

RhetoriQ will leverage **Redis Stack** (Redis Core + RedisJSON + RediSearch) as:

1. **Agent Memory Layer** - Planner and Retriever agents remember prior investigations, search patterns, and document retrievals
2. **Vector Search Engine** - Semantic similarity matching for claims, phrases, counter-narratives, and evidence
3. **High-Performance Cache** - Investigation workspace caching, reducing repeated computation by 50-100x
4. **Real-Time Spike Detection** - Enhanced phrase tracking with semantic clustering (already partially implemented)

**Current State:**
- ✅ Basic `PhraseStore` implemented in `backend/services/redis_store.py`
- ✅ Document model has `embedding: list[float] | None` field (currently unused)
- ❌ No vector search implementation
- ❌ No investigation caching
- ❌ No agent memory persistence

**Target State:**
- Redis Stack running with RediSearch vector indices
- All documents have 384-dim embeddings
- Agent memory persists across investigation rounds
- Sub-10ms semantic search for claims and evidence
- Investigation workspaces cached with 1-hour TTL

---

## Why Redis for RhetoriQ?

### The Problem Without Redis

1. **No Semantic Search**: Planner generates `semantic_queries` but they're unused. Retriever can't find semantically similar documents.
2. **No Agent Memory**: Every investigation round starts fresh. No learning from prior retrievals.
3. **Repeated Computation**: Frontend polls 5+ GET endpoints per investigation. Each returns full objects with no caching.
4. **Missed Counter-Narratives**: String matching misses semantic oppositions (e.g., "climate crisis" vs "weather patterns").
5. **Slow Claim Matching**: Final report builder can't efficiently match claims to supporting evidence.

### The Solution With Redis Stack

| Use Case | Redis Feature | Impact |
|----------|---------------|--------|
| Document similarity search | RediSearch vector index | Find semantically related docs in <10ms |
| Investigation caching | RedisJSON | Reduce API response time from 2-5s to <100ms |
| Agent memory | Redis Hash + JSON | Retriever remembers what queries worked |
| Phrase mutation tracking | Vector similarity | Detect "gas stove ban" → "appliance restrictions" |
| Counter-narrative detection | Cosine similarity search | Find opposing frames automatically |
| Claim-to-evidence matching | Embedding similarity | Match report claims to supporting snippets |

---

## Current Redis Implementation

### What Exists: `backend/services/redis_store.py`

The `PhraseStore` class provides:

```python
class PhraseStore:
    def record_phrase(phrase, timestamp, doc_id) -> None
    def compute_spike_score(phrase, now) -> float
    def get_top_phrases(n) -> list[tuple[str, int]]
```

**Redis keys used:**
```
rq:phrase_count:{phrase}:{YYYY-MM-DD-HH}     # Hourly mention counts
rq:phrase_docs:{phrase}:{YYYY-MM-DD-HH}      # Document IDs per phrase
rq:phrase_mentions:latest                     # Global sorted set (top phrases)
```

**What it does well:**
- Transparent fallback to in-memory when Redis unavailable
- Spike score computation (24h vs 7-day baseline)
- Top-N trending phrases

**What it doesn't do:**
- No vector search
- No embeddings
- No semantic similarity
- No investigation caching
- No agent memory

---

## Redis Stack Architecture for RhetoriQ

### Components

1. **Redis Core** (already in use)
   - Strings, Sets, Sorted Sets
   - Phrase counters, spike tracking

2. **RedisJSON** (new)
   - Store complex investigation objects as JSON
   - Query and update nested fields
   - Use for: `LiveInvestigationWorkspace`, agent memory, cached reports

3. **RediSearch** (new)
   - Full-text search indices
   - **Vector similarity search** (critical for semantic matching)
   - Hybrid queries: combine text + vector + filters

4. **Redis Streams** (optional, Phase 4)
   - Real-time pipeline status updates
   - Frontend live investigation progress

### Memory Footprint Estimate

| Data Type | Count | Size per Item | Total |
|-----------|-------|---------------|-------|
| Document embeddings (384-dim float32) | 100K | 1.5 KB | 150 MB |
| Document JSON (RedisJSON) | 100K | 3 KB | 300 MB |
| Investigation workspaces | 1K | 500 KB - 2 MB | 500 MB - 2 GB |
| Phrase counters (hourly buckets) | ~50K phrases × 168 hours | <100 bytes | 5-10 MB |
| Agent memory (per investigation) | 1K | 50-100 KB | 50-100 MB |
| **Total Estimated** | | | **~1-3 GB** for MVP |

For production: 8-16 GB Redis instance recommended. For hackathon demo: 2-4 GB sufficient.

---

## Key Integration Points

### 1. Document Embeddings & Vector Search

**Goal:** Enable semantic similarity search for documents, claims, phrases.

**Implementation:**

```python
# backend/services/embedding_service.py
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # 384-dim embeddings, fast inference
        self.model = SentenceTransformer(model_name)

    def embed_document(self, doc: Document) -> list[float]:
        # Combine title + snippet for better semantic representation
        text = f"{doc.title}. {doc.snippet or doc.text[:500]}"
        return self.model.encode(text).tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.model.encode(query).tolist()
```

**Redis Schema:**

```python
# Create RediSearch index with vector field
from redis.commands.search.field import VectorField, TextField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

index_schema = (
    TextField("$.title", as_name="title"),
    TextField("$.text", as_name="text"),
    TagField("$.source_type", as_name="source_type"),
    VectorField(
        "$.embedding",
        "FLAT",  # or "HNSW" for larger datasets
        {
            "TYPE": "FLOAT32",
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE",
        },
        as_name="embedding"
    )
)

redis_client.ft("idx:documents").create_index(
    index_schema,
    definition=IndexDefinition(prefix=["rq:doc:"], index_type=IndexType.JSON)
)
```

**Vector Similarity Query:**

```python
def semantic_search(query_embedding: list[float], limit=10):
    query = (
        Query("(*)=>[KNN $k @embedding $vec]")
        .sort_by("__embedding_score")
        .return_fields("id", "title", "source_name", "__embedding_score")
        .dialect(2)
    )

    results = redis_client.ft("idx:documents").search(
        query,
        {"k": limit, "vec": np.array(query_embedding, dtype=np.float32).tobytes()}
    )
    return results.docs
```

**Use Cases:**
- `RetrieverAgent.retrieve()` - Find documents semantically related to `plan.semantic_queries`
- `CounterNarrativeBuilder` - Find opposing frames via vector similarity
- `FinalReportBuilder` - Match claims to supporting evidence snippets

---

### 2. Investigation Workspace Caching

**Goal:** Reduce repeated computation and API response time.

**Current Flow (No Caching):**
1. Frontend: `POST /api/investigate` → Planner runs (500ms)
2. Frontend: `GET /api/investigations/{id}` → Full workspace fetch
3. Frontend: `POST /api/investigations/{id}/retrieve` → Retriever runs (2-10s)
4. Frontend: `GET /api/investigations/{id}` → Full workspace fetch again
5. Repeat for timeline, counter-narratives, analyst, report...

**Problem:** Steps 2, 4, etc. rebuild workspace from SQLite, serialize to JSON. No caching.

**Solution: RedisJSON Cache**

```python
# backend/services/investigation_cache.py
from redis import Redis
from redis.commands.json.path import Path

class InvestigationCache:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def cache_workspace(self, workspace: InvestigationWorkspace, ttl_seconds=3600):
        key = f"rq:investigation:{workspace.investigation_id}"
        self.redis.json().set(key, Path.root_path(), workspace.model_dump(mode="json"))
        self.redis.expire(key, ttl_seconds)

    def get_workspace(self, investigation_id: str) -> InvestigationWorkspace | None:
        key = f"rq:investigation:{investigation_id}"
        data = self.redis.json().get(key)
        if data:
            return InvestigationWorkspace.model_validate(data)
        return None

    def update_stage_artifact(self, investigation_id: str, stage: str, artifact: dict):
        # Update nested field in cached workspace
        key = f"rq:investigation:{investigation_id}"
        self.redis.json().set(key, Path(f".{stage}"), artifact)
```

**Wiring into API:**

```python
# backend/api/narratives.py
@router.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: str):
    # Try cache first
    workspace = investigation_cache.get_workspace(investigation_id)
    if workspace:
        return workspace

    # Cache miss: load from SQLite, then cache
    workspace = investigation_repo.get_workspace(investigation_id)
    investigation_cache.cache_workspace(workspace, ttl_seconds=3600)
    return workspace
```

**Impact:**
- Cache hit: <10ms response (vs 100-500ms without cache)
- Reduced SQLite I/O by 80%+
- Frontend gets instant workspace snapshots

---

### 3. Agent Memory

**Goal:** Agents remember prior rounds, successful queries, retrieved documents.

**Use Case 1: Retriever Agent Memory**

The `RetrieverAgent` runs multi-round retrieval. Currently, each round is independent. With Redis memory:

```python
# Store round memory
def _save_round_memory(investigation_id, round_number, queries, doc_ids, coverage):
    key = f"rq:agent_memory:retriever:{investigation_id}"
    memory = {
        "round": round_number,
        "queries": queries,
        "retrieved_doc_ids": doc_ids,
        "coverage_score": coverage.total_documents,
        "query_effectiveness": {q: len([d for d in doc_ids if q in d]) for q in queries}
    }
    redis_client.json().set(key, Path(f".rounds[{round_number-1}]"), memory)

# Read memory in next round
def _build_round_queries(plan, round_number, prior_documents):
    if round_number > 1:
        memory = redis_client.json().get(f"rq:agent_memory:retriever:{investigation_id}")
        # Avoid queries that returned no results
        ineffective_queries = [q for q, count in memory["query_effectiveness"].items() if count == 0]
        # Generate new queries, exclude ineffective ones
```

**Use Case 2: Planner Agent Memory**

```python
# When planning investigation, check if we've seen similar queries
def plan_investigation(query_text, prior_context=None):
    # Generate query embedding
    query_embedding = embedding_service.embed_query(query_text)

    # Search for similar prior investigations
    similar_investigations = semantic_search_investigations(query_embedding, limit=3)

    # If high similarity (>0.85), reuse plan structure
    if similar_investigations and similar_investigations[0].score > 0.85:
        prior_plan = similar_investigations[0].plan
        # Adapt prior plan to new query
```

**Redis Schema for Agent Memory:**

```
rq:agent_memory:planner:{investigation_id}     # JSON: prior_queries, entities, canonical_phrases
rq:agent_memory:retriever:{investigation_id}   # JSON: rounds[], query_effectiveness, coverage_timeline
rq:agent_memory:analyst:{investigation_id}     # JSON: claim_drafts, skeptic_objections, receipts_map
```

---

### 4. Enhanced Phrase Tracking with Semantic Clustering

**Current:** String-based phrase tracking in `PhraseStore`.

**Enhancement:** Detect phrase mutations via embeddings.

**Example Mutation Chain:**
```
"gas stove ban" (Jan 10)
  ↓ (cosine similarity: 0.78)
"natural gas appliance restrictions" (Jan 12)
  ↓ (cosine similarity: 0.72)
"cooking equipment mandate" (Jan 15)
```

**Implementation:**

```python
# When recording phrase, also store embedding
def record_phrase_with_embedding(phrase, timestamp, doc_id):
    # Original counter logic
    bucket = timestamp.strftime("%Y-%m-%d-%H")
    redis.incr(f"rq:phrase_count:{phrase}:{bucket}")

    # New: store phrase embedding for clustering
    embedding = embedding_service.embed_query(phrase)
    redis.json().set(f"rq:phrase_embedding:{phrase}", Path.root_path(), {
        "phrase": phrase,
        "embedding": embedding,
        "first_seen": timestamp.isoformat(),
        "total_mentions": redis.get(f"rq:phrase_total:{phrase}") or 0
    })

# Find phrase mutations
def find_phrase_mutations(canonical_phrase, similarity_threshold=0.70):
    phrase_embedding = embedding_service.embed_query(canonical_phrase)

    # Vector search across all phrase embeddings
    results = redis_client.ft("idx:phrases").search(
        Query("(*)=>[KNN 20 @embedding $vec]").dialect(2),
        {"vec": np.array(phrase_embedding, dtype=np.float32).tobytes()}
    )

    mutations = []
    for doc in results.docs:
        score = float(doc.__embedding_score)
        if 0.4 < score < 0.85:  # Semantic variation, not identical or unrelated
            mutations.append({
                "original": canonical_phrase,
                "mutation": doc.phrase,
                "similarity": score,
                "first_seen": doc.first_seen
            })
    return mutations
```

---

## Implementation Roadmap

**CURRENT STATUS:** Phase 1 is COMPLETE (code-wise). Phase 2 integration is next.

### Phase 1: Core Infrastructure (2-3 hours) ✅ COMPLETE

**Tasks:**
1. Install Redis Stack locally or provision cloud instance
2. Add dependencies to `requirements.txt`:
   ```
   redis[hiredis]==5.0.1
   redis-om==0.2.1
   ```
3. Create `backend/services/embedding_service.py`
4. Create `backend/services/redis_vector_store.py`
5. Create RediSearch indices for documents and phrases
6. Write unit tests: `backend/tests/test_redis_vector_store.py`

**Deliverables:** ✅
- [x] `backend/services/embedding_service.py` created
- [x] `backend/services/redis_vector_store.py` created
- [x] `backend/setup_redis.py` created
- [x] Unit tests written
- [ ] Redis Stack running (user needs to do this)
- [ ] Setup script executed successfully
- [ ] Vector index created and searchable

**Test Command:**
```python
# Should return semantically similar docs
results = redis_vector_store.semantic_search("climate policy costs", limit=5)
assert len(results) > 0
assert results[0].score > 0.7
```

**Next Action:** Run `python backend/setup_redis.py` with Redis Cloud credentials.

---

### Phase 2: Investigation Caching (1-2 hours) ✅ CODE COMPLETE, NOT INTEGRATED

**Tasks:**
1. Create `backend/services/investigation_cache.py`
2. Add `cache_workspace()`, `get_workspace()`, `update_stage_artifact()` methods
3. Wire into `backend/api/narratives.py`:
   - `GET /api/investigations/{id}` - Check cache first
   - After each POST stage endpoint, update cached artifact
4. Add cache stats endpoint: `GET /api/cache/stats`
5. Test cache hit/miss behavior

**Deliverables:** ✅
- [x] `backend/services/investigation_cache.py` created
- [ ] Wired into `backend/api/narratives.py` (TODO - Phase 2)
- [ ] Cache hit rate measured

**Integration Status:** Service exists but not used in API yet. See `whats_left.md` item #9.

**Test Command:**
```bash
# After Phase 2 integration:
# First call: cache miss
time curl http://localhost:8000/api/investigations/test-001
# ~200ms

# Second call: cache hit
time curl http://localhost:8000/api/investigations/test-001
# <20ms
```

---

### Phase 3: Agent Memory (3-4 hours) ⚠️ INFRASTRUCTURE READY, NOT INTEGRATED

**Tasks:**

**3A. Retriever Agent Enhancement**
1. Update `backend/agents/retriever_agent.py`:
   - Add `_save_round_memory()` method
   - Read prior round memory in `_build_round_queries()`
   - Use semantic search for `plan.semantic_queries`
2. Store retrieval memory in `rq:agent_memory:retriever:{id}`
3. Test multi-round retrieval with memory

**3B. Semantic Document Search**
1. Update `RetrieverAgent._retrieve_from_local_corpus()`:
   - Generate embeddings for all corpus documents (one-time)
   - Use vector search for semantic queries
   - Combine with keyword search results
2. Rank by: keyword_score * 0.4 + semantic_score * 0.6

**3C. Claim-to-Evidence Matching**
1. Update `backend/services/final_report_builder.py`:
   - For each claim, generate embedding
   - Vector search against document snippets
   - Return top-3 most relevant citations
2. Add to `FinalReportClaim.citations`

**Deliverables:** ⚠️
- [x] Vector search service created
- [x] Embedding service created
- [ ] Integrated into `backend/agents/retriever_agent.py` (TODO - See `whats_left.md` #8)
- [ ] Integrated into `backend/services/final_report_builder.py` (TODO - See `whats_left.md` #10)
- [ ] Round memory implementation (TODO)

**Integration Status:** Infrastructure exists but agents don't use it yet.

---

### Phase 4: Advanced Features (2-3 hours, optional) - AFTER PHASE 3

**4A. Phrase Mutation Detection**
- Implement `find_phrase_mutations()` using vector similarity
- Add to timeline and counter-narrative builders
- Show mutation chains in frontend

**4B. Counter-Narrative Semantic Detection**
- Embed main narrative canonical phrase
- Search for low-similarity but entity-overlapping documents
- Automatically flag potential counter-narratives

**4C. Real-Time Trending with Vector Clustering**
- Cluster trending phrases by semantic similarity
- Group "gas stove ban", "appliance restrictions", "cooking equipment mandate"
- Show narrative families on dashboard

**4D. Redis Streams for Live Pipeline Updates** (optional)
- Publish investigation stage completion events to Redis Stream
- Frontend subscribes via SSE or WebSocket
- Real-time progress bar without polling

---

## Data Schemas & Key Patterns

### Document Storage

```json
// RedisJSON Key: rq:doc:{doc_id}
{
  "id": "doc_001",
  "source_name": "Local Gazette",
  "source_type": "local_news",
  "title": "City council debates new energy policy",
  "text": "Full article text...",
  "snippet": "The policy was described as a hidden energy tax...",
  "embedding": [0.123, -0.456, ...],  // 384-dim vector
  "entities": ["city council", "energy policy"],
  "phrases": ["hidden energy tax", "utility costs"],
  "published_at": "2026-06-20T09:14:00Z"
}
```

### Investigation Workspace Cache

```json
// RedisJSON Key: rq:investigation:{investigation_id}
{
  "investigation_id": "inv_12345",
  "query_text": "Where did the hidden energy tax narrative come from?",
  "status": "timeline_completed",
  "current_stage": "timeline",
  "plan": { /* InvestigationPlan */ },
  "retrieval": { /* RetrievalResult */ },
  "retrieved_documents": [ /* Document[] */ ],
  "timeline": { /* TimelineResult */ },
  "counter_narratives": null,
  "analyst": null,
  "report": null,
  "created_at": "2026-06-20T13:00:00Z",
  "updated_at": "2026-06-20T13:05:30Z"
}
```

### Agent Memory

```json
// RedisJSON Key: rq:agent_memory:retriever:{investigation_id}
{
  "investigation_id": "inv_12345",
  "rounds": [
    {
      "round": 1,
      "queries": ["\"hidden energy tax\"", "energy policy costs"],
      "retrieved_doc_ids": ["doc_001", "doc_002", "doc_003"],
      "coverage_score": 3,
      "query_effectiveness": {
        "\"hidden energy tax\"": 2,
        "energy policy costs": 1
      }
    },
    {
      "round": 2,
      "queries": ["utility bill surcharge", "green mandate costs"],
      "retrieved_doc_ids": ["doc_004", "doc_005"],
      "coverage_score": 5,
      "query_effectiveness": {
        "utility bill surcharge": 1,
        "green mandate costs": 1
      }
    }
  ]
}
```

### Phrase Embeddings

```json
// RedisJSON Key: rq:phrase_embedding:{phrase}
{
  "phrase": "hidden energy tax",
  "embedding": [0.234, -0.567, ...],  // 384-dim
  "first_seen": "2026-06-20T09:14:00Z",
  "total_mentions": 47,
  "related_phrases": ["utility surcharge", "green energy costs"],
  "mutation_score": 0.0  // 0.0 = original, >0 = mutation
}
```

---

## Vector Index Definitions

### Documents Index

```python
from redis.commands.search.field import VectorField, TextField, TagField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

doc_index_schema = (
    TextField("$.title", as_name="title"),
    TextField("$.text", as_name="text"),
    TextField("$.snippet", as_name="snippet"),
    TagField("$.source_type", as_name="source_type"),
    TagField("$.source_name", as_name="source_name"),
    NumericField("$.published_at", as_name="published_at"),
    VectorField(
        "$.embedding",
        "HNSW",  # Hierarchical Navigable Small World for fast ANN search
        {
            "TYPE": "FLOAT32",
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE",
            "INITIAL_CAP": 10000,
            "M": 16,
            "EF_CONSTRUCTION": 200
        },
        as_name="embedding"
    )
)

redis_client.ft("idx:documents").create_index(
    doc_index_schema,
    definition=IndexDefinition(prefix=["rq:doc:"], index_type=IndexType.JSON)
)
```

### Phrases Index

```python
phrase_index_schema = (
    TextField("$.phrase", as_name="phrase"),
    NumericField("$.total_mentions", as_name="mentions"),
    VectorField(
        "$.embedding",
        "FLAT",  # Simple brute-force for small phrase set
        {
            "TYPE": "FLOAT32",
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        },
        as_name="embedding"
    )
)

redis_client.ft("idx:phrases").create_index(
    phrase_index_schema,
    definition=IndexDefinition(prefix=["rq:phrase_embedding:"], index_type=IndexType.JSON)
)
```

---

## Performance Estimates

### Latency

| Operation | Without Redis | With Redis | Improvement |
|-----------|---------------|------------|-------------|
| Get investigation workspace | 100-200ms (SQLite + serialize) | 5-15ms (RedisJSON) | **10-20x faster** |
| Semantic document search (100K docs) | N/A (not implemented) | 8-12ms (HNSW index) | New capability |
| Find top 50 trending phrases | 50-100ms (scan all docs) | 2-5ms (sorted set) | **20x faster** |
| Match claim to evidence (1K docs) | 500ms+ (iterate all) | 10-20ms (vector search) | **25-50x faster** |
| Phrase mutation detection | N/A | 15-25ms | New capability |

### Throughput

| Metric | Without Redis | With Redis |
|--------|---------------|------------|
| Concurrent investigations | 5-10/sec (SQLite bottleneck) | 50-100/sec |
| Document ingestion rate | 100 docs/sec | 500+ docs/sec (batch insert) |
| API requests/sec (cached) | 50-100 | 1000+ |

### Memory Usage (for 100K documents, 1K investigations)

```
Documents (JSON):           100K × 3 KB      = 300 MB
Document embeddings:        100K × 1.5 KB    = 150 MB
Investigation workspaces:   1K × 500 KB      = 500 MB
Agent memory:               1K × 50 KB       = 50 MB
Phrase counters:            50K phrases      = 10 MB
Phrase embeddings:          50K × 1.5 KB     = 75 MB
Vector indices (overhead):                     200 MB
-----------------------------------------------------------
Total:                                        ~1.3 GB
```

For production: 4-8 GB Redis instance recommended (allows for growth + overhead).

---

## Environment Variables

Add to `backend/.env`:

```bash
# Redis connection
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0

# Redis features
ENABLE_VECTOR_SEARCH=true
ENABLE_INVESTIGATION_CACHE=true
CACHE_TTL_SECONDS=3600

# Embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
BATCH_EMBED_SIZE=32

# Performance tuning
VECTOR_INDEX_TYPE=HNSW  # or FLAT for <10K docs
HNSW_M=16
HNSW_EF_CONSTRUCTION=200
```

Update `backend/config.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # Redis features
    ENABLE_VECTOR_SEARCH: bool = True
    ENABLE_INVESTIGATION_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    BATCH_EMBED_SIZE: int = 32
```

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_embedding_service.py
def test_embed_document():
    service = EmbeddingService()
    doc = Document(title="Test", text="Sample text", ...)
    embedding = service.embed_document(doc)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)

# backend/tests/test_redis_vector_store.py
def test_semantic_search():
    store = RedisVectorStore()
    store.add_document(doc1)  # "Climate change is urgent"
    store.add_document(doc2)  # "Global warming requires action"
    store.add_document(doc3)  # "Cooking recipes for dinner"

    results = store.semantic_search("environmental policy", limit=2)
    assert len(results) == 2
    assert results[0].id in [doc1.id, doc2.id]  # Not doc3

# backend/tests/test_investigation_cache.py
def test_cache_hit():
    cache = InvestigationCache(redis_client)
    cache.cache_workspace(workspace)

    retrieved = cache.get_workspace(workspace.investigation_id)
    assert retrieved.investigation_id == workspace.investigation_id
```

### Integration Tests

```python
# backend/tests/test_retriever_with_redis.py
def test_retriever_uses_semantic_search():
    plan = InvestigationPlan(
        semantic_queries=["Find evidence about narrative spread"]
    )

    # Seed Redis with documents
    redis_vector_store.add_documents(test_corpus)

    retriever = RetrieverAgent(repository=repo)
    result = retriever.retrieve(investigation_id, plan)

    # Should find documents even if exact phrase doesn't match
    assert result.retrieved_document_ids is not None
    assert len(result.retrieved_document_ids) > 0
```

### Load Tests

```bash
# Simulate 100 concurrent investigations
locust -f backend/tests/load_test_redis.py --users 100 --spawn-rate 10
```

---

## Sponsor Integration Evidence

For the **Redis Sponsor Track**, document the following in `docs/REDIS_SPONSOR_INTEGRATION.md`:

### 1. Beyond Caching: Agent Memory

**Evidence:**
- `RetrieverAgent` stores round memory in `rq:agent_memory:retriever:{id}`
- Each round reads prior query effectiveness scores
- Agents avoid repeating ineffective queries

**Code snippet:**
```python
# backend/agents/retriever_agent.py
def _build_round_queries(self, plan, round_number, prior_documents):
    if round_number > 1:
        memory = self.redis.json().get(f"rq:agent_memory:retriever:{self.investigation_id}")
        ineffective = [q for q, score in memory["query_effectiveness"].items() if score == 0]
        # Generate new queries, exclude ineffective ones
```

### 2. Beyond Caching: Vector Search for Semantic Retrieval

**Evidence:**
- RediSearch vector index on 384-dim document embeddings
- Semantic queries from Planner Agent use vector similarity
- <10ms query time for 100K documents

**Code snippet:**
```python
# backend/services/redis_vector_store.py
def semantic_search(self, query_embedding, limit=10):
    results = self.redis.ft("idx:documents").search(
        Query("(*)=>[KNN $k @embedding $vec]").dialect(2),
        {"k": limit, "vec": np.array(query_embedding).tobytes()}
    )
    return results.docs
```

### 3. Beyond Caching: Context Retrieval for Claim Matching

**Evidence:**
- Final report builder uses vector search to match claims to evidence
- Each claim gets top-3 most relevant document snippets
- Eliminates manual citation matching

**Screenshot:** Show final report with auto-generated citations

**Metrics:**
- Before Redis: Manual claim-to-evidence matching (N/A)
- After Redis: Automatic matching in 10-20ms per claim

### 4. Performance Improvement Metrics

| Metric | Before Redis | After Redis | Improvement |
|--------|--------------|-------------|-------------|
| Investigation workspace fetch | 150ms | 12ms | 12.5x |
| Semantic document search | N/A | 10ms | New feature |
| Trending phrases query | 80ms | 3ms | 26x |
| Claim-to-evidence matching | Manual | 15ms/claim | Automated |

---

## Next Steps for Implementation

### Immediate Actions (Today)

**Step 1: Install Redis Stack**
```bash
# Option A: Docker (recommended)
docker run -d --name redis-stack -p 6379:6379 \
  -p 8001:8001 redis/redis-stack:latest

# Option B: Cloud (if Docker unavailable)
# Sign up for Redis Cloud free tier: https://redis.com/try-free/
# Or Upstash: https://upstash.com/
```

**Step 2: Test Redis Connection**
```bash
cd backend
python3 -c "
from services.redis_store import PhraseStore
store = PhraseStore(redis_url='redis://localhost:6379')
print('Redis connected:', store.using_redis)
"
```

**Step 3: Update Dependencies**
```bash
cd backend
echo "redis-om==0.2.1" >> requirements.txt
pip install -r requirements.txt
```

### Phase 1: Core Infrastructure (Next 2-3 hours)

1. Create `backend/services/embedding_service.py` (copy template from this doc)
2. Create `backend/services/redis_vector_store.py`
3. Write unit tests
4. Generate embeddings for demo documents
5. Create vector indices
6. Test semantic search with 10-20 documents

### Phase 2: Investigation Caching (Next 1-2 hours)

1. Create `backend/services/investigation_cache.py`
2. Update `backend/api/narratives.py` to use cache
3. Test cache hit/miss behavior
4. Add cache stats endpoint

### Phase 3: Agent Memory (Next 3-4 hours)

1. Update `RetrieverAgent` to use semantic search
2. Implement round memory persistence
3. Update `FinalReportBuilder` for claim-to-evidence matching
4. Test end-to-end investigation with Redis

### Final: Documentation & Evidence (1 hour)

1. Create `docs/REDIS_SPONSOR_INTEGRATION.md`
2. Update `docs/CLAUDE_CODE_BUILD_LOG.md` with Redis work
3. Take screenshots of before/after performance
4. Document Redis usage for sponsor judges

---

## Redis Cloud Setup (Alternative to Local)

If local Docker unavailable, use Redis Cloud:

1. Sign up: https://redis.com/try-free/
2. Create database with Redis Stack (includes RediSearch)
3. Get connection string: `redis://default:password@host:port`
4. Update `.env`:
   ```
   REDIS_URL=redis://default:your-password@redis-12345.redis.com:12345
   ```

Free tier includes:
- 30 MB storage (enough for MVP demo)
- RediSearch + RedisJSON
- 30 connections

---

## Troubleshooting

### Issue: "ERR unknown command 'FT.CREATE'"

**Cause:** Redis Core installed instead of Redis Stack.

**Solution:**
```bash
# Stop Redis Core
docker stop redis

# Start Redis Stack
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

### Issue: Embeddings are slow to generate

**Cause:** CPU-only inference.

**Solution:**
```python
# Use smaller model for hackathon speed
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 384-dim, fast

# Or batch embed
embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
```

### Issue: Redis memory full

**Solution:**
```bash
# Check memory usage
redis-cli INFO memory

# Increase maxmemory (Docker)
docker run -d --name redis-stack -p 6379:6379 \
  redis/redis-stack:latest \
  --maxmemory 2gb --maxmemory-policy allkeys-lru
```

---

## Summary

This Redis integration transforms RhetoriQ from a stateless pipeline into an **intelligent, memory-enabled agent system**:

✅ **Agent Memory** - Infrastructure ready, needs integration into agents
✅ **Vector Search** - Service built, needs wiring into Retriever
✅ **High Performance** - Cache service ready, needs API integration
✅ **New Capabilities** - Phrase mutation detection, auto-claim matching (after integration)
⚠️ **Sponsor Evidence** - Need to run setup, integrate, and collect metrics

**Implementation Status:**
- **Phase 1 (Core Infrastructure):** ✅ COMPLETE (code-wise)
- **Phase 2 (Backend Integration):** ❌ TODO - See `whats_left.md` items #7-11
- **Phase 3 (Testing & Evidence):** ❌ TODO - See `whats_left.md` items #12-14

**Total Implementation Time:** 8-12 hours
- Phase 1: ✅ Done (3 hours)
- Phase 2: ⏳ Remaining (4-6 hours)
- Phase 3: ⏳ Remaining (1-2 hours)

**Redis Memory Required:** 1-3 GB for MVP
**Performance Gain:** 10-100x for cached operations, new semantic features (after integration)

**Next Steps:**
1. Run `python backend/setup_redis.py` with Redis Cloud credentials
2. Follow `whats_left.md` items #7-14 for integration
3. See `REDIS_NEXT_STEPS.md` for quick start guide
