# Arize Sponsor Integration

## What Arize Does In RhetoriQ

Arize is the AI observability and grounding-quality layer. RhetoriQ uses it to trace model calls across the investigation pipeline and emit a grounding eval for the final report.

This matters because RhetoriQ is not just producing prose. It is producing civic intelligence, so the team needs visibility into model inputs, outputs, latency, failures, and how well final claims are backed by receipts.

## How Arize Was Added

Configuration lives in `backend/config.py`:

- `ARIZE_API_KEY`
- `ARIZE_SPACE_ID`

Core implementation files:

- `backend/services/arize_tracer.py` initializes Arize/OpenTelemetry tracing.
- `backend/agents/model_client.py` wraps model calls with `TracedModelClient`.
- `backend/api/arize_status.py` exposes `/api/arize/status`.
- `backend/main.py` calls `init_arize_tracing()` on startup.
- `backend/api/narratives.py` records a `grounding_eval` span during report assembly.

The tracer uses `arize.otel.register()` when credentials and the Arize package are available. If the package or credentials are missing, the integration fails closed and the app continues without tracing.

## How It Works In The Pipeline

1. FastAPI startup initializes Arize tracing.
2. The model factory builds Gemini, Groq, Ollama, or mock clients.
3. When tracing is active, the selected client is wrapped in `TracedModelClient`.
4. Each `generate_json()` call emits an Arize span with:

```text
model name
agent schema
prompt character count
response character count
latency
input preview
output preview
error state
```

5. Final report generation calls `record_grounding_eval()` with counts for verified, pending, unavailable, and total claims.
6. Arize receives a `grounding_eval` span with a computed grounding score.

## How Crucial Arize Is

Arize is high importance. RhetoriQ can run without Arize, but the project is much harder to trust, debug, or evaluate without an observability layer.

Arize is crucial for judging and iteration because it answers:

- Which agent/model call produced a questionable output?
- Did latency spike during retrieval, receipts, or report generation?
- Did the final report rely on enough verified evidence?
- Are we improving grounding over repeated runs?

## Problem Statement Fit

The problem statement requires careful civic analysis with uncertainty. Arize helps prove that the system is not an opaque chatbot. It gives the team a traceable record of how the investigation moved from prompts to artifacts to grounding scores.

## Demo Proof Points

- Show `/api/arize/status` with tracing configured and active.
- Open Arize and show spans for planner, receipts, family, counterpoints, and report-related calls.
- Show the `grounding_eval` span with verified/pending/unavailable claim counts.
- Compare a weak report run to a stronger run after receipts and skeptic checks are added.
