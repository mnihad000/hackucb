# Band Sponsor Integration

## What Band Does In RhetoriQ

Band is the shared agent-room layer. RhetoriQ builds a multi-agent investigation locally, and Band turns that work into a visible room of agent updates.

This is no longer only a final `AgentDebateResult` sync. RhetoriQ now publishes stage events throughout the investigation pipeline and also syncs the final agent debate. That makes the process legible while it runs: planning, retrieval, source diversity, timeline, counter-narratives, analyst synthesis, skeptic review, Browserbase source verification, receipts, report drafting, final report, and debate.

## How Band Was Added

Configuration lives in `backend/config.py`:

- `BAND_API_KEY`
- `BAND_AGENT_ID`
- `BAND_ROOM_ID`
- `BAND_REST_URL`
- `BAND_WS_URL`

Core implementation files:

- `backend/services/band_room.py` syncs both stage events and agent debate artifacts into Band.
- `backend/api/band_status.py` exposes `/api/band/status`.
- `backend/api/narratives.py` publishes Band stage events as individual artifacts are built and syncs the final debate.
- `backend/services/research_loop_runner.py` publishes Band stage events during the supervised research loop.
- `frontend/src/pages/InvestigationPage.tsx` displays Band sync status, posted message count, and sync errors on the debate card.
- `backend/tests/test_band_room.py` verifies not-configured behavior, fake REST event posting, and stage-event chat reuse.

Dependency in `backend/requirements.txt`:

```text
band-sdk==1.0.0
```

## How It Works In The Pipeline

1. RhetoriQ starts or resumes an investigation.
2. `BandRoomSync` checks that the Band API key, agent ID, and SDK are available.
3. If `BAND_ROOM_ID` is set, RhetoriQ reuses that room.
4. If no room is set, RhetoriQ creates or reuses a chat for the current investigation.
5. As each pipeline artifact is built, RhetoriQ calls `sync_stage_event()`.
6. Stage events are posted for roles such as:

```text
Query Planner Agent
Retriever Agent
Source Diversity Agent
Timeline Agent
Counter-Narrative Agent
Narrative Family Agent
Analyst Agent
Skeptic Agent
Claim Counterpoint Agent
Browserbase Verification Agent
Receipts Agent
Final Report Agent
```

7. When the local `AgentDebateResult` is built, RhetoriQ also posts one event per debate role:

```text
Analyst Agent
Skeptic Agent
Receipts Agent
Counter-Narrative Agent
Safety Agent
Final Language Agent
```

8. The debate sync result is written back into the debate artifact with `band_chat_id`, `band_sync_status`, `band_message_count`, and `band_sync_error`.

## Robustness Details

The Band integration is best-effort and cannot break an investigation:

- Missing configuration returns `not_configured`.
- Empty stage content returns `skipped`.
- Sync exceptions return `failed` with an error string.
- The backend reuses a chat per investigation, so stage updates and debate messages land in the same investigation room.
- `band_room.py` includes a fallback request-object path for SDK environments where typed request classes are not importable but the REST client exists.
- Local tests use fake Band REST clients, so the integration can be validated without live Band network calls.

## How Crucial Band Is

Band is medium-high importance. It is not required for the investigation engine to function, but it makes the agent system legible and demoable.

Band is especially useful because RhetoriQ's central UX is not only "AI gives an answer." The product is about an investigation process:

- Planner scopes the investigation.
- Retriever collects evidence.
- Timeline and source-diversity agents structure the evidence.
- Analyst proposes a synthesis.
- Skeptic challenges unsupported claims.
- Browserbase Verification Agent checks cited sources.
- Receipts Agent checks evidence.
- Counter-Narrative Agent adds competing frames.
- Safety Agent softens risky language.
- Final Language Agent decides what the user should see.

Band turns that process into visible collaboration.

## Problem Statement Fit

The problem statement is about tracing contested public narratives. That requires disagreement, caution, and a visible chain of custody, not just generation. Band helps represent the process that keeps RhetoriQ from overclaiming:

- what was retrieved,
- what was verified,
- where the analyst and skeptic disagree,
- which claims were softened,
- when the final report was ready.

This makes Band a real investigation-room layer rather than a decorative chat export.

## Demo Proof Points

- Show `/api/band/status` reporting configured sync.
- Run an investigation and show Band receiving stage events as artifacts complete.
- Run `/api/investigations/{id}/agent-debate`.
- Show the UI message count indicating Band room sync.
- Open Band and show both the pipeline stage events and the six final debate role events for the same investigation.
- Point out that the Browserbase Verification Agent event appears in the same room as the other investigation stages.

## Tests Covering The Integration

- `backend/tests/test_band_room.py::test_band_room_sync_not_configured_without_credentials`
- `backend/tests/test_band_room.py::test_band_room_sync_uses_fake_rest_client`
- `backend/tests/test_band_room.py::test_band_stage_event_reuses_chat`
