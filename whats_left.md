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
3. narrative family with mutation rail and active-branch highlighting
4. key claims with support status / verification state
5. source diversity
6. agent debate
7. limitations / warnings / recommended checks

The live hot-topics pipeline is also implemented. The dashboard can pull the trending feed and start live investigations from radar topics.

The biggest remaining work is no longer the core pipeline shape. The remaining work is mostly:

1. wiring real verification beyond demo mode
2. finishing remaining frontend/backend product surfaces outside the investigation page
3. deciding how much seeded demo UX should remain
4. cleaning up stale docs

What Is Left

1. Build a real non-demo verification path in `backend/services/verification.py`.
   The receipts pipeline is real, but source verification still falls back to demo fixtures and raises `NotImplementedError` in real mode.

2. Replace seeded `RecentInvestigations` with live backend-backed data if the dashboard should be fully live.
   The investigation workspace is real, but the dashboard's recent-investigation cards are still seeded frontend data.

3. Decide how much seeded demo routing should remain in the product shell.
   Some non-`inv_...` investigation routes and demo content still exist for screenshots, walkthroughs, and fallback UX.

4. Upgrade `agent_debate` from deterministic summarizer to a true skeptic/debate agent if that is still desired.
   The artifact exists and is persisted, but it is generated from observable stage outputs rather than a dedicated skeptic agent module.

5. Build the remaining optional agent roles if the full multi-agent spec is still the target.
   The useful remaining role-specific additions are:
   - Skeptic / debate agent
   - Final adjudicator / report-language agent

6. Strengthen the report surface further if you want a more explicit receipts mode.
   The page now shows support status and verification context, but a deeper claim-by-claim audit view could still be added if needed.

7. Clean up outdated docs.
   Several markdown files still describe older project state:
   - receipts as missing
   - family / debate as seeded-only
   - older frontend behavior
   - older backend stage counts

8. Remove the temporary backend split note from `.gitignore`.
   Current `.gitignore` still contains:
   `# Temporary backend split for incremental commits:`
   `# Commit 1: keep core app files only`

Done Recently

1. Narrative family is no longer heuristic-only.
   There is now a hybrid narrative family / mutation investigator agent with deterministic evidence extraction, mutation scoring, validated LLM semantic grouping, and deterministic fallback.

2. The family artifact payload is richer.
   `NarrativeFamilyResult` now includes:
   - `active_branch_id`
   - `mutation_summary`
   - `mutation_trail`
   - `generation_method`

3. The live investigation page is wired to the richer family artifact.
   The family card now renders a mutation rail, branch-type labeling, active-branch highlighting, and the semantic-framing caveat.

4. Final report and debate builders now consume family context.
   Mutation/family framing can inform summary and language decisions without changing the pipeline stage structure.

Current Agents

There are currently 6 meaningful backend agent modules in the repo:

1. `Planner Agent` in `backend/agents/planner_agent.py`
2. `Retriever Agent` in `backend/agents/retriever_agent.py`
3. `Discovery Agent` in `backend/agents/discovery_agent.py`
4. `Claim Counterpoint Agent` in `backend/agents/claim_counterpoint_agent.py`
5. `Receipts Agent` in `backend/agents/receipts_agent.py`
6. `Narrative Family Agent` in `backend/agents/narrative_family_agent.py`

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
2. family is now a real artifact and hybrid agent, so the bigger remaining trust gap is critique / softening / rejection logic
3. a later final adjudicator becomes much stronger once skeptic output is explicit

Summary

The project is no longer missing the main investigation backbone. Planner, retrieval, diversity, timeline, counter-narratives, family, analyst, claim counterpoints, receipts, agent debate, and final report are all real and persisted.

What remains is mostly the last mile:

1. real verification in non-demo mode
2. deciding how much seeded demo UX to keep
3. replacing seeded dashboard surfaces with live backend-backed data if desired
4. adding optional skeptic / adjudicator agent roles if desired
5. cleaning up docs and leftover temporary project scaffolding
