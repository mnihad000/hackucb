# RhetoriQ

RhetoriQ is a narrative chain-of-custody system for civic claims. It traces how a public narrative appears, spreads, mutates, and gets challenged, then grounds the final report in receipts.

## Redis Agent Memory

Redis powers RhetoriQ's agent memory, vector search, embedding cache, and investigation context retrieval. Agents use Redis to avoid duplicate work and connect new claims to similar narratives seen before.

The backend stores generated embedding vectors for articles, claims, timeline events, and agent findings. It does not store SentenceTransformer model weights in Redis. New investigations can retrieve similar claims and related articles from memory before planning, and completed stages write their findings back for future investigations.

Useful endpoints:

- `GET /api/health/redis`
- `GET /health/embeddings`
- `GET /api/investigations/{id}/memory`
- `GET /api/investigations/{id}/similar-claims`
- `GET /api/investigations/{id}/related-articles`
