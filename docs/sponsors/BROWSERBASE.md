# Browserbase Sponsor Integration

## What Browserbase Does In RhetoriQ

Browserbase is the source verification layer. RhetoriQ should not cite a public source just because a retriever found a URL. Browserbase lets the backend open the page in a real browser session, extract live metadata, compare the page against stored document metadata, and produce a receipt.

The receipt is what lets the final report say: this claim is supported by a checked source, not just a remembered snippet.

## How Browserbase Was Added

Configuration lives in `backend/config.py`:

- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`

Core implementation files:

- `backend/agents/browserbase_agent.py` defines `BrowserbaseAgent` and the `Receipt` object.
- `backend/services/verification_cache.py` caches verification results in Redis for 24 hours.
- `backend/services/verification.py` reads cached verification states when building report support metadata.
- `backend/api/browserbase_status.py` exposes `/api/browserbase/status`.
- `backend/api/narratives.py` auto-verifies a limited set of retrieved documents before receipts/report generation.

Dependencies are listed in `backend/requirements.txt`:

```text
browserbase==1.13.0
playwright==1.60.0
```

## How It Works In The Pipeline

1. Retrieval returns candidate `Document` objects with URLs, titles, timestamps, and snippets.
2. `BrowserbaseAgent.verify_documents()` checks Redis verification cache first.
3. If there is no cached result and Browserbase is configured, the agent creates a Browserbase session.
4. Playwright connects to that session over CDP and opens the URL.
5. The agent extracts the live title and page HTML.
6. The agent compares live content to stored title/snippet metadata.
7. The result is saved as a receipt with one of these statuses:

```text
verified
source_updated
blocked
unavailable
needs_manual_review
```

If Browserbase is not configured, the project falls back to `httpx` so local development still works. That fallback is useful for demos, but the sponsor story is the real-browser path.

## How Crucial Browserbase Is

Browserbase is critical for the trust layer. Without it, the app can still assemble an investigation report, but it cannot demonstrate that a cited source page was actually opened and checked during the pipeline.

Browserbase is crucial because civic narrative analysis is sensitive:

- URLs can go stale.
- Pages can change after indexing.
- Paywalls, 403s, and unavailable pages need to be marked honestly.
- The report should distinguish a verified receipt from an unchecked candidate source.

## Problem Statement Fit

The problem statement asks RhetoriQ to trace narratives with evidence. Browserbase makes the evidence side credible by turning source URLs into receipt objects. It helps RhetoriQ avoid unsupported civic claims and makes the chain of custody inspectable.

## Demo Proof Points

- Show `/api/browserbase/status` reporting `backend: browserbase` when configured.
- Run an investigation and show receipt statuses in the report.
- Show `rq:verify:*` cache entries in Redis after verification.
- In the UI, point to verified or failed receipt states rather than only source links.
