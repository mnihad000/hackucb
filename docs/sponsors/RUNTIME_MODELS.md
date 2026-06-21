# Runtime Model Layer: Gemini + Groq

## What The Runtime Models Do In RhetoriQ

Gemini and Groq provide the structured reasoning layer for RhetoriQ's agents. They power JSON-producing investigation steps such as planning, narrative-family extraction, receipts synthesis, claim counterpoints, and report-adjacent analysis.

This is the layer that turns retrieved source context into structured artifacts the rest of the app can display and verify.

## How The Runtime Layer Was Added

Configuration lives in `backend/config.py`:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GROQ_API_KEY`
- `GROQ_MODEL`

Core implementation files:

- `backend/agents/model_client.py` defines `GeminiModelClient`, `GroqModelClient`, `OllamaModelClient`, `CachedModelClient`, `MockModelClient`, and `TracedModelClient`.
- `backend/agents/planner_agent.py` uses the model client to build structured investigation plans.
- `backend/agents/narrative_family_agent.py` uses the model client for narrative family extraction.
- Other builders and agent services use model output directly or consume model-generated artifacts.

Dependencies in `backend/requirements.txt`:

```text
google-genai==1.16.0
groq==0.11.0
```

## How It Works In The Pipeline

`build_model_client()` tries providers in a controlled order:

```text
preferred provider
Gemini
Groq
Ollama
Mock
```

The client contract is simple:

```text
generate_json(system_prompt, user_prompt, schema_name) -> dict
```

That keeps each agent focused on a schema rather than provider-specific details. When Arize tracing is active, the selected model client is wrapped by `TracedModelClient` so model calls become observable spans.

## How Crucial The Runtime Layer Is

The runtime model layer is critical. Redis can retrieve evidence and Browserbase can verify URLs, but RhetoriQ still needs model reasoning to:

- interpret the user question;
- select search strategies;
- summarize narrative families;
- compare claims and counterclaims;
- draft careful, source-grounded language.

The mock client lets tests and demos keep running without credentials, but production-quality investigation depends on real model providers.

## Problem Statement Fit

RhetoriQ's problem statement requires more than search. The system must transform evidence into cautious civic analysis. Gemini and Groq provide the structured reasoning needed to plan, synthesize, challenge, and communicate that analysis while keeping outputs machine-readable for downstream verification.

## Demo Proof Points

- Show the planner output from `/api/investigate`.
- Show model-backed narrative family or receipts artifacts.
- Show Arize spans for model calls when tracing is active.
- Show graceful fallback behavior in demo mode through the mock model client.
