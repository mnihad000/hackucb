Findings

The portability cleanup is done. Backend config now loads `backend/.env` from the backend directory, relative SQLite paths resolve under `backend/`, the frontend builds, and the backend test suite passes.

The investigation experience is still not spec-complete on the frontend. The live page mainly renders the flowchart, key claims, and a few generic info cards in `frontend/src/pages/InvestigationPage.tsx` around lines 147 and 254. The spec still requires a distinct timeline, narrative family tree, source diversity panel, multi-agent debate summary, and receipts-driven report surface in `HACKATHON_MVP_SPEC.md` around lines 934 and 1117.

Live radar/trending is not actually wired into the app. The backend has a trending router in `backend/api/trending.py`, but `backend/main.py` only mounts health, ingest, and narratives. The dashboard still pulls hardcoded `radarTopics` and `recentInvestigations` from `frontend/src/lib/demoData.ts` via `frontend/src/pages/DashboardPage.tsx`, and the component itself still describes the radar as seeded in `frontend/src/components/dashboard/NarrativeRadar.tsx`.

The live backend contract still omits several artifacts the docs promise. `LiveInvestigationWorkspace` only carries plan, retrieval, timeline, counter_narratives, analyst, and report in `frontend/src/types/rhetoriq.ts`, matching `backend/models/investigation.py`. There is no live `source_diversity`, `family`, or `agent_debate` artifact yet.

The docs are not fully up to date with the code. `FRONTEND_DESCRIPTION.md` still says Ask RhetoriQ routes to the seeded demo and that the frontend does not call the backend yet, but the current component does POST to `/api/investigate` in `frontend/src/components/dashboard/AskRhetoriQ.tsx`. Part of what is missing is documentation cleanup and scope reconciliation.

What Is Left

## Core Backend/Frontend Integration

1. Mount the trending router in `backend/main.py` so the backend exposes the live radar endpoint.
2. Wire the frontend dashboard radar to the backend trending endpoint instead of only using `frontend/src/lib/demoData.ts`.
3. Add the missing investigation UI sections: timeline, narrative family tree, source diversity, agent debate, and receipts/report surface.
4. Extend the live investigation payload with `source_diversity`, `family`, `agent_debate`, and stronger `receipts` data.
5. Clean up docs that still describe older frontend/backend behavior.
6. Remove the temporary backend split rules from `.gitignore` when making the final full-backend commit.

## Redis Sponsor Integration (Phase 2 & 3)

**Status:** Infrastructure complete (Phase 1), but not wired into backend yet.

**Created (Phase 1 - DONE):**
- `backend/services/embedding_service.py` - 384-dim semantic embeddings
- `backend/services/redis_vector_store.py` - RediSearch vector similarity search
- `backend/services/investigation_cache.py` - RedisJSON workspace caching
- `backend/setup_redis.py` - Setup script and testing
- `backend/tests/test_embedding_service.py` - Unit tests
- `backend/tests/test_redis_vector_store.py` - Unit tests
- Updated `backend/config.py` with Redis settings
- Updated `backend/requirements.txt` with redis-om, numpy

**Documentation (Phase 1 - DONE):**
- `redis_integration.md` - Full implementation guide (1060 lines)
- `REDIS_NEXT_STEPS.md` - Quick start guide
- `docs/REDIS_SPONSOR_INTEGRATION.md` - Sponsor evidence template

**Still TODO (Phase 2 - Integration):**

7. **Run Redis setup** (if not done): `python backend/setup_redis.py`
   - Tests Redis Cloud connection
   - Creates RediSearch vector index
   - Indexes demo documents with embeddings
   - Verifies semantic search and caching work

8. **Wire semantic search into Retriever Agent** (2-3 hours):
   - Edit `backend/agents/retriever_agent.py`
   - Add `RedisVectorStore` import and initialization
   - Use vector search for `plan.semantic_queries` instead of just keyword search
   - Combine vector results with keyword results (weighted ranking)
   - Store agent round memory in Redis for query optimization

9. **Add investigation caching to API endpoints** (1-2 hours):
   - Edit `backend/api/narratives.py`
   - Import `InvestigationCache` and initialize
   - In `GET /api/investigations/{id}`, check cache before SQLite
   - After each POST stage endpoint (retrieve, timeline, etc.), update cached artifact
   - Add cache statistics endpoint for monitoring

10. **Enable claim-to-evidence auto-matching** (1-2 hours):
    - Edit `backend/services/final_report_builder.py`
    - Use vector search to match each claim to supporting document snippets
    - Generate citations automatically based on semantic similarity
    - Add to `FinalReportClaim.citations` field

11. **Generate embeddings for demo documents** (30 min):
    - Create `backend/scripts/generate_embeddings.py`
    - Batch-generate embeddings for `ALL_DOCUMENTS` from `demo_data.py`
    - Store in Redis vector store for testing

**Still TODO (Phase 3 - Testing & Evidence):**

12. **Live integration testing** (30 min):
    - Start backend with Redis connected
    - Run full investigation with semantic queries
    - Verify caching reduces API response times
    - Test agent memory persistence across rounds

13. **Collect sponsor track evidence**:
    - Screenshot Redis Cloud dashboard showing active database
    - Screenshot semantic search results from investigations
    - Screenshot investigation cache hit/miss stats
    - Measure before/after performance (cache hit vs miss)
    - Document agent memory examples in RedisInsight
    - Update `docs/REDIS_SPONSOR_INTEGRATION.md` with evidence

14. **Performance benchmarking**:
    - Measure investigation workspace fetch: cached vs uncached
    - Measure semantic search latency for various query sizes
    - Document cache hit rate over typical investigation workflow
    - Show 10-100x improvement metrics for sponsor judges

**Redis Integration Files:**
```
backend/
  services/
    embedding_service.py          ✅ Complete
    redis_vector_store.py          ✅ Complete
    investigation_cache.py         ✅ Complete
  agents/
    retriever_agent.py             ❌ Needs vector search integration
  api/
    narratives.py                  ❌ Needs caching integration
  services/
    final_report_builder.py        ❌ Needs claim-to-evidence matching
  setup_redis.py                   ✅ Complete
  tests/
    test_embedding_service.py      ✅ Complete
    test_redis_vector_store.py     ✅ Complete

docs/
  redis_integration.md             ✅ Complete
  REDIS_NEXT_STEPS.md             ✅ Complete
  REDIS_SPONSOR_INTEGRATION.md    ⚠️  Needs evidence screenshots
```

Current Agents

There are currently 2 real agent modules:

1. `Planner Agent` in `backend/agents/planner_agent.py`
2. `Retriever Agent` in `backend/agents/retriever_agent.py`

There are also deterministic investigation stages that behave like pipeline steps, but are not separate LLM agents:

1. `backend/services/timeline_builder.py`
2. `backend/services/counter_narrative_builder.py`
3. `backend/services/analyst_builder.py`
4. `backend/services/final_report_builder.py`
5. `backend/services/verification.py`
6. `backend/services/graph_builder.py`
7. `backend/services/mutation_detection.py`
8. `backend/services/spike_detection.py`

Possible Additional Agents

The docs describe an 8-agent backbone. If the project follows that architecture, the next 6 likely agent roles are:

1. Timeline / chronology agent, unless kept deterministic.
2. Counter-narrative investigator.
3. Source diversity investigator.
4. Analyst / synthesis agent.
5. Skeptic agent.
6. Receipts / grounding agent.

Do not make every stage an LLM agent by default. Timeline, graph, spike detection, and basic receipt checks should stay deterministic unless the feature needs interpretation, comparison, synthesis, or critique.

Investigator vs Counter-Source Investigator

The main investigator and counter-source investigator should be different roles.

The main investigator or analyst asks: what happened, how did this narrative spread, and what does the evidence support?

The counter-source investigator asks: what credible opposing frames, corrections, rebuttals, or alternative explanations exist, and are we missing them?

That separation helps prevent the final report from becoming one-sided. For MVP, `backend/services/counter_narrative_builder.py` can remain the deterministic version of that role. Later, it can be wrapped with a real `CounterNarrativeAgent` if the product needs deeper reasoning.

Summary

The core free-text backend pipeline is there: planner, retrieval, timeline, counter-narratives, analyst, final report, and persisted workspaces are real. The biggest remaining work is product finish: live radar hookup, spec-complete investigation UI, missing family/source-diversity/debate/receipts artifacts, and a clearer multi-agent presentation.
