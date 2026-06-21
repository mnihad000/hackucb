# RhetoriQ Sponsor Integration Overview

RhetoriQ is a civic narrative chain-of-custody system. The project investigates how public claims appear, spread, mutate, and get challenged, then turns the result into a source-grounded report with receipts.

The sponsor integrations are organized by product responsibility. Each sponsor owns a clear layer of the investigation pipeline instead of being added as a surface-level badge.

## Implemented Sponsor Layers

| Sponsor / Tool | Project Role | Crucialness | Main Files |
|---|---|---:|---|
| Redis | Narrative memory, vector retrieval, investigation cache, phrase counters | Critical | `backend/services/redis_memory.py`, `backend/services/redis_vector_store.py`, `backend/services/investigation_cache.py`, `backend/services/redis_store.py` |
| Browserbase | Live source-page verification and receipt generation | Critical | `backend/agents/browserbase_agent.py`, `backend/services/verification_cache.py`, `backend/api/browserbase_status.py` |
| Arize | LLM tracing and grounding-quality evaluation | High | `backend/services/arize_tracer.py`, `backend/agents/model_client.py`, `backend/api/arize_status.py` |
| Band | Shared multi-agent investigation room for visible agent debate | Medium-High | `backend/services/band_room.py`, `backend/api/band_status.py`, `frontend/src/pages/InvestigationPage.tsx` |
| Gemini + Groq | Runtime model providers for structured investigation agents | Critical runtime dependency | `backend/agents/model_client.py`, agent builders in `backend/agents/` and `backend/services/` |

## Planned Or Optional Sponsors

The planning docs also mention Deepgram, Sentry, Fetch AI, Orkes, and The Token Company. They are good future fits, but they are not currently first-class implemented layers in this repository. The implemented MVP story is strongest when it focuses on Redis, Browserbase, Arize, Band, and the model runtime layer.

## How The Sponsor Stack Fits The Problem Statement

The problem RhetoriQ tackles is not just answering a civic question. It is preserving the path from claim to evidence:

1. A user asks where a narrative came from or how it spread.
2. Model agents convert the question into an investigation plan.
3. Redis retrieves related documents, prior findings, phrase counters, and semantic matches.
4. Browserbase verifies source URLs before the app cites them.
5. RhetoriQ builds timeline, source-diversity, mutation, counter-narrative, receipts, debate, and final-report artifacts.
6. Band can publish the agent debate into a shared room so the reasoning process is observable.
7. Arize traces model calls and records grounding evals so the team can inspect quality, latency, failures, and overclaim risk.

This sponsor stack directly supports the core promise: RhetoriQ should say what it observed, show where it observed it, and avoid claiming more certainty than the evidence supports.

## Useful Status Endpoints

- `GET /api/redis/status`
- `GET /api/health/redis`
- `GET /api/browserbase/status`
- `GET /api/arize/status`
- `GET /api/band/status`
- `GET /health/embeddings`

## Individual Sponsor Docs

- [Redis](./REDIS.md)
- [Browserbase](./BROWSERBASE.md)
- [Arize](./ARIZE.md)
- [Band](./BAND.md)
- [Runtime Models](./RUNTIME_MODELS.md)
