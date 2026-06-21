# Redis Sponsor Integration

## What Redis Does In RhetoriQ

Redis is the project's narrative memory layer. It gives RhetoriQ fast recall across investigations, semantic document search, phrase spike tracking, and cached investigation workspaces.

RhetoriQ uses Redis for more than simple caching:

- Vector search over documents with native Redis vector set commands.
- Agent memory for articles, claims, timeline events, and agent findings.
- Investigation workspace caching with RedisJSON.
- Phrase counters and trending phrase ranked sets.
- Browserbase verification-result caching so URLs are not re-opened repeatedly during demos.

## How Redis Was Added

Configuration lives in `backend/config.py`:

- `REDIS_URL`
- `REDIS_PASSWORD`
- `REDIS_DB`
- `ENABLE_VECTOR_SEARCH`
- `ENABLE_INVESTIGATION_CACHE`
- `CACHE_TTL_SECONDS`
- `EMBEDDING_CACHE_TTL_SECONDS`

Core implementation files:

- `backend/services/redis_memory.py` stores and searches article, claim, timeline-event, and agent-finding vectors.
- `backend/services/redis_vector_store.py` stores document embeddings with `VADD` and searches them with `VSIM`.
- `backend/services/investigation_cache.py` caches full investigation workspaces with RedisJSON.
- `backend/services/redis_store.py` tracks phrase counts and latest phrase mentions.
- `backend/services/trending_runtime.py` stores trending refresh locks, latest snapshots, topic hashes, and last errors.
- `backend/services/verification_cache.py` caches Browserbase receipt checks by URL hash.
- `backend/api/redis_status.py` exposes health and utilization through `/api/redis/status` and `/api/health/redis`.

The retriever and investigation APIs call Redis during real workflows. For example, `backend/agents/retriever_agent.py` indexes retrieved documents into the vector store and falls back to keyword scoring if Redis is unavailable. `backend/api/narratives.py` stores planner, retrieval, timeline, analyst, receipts, debate, and report artifacts as Redis memory items.

## How It Works In The Pipeline

1. The planner creates search and semantic queries.
2. The retriever collects candidate documents.
3. Documents are embedded and added to Redis vector sets.
4. Later investigation stages store claims, timeline nodes, and agent findings in Redis memory.
5. New investigations query Redis for similar claims and related articles before building fresh context.
6. The dashboard and status endpoints expose Redis health, counts, hit rates, and top phrases.

Important Redis key families include:

```text
rq:vset:docs
rq:doc:meta:{doc_id}
rq:memory:vset:articles
rq:memory:vset:claims
rq:memory:vset:timeline_events
rq:memory:vset:agent_findings
rq:memory:{content_type}:meta:{item_id}
rq:memory:investigation:{investigation_id}:items
rq:investigation:{investigation_id}
rq:phrase_count:{phrase}:{bucket}
rq:phrase_mentions:latest
rq:verify:{url_hash}
```

## How Crucial Redis Is

Redis is critical. Without it, RhetoriQ can still run a basic deterministic/demo investigation, but it loses the memory that makes the product feel like a narrative intelligence system instead of a one-off report generator.

Redis is crucial because the problem statement depends on continuity:

- Has this claim appeared before?
- What related claims or mutations are semantically similar?
- Which phrases are spiking?
- What did prior agents already find?
- Can repeated investigations load quickly enough for a live product?

## Problem Statement Fit

RhetoriQ's job is to trace civic narratives across time and evidence. Redis makes that possible by preserving the chain between old documents, new claims, generated findings, and retrieved context. It is the substrate that lets the system compare today's narrative against prior observations instead of treating every prompt as isolated.

## Demo Proof Points

- Show `/api/redis/status` with vector counts, memory counts, cache stats, and top phrases.
- Run a topic investigation, then call `/api/investigations/{id}/memory`.
- Query `/api/investigations/{id}/similar-claims` or `/api/investigations/{id}/related-articles`.
- Use RedisInsight to show `rq:*` keys created by a live investigation.
