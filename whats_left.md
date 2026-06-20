Findings

The investigation experience is still not spec-complete on the frontend. The live page mainly renders the flowchart, key claims, and a few generic info cards in `frontend/src/pages/InvestigationPage.tsx` around lines 147 and 254. The spec still requires a distinct timeline, narrative family tree, source diversity panel, multi-agent debate summary, and receipts-driven report surface in `HACKATHON_MVP_SPEC.md` around lines 934 and 1117.

Live radar/trending is not actually wired into the app. The backend has a trending router in `backend/api/trending.py`, but `backend/main.py` only mounts health, ingest, and narratives. The dashboard still pulls hardcoded `radarTopics` and `recentInvestigations` from `frontend/src/lib/demoData.ts` via `frontend/src/pages/DashboardPage.tsx`, and the component itself still describes the radar as seeded in `frontend/src/components/dashboard/NarrativeRadar.tsx`.

The live backend contract still omits several artifacts the docs promise. `LiveInvestigationWorkspace` only carries plan, retrieval, timeline, counter_narratives, analyst, and report in `frontend/src/types/rhetoriq.ts`, matching `backend/models/investigation.py`. There is no live source_diversity, family, or agent_debate artifact, and the agent architecture doc explicitly defers Source Diversity, Skeptic, and Receipts in `building_agents.md`.

The docs are not fully up to date with the code. `FRONTEND_DESCRIPTION.md` still says Ask RhetoriQ routes to the seeded demo and that the frontend does not call the backend yet, but the current component does POST to `/api/investigate` in `frontend/src/components/dashboard/AskRhetoriQ.tsx`. So part of what is missing is documentation cleanup and scope reconciliation.

Reliability is not fully green. I ran `pytest -q` in `backend/`: 90 tests passed, 5 failed. The failures point to an unresolved demo/live split: `backend/.env` sets `DEMO_MODE=false`, while verification still hard-fails outside demo mode in `backend/services/verification.py`, and mutation behavior changes with demo mode in `backend/services/mutation_detection.py`.

Summary

The core free-text backend pipeline is there: planner, retrieval, timeline, counter-narratives, analyst, final report, and persisted workspaces are real. What is still missing is the product-level finish: live radar hookup, spec-complete investigation UI, the missing family/source-diversity/debate/receipts artifacts, and cleanup of the demo-vs-live reliability gap.
