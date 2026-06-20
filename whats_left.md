Findings

The live hot-topics pipeline is implemented. The backend exposes a discovery-agent trending feed through `backend/api/trending.py`, the router is mounted in `backend/main.py`, the dashboard fetches the live feed from `frontend/src/pages/DashboardPage.tsx`, and radar cards start real investigations through `POST /api/trending/{topic_id}/investigate`.

The free-text investigation pipeline is also real end to end. The planner, retriever, source-diversity, timeline, counter-narrative, analyst, claim-counterpoint, and final report stages are persisted and loaded into the investigation page.

Source diversity is now a first-class investigation artifact. Retrieved documents are enriched with reusable `source_profile` metadata, the backend exposes `POST /api/investigations/{id}/source-diversity`, the workspace payload includes `source_diversity`, and the investigation page renders a dedicated source diversity panel.

Claim-level counterpoints are now a real separate stage. The backend exposes `POST /api/investigations/{id}/claim-counterpoints`, the workspace persists `claim_counterpoints`, the report can carry linked counterpoint summaries, and the node details panel can show opposing, corrective, or reframing sources projected from claim-level pairs.

The biggest remaining gap is that the investigation experience is still not spec-complete on either trust/grounding or the frontend. The page now has coverage, claims, source-diversity context, and approximate both-sides node detail, but it still lacks a distinct timeline surface, narrative family tree, multi-agent debate summary, and a stronger receipts-driven report surface with explicit support status.

Some docs are now outdated in the opposite direction. Older markdown files still describe source diversity as missing, or describe the radar/frontend wiring as still seeded or incomplete.

What Is Left

1. Build a real `Receipts Agent` or receipts-stage artifact that maps claims to support status, better snippets, verification state, and counter-evidence coverage.
2. Extend the live investigation payload with `family`, `agent_debate`, and stronger claim-level `receipts` artifacts.
3. Add the missing investigation UI sections: distinct timeline panel, narrative family tree, agent debate summary, and stronger receipts/report surface.
4. Decide whether `RecentInvestigations` should remain seeded or become a live backend-backed list.
5. Clean up docs that still describe older frontend/backend behavior, especially radar, investigation-page behavior, and the old pre-counterpoint pipeline shape.
6. Remove the temporary backend split rules from `.gitignore` when making the final full-backend cleanup pass.

Current Agents

There are currently 4 meaningful agent modules or agent-like orchestrators in the repo:

1. `Planner Agent` in `backend/agents/planner_agent.py`
2. `Retriever Agent` in `backend/agents/retriever_agent.py`
3. `Discovery Agent` in `backend/agents/discovery_agent.py`
4. `Claim Counterpoint Agent` in `backend/agents/claim_counterpoint_agent.py`

There are also deterministic investigation stages that behave like pipeline steps, but are not separate LLM agents:

1. `backend/services/source_diversity_builder.py`
2. `backend/services/timeline_builder.py`
3. `backend/services/counter_narrative_builder.py`
4. `backend/services/analyst_builder.py`
5. `backend/services/final_report_builder.py`
6. `backend/services/verification.py`
7. `backend/services/graph_builder.py`
8. `backend/services/mutation_detection.py`
9. `backend/services/spike_detection.py`
10. `backend/services/trending_ranker.py`

Possible Additional Agents

The docs still describe a broader multi-agent backbone. The next useful role-specific additions are:

1. Receipts / grounding agent.
2. Skeptic or debate agent that challenges the analyst synthesis.
3. Narrative family / mutation investigator.
4. Final adjudicator / report-language agent once skeptic and receipts exist.

Do not make every stage an LLM agent by default. Timeline building, clustering, ranking, source-profile enrichment, and basic receipt checks should stay deterministic unless the feature requires synthesis, critique, or claim review.

Recommended Next Agent

The next agent to build should be: `Receipts Agent`.

That is the highest-value next agent because:

1. The investigation page already has timeline, counter-narrative, analyst, report, source-diversity, and claim-counterpoint context, but trust still depends on stronger claim-to-evidence grounding and explicit support status.
2. A receipts agent is narrower and more defensible than jumping straight to full debate. It can upgrade both main-claim and counter-claim evidence into a real auditable layer.
3. A later skeptic/debate agent becomes much stronger if claims already have structured receipt coverage and unsupported claims are explicitly flagged.

Summary

The app now has a real live entrypoint and a persisted investigation pipeline with source diversity and claim-level counterpoints included. The next highest-value agentic addition is a receipts/grounding layer that makes both sides of the report more inspectable, flags unsupported claims, and sets up a later skeptic/debate stage.
