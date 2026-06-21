# Browserbase Sponsor Integration

## What Browserbase Does In RhetoriQ

Browserbase is the source verification layer. RhetoriQ should not cite a public source just because a retriever found a URL. Browserbase lets the backend open the page in a real browser session, extract live metadata, compare the page against stored document metadata, and produce a receipt.

The important implementation detail is that Browserbase is now part of the investigation contract, not a side demo. RhetoriQ builds and persists a `SourceVerificationResult` artifact for cited or high-relevance sources. Receipt generation then consumes those verification states before the final report is annotated.

## How Browserbase Was Added

Configuration lives in `backend/config.py`:

- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`

Core implementation files:

- `backend/agents/browserbase_agent.py` defines `BrowserbaseAgent` and the `Receipt` object.
- `backend/services/source_verification_builder.py` converts Browserbase checks into the persisted `SourceVerificationResult` artifact.
- `backend/services/verification_cache.py` caches verification results in Redis for 24 hours.
- `backend/services/investigation_repository.py` persists and reloads `source_verification_results`.
- `backend/api/narratives.py` runs source verification before receipts/report generation and exposes `POST /api/investigations/{id}/source-verification`.
- `backend/api/browserbase_status.py` exposes `/api/browserbase/status`.
- `backend/services/research_loop_runner.py` runs Browserbase source verification inside the supervised research loop before receipts are built.
- `frontend/src/pages/InvestigationPage.tsx` displays the source verification panel with status counts, backend mix, and checked source links.

Dependencies are listed in `backend/requirements.txt`:

```text
browserbase==1.13.0
playwright==1.60.0
```

## How It Works In The Pipeline

1. Retrieval returns candidate `Document` objects with URLs, titles, timestamps, and snippets.
2. The report and claim-counterpoint builders decide which documents are actually cited.
3. `build_source_verification()` selects cited documents, or high-relevance retrieved documents if no report exists yet.
4. `BrowserbaseAgent.verify_documents()` checks Redis verification cache first.
5. If there is no cached result and Browserbase is configured, the agent creates a Browserbase session.
6. Playwright connects to that session over CDP and opens the URL.
7. The agent extracts the live title and page HTML.
8. The agent compares live content to stored title/snippet metadata.
9. The result is persisted as `SourceVerificationResult` with per-source receipts, status counts, backend counts, and limitations.
10. Receipt generation turns those source states into claim-level verification states for the final report.

Browserbase raw statuses:

```text
verified
source_updated
blocked
unavailable
needs_manual_review
```

RhetoriQ maps those into report-safe receipt states:

```text
verified
metadata_mismatch
unavailable
pending
```

The artifact also records which backend produced each result:

```text
browserbase
httpx_fallback
cache
demo_fixture
not_verified
```

If Browserbase is not configured, the project falls back to `httpx` so local development still works. That fallback is explicit in `backend_counts` and `fallback_checked_count`, so a demo can distinguish true Browserbase verification from local fallback checks.

## Persisted Artifact

`SourceVerificationResult` is saved in SQLite and returned in the investigation workspace:

- `investigation_id`
- `receipts`
- `status_counts`
- `backend_counts`
- `verified_count`
- `browserbase_verified_count`
- `fallback_checked_count`
- `pending_count`
- `unavailable_count`
- `metadata_mismatch_count`
- `limitations`
- `cached`

This means Browserbase verification survives page reloads, appears in the workspace API, and can be shown directly in the frontend.

## How Crucial Browserbase Is

Browserbase is critical for the trust layer. Without it, the app can still assemble an investigation report, but it cannot demonstrate that a cited source page was actually opened and checked during the pipeline.

Browserbase is crucial because civic narrative analysis is sensitive:

- URLs can go stale.
- Pages can change after indexing.
- Paywalls, 403s, and unavailable pages need to be marked honestly.
- The report should distinguish a verified receipt from an unchecked candidate source.

## Problem Statement Fit

The problem statement asks RhetoriQ to trace narratives with evidence. Browserbase makes the evidence side credible by turning source URLs into receipt objects, then carrying those receipt states into claim-level support and final report confidence.

This is a robust fit because the verification result is not just a status page:

- It runs inside the report/receipts path.
- It runs inside the supervised research loop.
- It persists as an artifact.
- It is visible in the workspace UI.
- It records limitations when real Browserbase is unavailable or a source cannot be checked.

## Demo Proof Points

- Show `/api/browserbase/status` reporting `backend: browserbase` when configured.
- Run `POST /api/investigations/{id}/source-verification` and show the persisted source verification artifact.
- Run an investigation report and show that receipt statuses came from the source verification artifact.
- Show `rq:verify:*` cache entries in Redis after verification.
- In the UI, point to the Source verification panel: verified count, Browserbase count, fallback count, unavailable/pending/mismatch counts, and checked source links.

## Tests Covering The Integration

- `backend/tests/test_source_verification_builder.py`
- `backend/tests/test_investigation_repository.py::test_source_verification_result_persists_and_loads_in_workspace`
- `backend/tests/test_api.py::test_source_verification_endpoint_persists_browserbase_artifact`
