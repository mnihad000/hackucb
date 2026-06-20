Findings

The portability cleanup is done. Backend config now loads `backend/.env` from the backend directory, relative SQLite paths resolve under `backend/`, the frontend builds, and the backend test suite passes.

The investigation experience is still not spec-complete on the frontend. The live page mainly renders the flowchart, key claims, and a few generic info cards in `frontend/src/pages/InvestigationPage.tsx` around lines 147 and 254. The spec still requires a distinct timeline, narrative family tree, source diversity panel, multi-agent debate summary, and receipts-driven report surface in `HACKATHON_MVP_SPEC.md` around lines 934 and 1117.

Live radar/trending is not actually wired into the app. The backend has a trending router in `backend/api/trending.py`, but `backend/main.py` only mounts health, ingest, and narratives. The dashboard still pulls hardcoded `radarTopics` and `recentInvestigations` from `frontend/src/lib/demoData.ts` via `frontend/src/pages/DashboardPage.tsx`, and the component itself still describes the radar as seeded in `frontend/src/components/dashboard/NarrativeRadar.tsx`.

The live backend contract still omits several artifacts the docs promise. `LiveInvestigationWorkspace` only carries plan, retrieval, timeline, counter_narratives, analyst, and report in `frontend/src/types/rhetoriq.ts`, matching `backend/models/investigation.py`. There is no live `source_diversity`, `family`, or `agent_debate` artifact yet.

The docs are not fully up to date with the code. `FRONTEND_DESCRIPTION.md` still says Ask RhetoriQ routes to the seeded demo and that the frontend does not call the backend yet, but the current component does POST to `/api/investigate` in `frontend/src/components/dashboard/AskRhetoriQ.tsx`. Part of what is missing is documentation cleanup and scope reconciliation.

What Is Left

1. Mount the trending router in `backend/main.py` so the backend exposes the live radar endpoint.
2. Wire the frontend dashboard radar to the backend trending endpoint instead of only using `frontend/src/lib/demoData.ts`.
3. Add the missing investigation UI sections: timeline, narrative family tree, source diversity, agent debate, and receipts/report surface.
4. Extend the live investigation payload with `source_diversity`, `family`, `agent_debate`, and stronger `receipts` data.
5. Clean up docs that still describe older frontend/backend behavior.
6. Remove the temporary backend split rules from `.gitignore` when making the final full-backend commit.

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
