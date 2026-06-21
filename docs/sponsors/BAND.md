# Band Sponsor Integration

## What Band Does In RhetoriQ

Band is the shared agent-room layer. RhetoriQ already builds an observable agent debate artifact from the investigation outputs. Band takes that debate and posts each agent's contribution into a shared investigation room.

This makes the multi-agent part of RhetoriQ visible. Instead of only showing a final answer, the project can show Analyst, Skeptic, Receipts, Counter-Narrative, Safety, and Final Language positions as room events.

## How Band Was Added

Configuration lives in `backend/config.py`:

- `BAND_API_KEY`
- `BAND_AGENT_ID`
- `BAND_ROOM_ID`
- `BAND_REST_URL`
- `BAND_WS_URL`

Core implementation files:

- `backend/services/band_room.py` syncs agent debate artifacts into Band.
- `backend/api/band_status.py` exposes `/api/band/status`.
- `backend/api/narratives.py` calls Band sync after agent debate creation.
- `frontend/src/pages/InvestigationPage.tsx` displays Band sync status, posted message count, and sync errors.
- `backend/tests/test_band_room.py` verifies not-configured behavior and fake REST event posting.

Dependency in `backend/requirements.txt`:

```text
band-sdk==1.0.0
```

## How It Works In The Pipeline

1. RhetoriQ builds the local `AgentDebateResult`.
2. `BandRoomSync` checks that the Band API key, agent ID, and SDK are available.
3. If `BAND_ROOM_ID` is set, RhetoriQ reuses that room.
4. If no room is set, RhetoriQ creates a chat for the current investigation.
5. It posts one event per agent role:

```text
Analyst Agent
Skeptic Agent
Receipts Agent
Counter-Narrative Agent
Safety Agent
Final Language Agent
```

6. The sync result is written back into the debate artifact with `band_chat_id`, `band_sync_status`, `band_message_count`, and `band_sync_error`.

## How Crucial Band Is

Band is medium-high importance. It is not required for the investigation engine to function, but it makes the agent system legible and demoable.

Band is especially useful because RhetoriQ's central UX is not only "AI gives an answer." The product is about an investigation process:

- Analyst proposes a synthesis.
- Skeptic challenges unsupported claims.
- Receipts Agent checks evidence.
- Counter-Narrative Agent adds competing frames.
- Safety Agent softens risky language.
- Final Language Agent decides what the user should see.

Band turns that process into visible collaboration.

## Problem Statement Fit

The problem statement is about tracing contested public narratives. That requires disagreement and caution, not just generation. Band helps represent the internal debate that keeps RhetoriQ from overclaiming, which is important for civic trust.

## Demo Proof Points

- Show `/api/band/status` reporting configured sync.
- Run `/api/investigations/{id}/agent-debate`.
- Show the UI message count indicating Band room sync.
- Open Band and show the six agent role events for the same investigation.
