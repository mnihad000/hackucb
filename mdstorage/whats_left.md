Findings

The core live investigation pipeline is now real end to end.

The backend persists and serves these live investigation artifacts:

1. planner
2. retrieval
3. source diversity
4. timeline
5. counter-narratives
6. narrative family
7. analyst
8. claim counterpoints
9. receipts
10. agent debate
11. final report

The live frontend investigation page now renders dedicated surfaces for:

1. flowchart
2. timeline
3. narrative family
4. key claims with support status / verification state
5. source diversity
6. agent debate
7. limitations / warnings / recommended checks

The live hot-topics pipeline is also implemented. The dashboard can pull the trending feed and start live investigations from radar topics.

The biggest remaining work is no longer the core pipeline shape. The remaining work is mostly:

1. finishing the remaining product surfaces outside the live investigation page
2. wiring real verification beyond demo mode
3. deciding how much of the broader multi-agent architecture should become real agent modules versus deterministic builders
4. cleaning up seeded/demo content and stale docs

What Is Left

## Core Backend/Frontend Integration

1. Build a real `Receipts Agent` or receipts-stage artifact that maps claims to support status, better snippets, verification state, and counter-evidence coverage.
2. Extend the live investigation payload with `family`, `agent_debate`, and stronger claim-level `receipts` artifacts.
3. Add the missing investigation UI sections: distinct timeline panel, narrative family tree, agent debate summary, and stronger receipts/report surface.
4. Decide whether `RecentInvestigations` should remain seeded or become a live backend-backed list.
5. Clean up docs that still describe older frontend/backend behavior, especially radar, investigation-page behavior, and the old pre-counterpoint pipeline shape.
6. Remove the temporary backend split rules from `.gitignore` when making the final full-backend cleanup pass.

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

There are currently 5 meaningful backend agent modules in the repo:

1. `Planner Agent` in `backend/agents/planner_agent.py`
2. `Retriever Agent` in `backend/agents/retriever_agent.py`
3. `Discovery Agent` in `backend/agents/discovery_agent.py`
4. `Claim Counterpoint Agent` in `backend/agents/claim_counterpoint_agent.py`
5. `Receipts Agent` in `backend/agents/receipts_agent.py`

There are also deterministic investigation stages that behave like pipeline steps rather than separate LLM agents:

1. `backend/services/source_diversity_builder.py`
2. `backend/services/timeline_builder.py`
3. `backend/services/counter_narrative_builder.py`
4. `backend/services/narrative_family_builder.py`
5. `backend/services/analyst_builder.py`
6. `backend/services/agent_debate_builder.py`
7. `backend/services/final_report_builder.py`
8. `backend/services/verification.py`
9. `backend/services/graph_builder.py`
10. `backend/services/mutation_detection.py`
11. `backend/services/spike_detection.py`
12. `backend/services/trending_ranker.py`

Recommended Next Priorities

If the goal is product robustness rather than just more architecture, the highest-value next work is:

1. real verification outside demo mode
2. replacing seeded `RecentInvestigations` with live backend-backed data
3. doc cleanup so repo docs stop contradicting the current implementation

If the goal is the broader multi-agent system specifically, the highest-value next agent is:

1. `Skeptic Agent`

That is the next best agent because:

1. receipts already exist and can now ground objections
2. family already exists as an artifact, so the bigger remaining trust gap is critique / softening / rejection logic
3. a later final adjudicator becomes much stronger once skeptic output is explicit

Summary

The project is no longer missing the main investigation backbone. Planner, retrieval, diversity, timeline, counter-narratives, family, analyst, claim counterpoints, receipts, agent debate, and final report are all real and persisted.

What remains is mostly the last mile:

1. real verification in non-demo mode
2. deciding how much seeded demo UX to keep
3. adding optional skeptic / adjudicator agent roles if desired
4. cleaning up docs and leftover temporary project scaffolding
