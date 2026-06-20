# Redis Integration - Next Steps

## ✅ What's Done (Phase 1: Core Infrastructure)

You now have:

1. **`backend/services/embedding_service.py`** - Generate 384-dim semantic embeddings
2. **`backend/services/redis_vector_store.py`** - Vector similarity search using RediSearch
3. **`backend/services/investigation_cache.py`** - Investigation workspace caching with RedisJSON
4. **`backend/setup_redis.py`** - Setup script to initialize indices and test
5. **`backend/tests/test_embedding_service.py`** - Embedding service unit tests
6. **`backend/tests/test_redis_vector_store.py`** - Vector store unit tests
7. **Updated `backend/config.py`** - Redis configuration settings
8. **Updated `backend/requirements.txt`** - Added redis-om and numpy

## 🚀 Quick Start (Next 15 minutes)

### Step 1: Install Redis Stack (5 min)

**Option A: Docker (Recommended)**
```bash
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

**Option B: Redis Cloud (No Docker)**
1. Go to https://redis.com/try-free/
2. Create free database with Redis Stack
3. Copy connection string

### Step 2: Update Environment Variables (2 min)

Edit `backend/.env`:

```bash
# If using Docker (default)
REDIS_URL=redis://localhost:6379

# If using Redis Cloud
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT

# Enable Redis features
ENABLE_VECTOR_SEARCH=true
ENABLE_INVESTIGATION_CACHE=true
CACHE_TTL_SECONDS=3600

# Embedding config (defaults are fine)
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

### Step 3: Install Dependencies (3 min)

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `redis-om==0.2.1` - RedisJSON support
- `numpy==1.26.4` - Vector operations
- `sentence-transformers` (already installed)

### Step 4: Run Setup Script (5 min)

```bash
cd backend
python setup_redis.py
```

This will:
- Test Redis connection
- Create RediSearch vector index
- Optionally index demo documents (50 docs, ~1-2 min)
- Test semantic search
- Test investigation caching
- Show health status

**Expected Output:**
```
✅ Redis connected: redis://localhost:6379
✅ Vector index created successfully
✅ Indexed 50 documents with embeddings
✅ Vector search working!
✅ Investigation cache working!
```

## 📊 What You Can Do Now

### 1. Test Semantic Search

```python
from services.redis_vector_store import RedisVectorStore

store = RedisVectorStore()
results = store.semantic_search("climate policy costs", limit=5)

for result in results:
    print(f"{result.title} (score: {result.score:.3f})")
```

### 2. Test Investigation Caching

```python
from services.investigation_cache import get_investigation_cache

cache = get_investigation_cache()
workspace = cache.get_workspace("inv_12345")

if workspace:
    print("Cache hit! ✅")
else:
    print("Cache miss")
```

### 3. Run Unit Tests

```bash
cd backend
pytest tests/test_embedding_service.py -v
pytest tests/test_redis_vector_store.py -v
```

## 🎯 Phase 2: Wire Into Backend (Next Tasks)

Now that infrastructure is ready, next steps:

### Task 1: Enable Semantic Search in Retriever Agent (2-3 hours)

**File:** `backend/agents/retriever_agent.py`

**Changes:**
1. Import `RedisVectorStore` and `get_embedding_service()`
2. In `_retrieve_from_local_corpus()`, use vector search for `plan.semantic_queries`
3. Combine vector search results with keyword search results
4. Rank by: `keyword_score * 0.4 + semantic_score * 0.6`

**Example:**
```python
# Add to RetrieverAgent.__init__
from services.redis_vector_store import get_redis_vector_store
self._vector_store = get_redis_vector_store()

# In _retrieve_from_local_corpus, for semantic queries:
if self._vector_store and plan.semantic_queries:
    for query in plan.semantic_queries:
        vector_results = self._vector_store.semantic_search(query, limit=10)
        # Convert to documents and merge with keyword results
```

### Task 2: Add Investigation Caching to API (1-2 hours)

**File:** `backend/api/narratives.py`

**Changes:**
1. Import `get_investigation_cache()`
2. In `GET /investigations/{id}`, check cache first
3. After each POST endpoint (retrieve, timeline, etc.), update cached artifact

**Example:**
```python
from services.investigation_cache import get_investigation_cache

_cache = get_investigation_cache()

@router.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: str):
    # Try cache first
    if _cache:
        workspace = _cache.get_workspace(investigation_id)
        if workspace:
            return workspace

    # Cache miss: load from SQLite
    workspace = _investigation_repo.get_workspace(investigation_id)

    # Cache for future requests
    if _cache and workspace:
        _cache.cache_workspace(workspace, ttl_seconds=3600)

    return workspace
```

### Task 3: Generate Embeddings for All Demo Documents (30 min)

**Create:** `backend/scripts/generate_embeddings.py`

```python
from demo_data import ALL_DOCUMENTS
from services.redis_vector_store import RedisVectorStore

store = RedisVectorStore()
store.create_index(dimension=384)
added = store.add_documents_batch(ALL_DOCUMENTS, generate_embeddings=True)
print(f"Indexed {added} documents with embeddings")
```

Run once to prepare demo:
```bash
python backend/scripts/generate_embeddings.py
```

## 📈 Performance Gains to Expect

| Operation | Before Redis | After Redis | Improvement |
|-----------|-------------|-------------|-------------|
| Get investigation workspace | 100-200ms | 10-20ms | **10-20x** |
| Semantic document search | N/A | 8-12ms | **New capability** |
| Find similar phrases | N/A | 15-25ms | **New capability** |
| Trending phrases query | 50-100ms | 2-5ms | **20x** |

## 🏆 Sponsor Evidence to Collect

For **Redis Sponsor Track** submission, document:

### 1. Agent Memory Example
- Show `RetrieverAgent` storing round effectiveness in Redis
- Demonstrate agent learning from prior rounds

### 2. Vector Search Performance
- Before/after semantic query response time
- Example: "Find documents about climate costs" → returns semantically similar docs

### 3. Investigation Caching Impact
- API response time comparison (cache hit vs miss)
- Show 10-100x speedup for repeated requests

### 4. Beyond Caching Use Cases
- **Agent Memory**: Agents remember what queries worked
- **Semantic Search**: Find similar content by meaning, not keywords
- **Context Retrieval**: Auto-match claims to supporting evidence

Create `docs/REDIS_SPONSOR_INTEGRATION.md` with screenshots and metrics.

## 🐛 Troubleshooting

### "ERR unknown command 'FT.CREATE'"
**Problem:** Redis Core installed instead of Redis Stack

**Solution:**
```bash
docker stop redis
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

### "ModuleNotFoundError: No module named 'sentence_transformers'"
**Problem:** Dependencies not installed

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### "Redis connection failed"
**Problem:** Redis not running

**Solution:**
```bash
# Check if running
docker ps | grep redis-stack

# If not, start it
docker start redis-stack

# Or run new container
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

### Embeddings generation is slow
**Problem:** CPU-only inference

**Solution:** Use batch processing (already implemented) or smaller model

## 📚 Additional Resources

- **Redis Integration Plan:** `redis_integration.md` (comprehensive guide)
- **Sponsor Strategy:** `RhetoriQ_Sponsor_Agent_Integration.md`
- **Redis Stack Docs:** https://redis.io/docs/stack/
- **RediSearch Vector Docs:** https://redis.io/docs/interact/search-and-query/search/vectors/

## ✅ Checklist

### Phase 1: Core Infrastructure (COMPLETE)
- [x] Core services created (embedding, vector store, cache)
- [x] Configuration updated (config.py, requirements.txt)
- [x] Unit tests written
- [x] Documentation created
- [ ] Redis Cloud account created ← **YOU ARE HERE**
- [ ] Redis Stack running (Docker or cloud)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` updated with `REDIS_URL`
- [ ] Setup script run successfully (`python backend/setup_redis.py`)
- [ ] Unit tests passing

### Phase 2: Backend Integration (TODO - See whats_left.md #7-11)
- [ ] Semantic search wired into Retriever Agent
- [ ] Investigation caching added to API endpoints
- [ ] Claim-to-evidence auto-matching enabled
- [ ] Demo documents indexed with embeddings

### Phase 3: Testing & Evidence (TODO - See whats_left.md #12-14)
- [ ] Live integration testing complete
- [ ] Sponsor track evidence collected (screenshots)
- [ ] Performance benchmarks documented

**Questions?** Check `redis_integration.md` for detailed implementation guidance.

---

**Current Status:** Phase 1 infrastructure is code-complete. Run setup script first, then move to Phase 2 integration.

**See:** `whats_left.md` for complete task breakdown with time estimates.
