from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from config import get_settings
from models.investigation import FetchFailure, RawPage

logger = logging.getLogger(__name__)


class HttpPageFetcher:
    def __init__(self, cache=None) -> None:
        self._settings = get_settings()
        self._cache = cache  # optional TrendingRedisCache

    def fetch(self, url: str) -> RawPage | FetchFailure:
        # Cache hit — skip the network entirely
        if self._cache is not None:
            cached = self._cache.get_page(url)
            if cached:
                try:
                    return RawPage(**cached)
                except Exception:
                    pass  # malformed cache entry → fall through to live fetch

        headers = {
            "User-Agent": "RhetoriQ/0.1 (+investigation retriever)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        }
        try:
            with httpx.Client(
                timeout=self._settings.FETCH_TIMEOUT_SECONDS,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = client.get(url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            return FetchFailure(url=url, error_type="timeout", message=str(exc), retryable=True)
        except httpx.HTTPStatusError as exc:
            return FetchFailure(
                url=url,
                error_type="http_status",
                message=str(exc),
                status_code=exc.response.status_code,
                retryable=500 <= exc.response.status_code < 600,
            )
        except httpx.HTTPError as exc:
            return FetchFailure(url=url, error_type="http_error", message=str(exc), retryable=True)

        content_type = response.headers.get("content-type")
        if content_type and "html" not in content_type and "xml" not in content_type:
            return FetchFailure(
                url=url,
                error_type="unsupported_content_type",
                message=f"Unsupported content type: {content_type}",
                status_code=response.status_code,
                retryable=False,
            )

        page = RawPage(
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            content_type=content_type,
            html=response.text,
            fetched_at=datetime.now(timezone.utc),
        )

        # Store in Redis for future runs (TTL managed by cache layer)
        if self._cache is not None:
            self._cache.set_page(url, page.model_dump(mode="json"))

        return page


class BrowserbaseFetcher:
    """
    Page fetcher that uses Browserbase's real browser (Playwright/Chromium) to
    render each article.  Handles SPAs, JavaScript-rendered content, and soft
    paywalls that plain httpx cannot penetrate.

    Falls back to HttpPageFetcher on any Browserbase session failure so the
    investigation pipeline keeps running even when the quota is exhausted or
    the service is unreachable.

    Sponsor track: Browserbase — every article in an investigation is opened in
    a real, cloud browser session before we cite it.
    """

    def __init__(self, cache=None) -> None:
        self._settings = get_settings()
        self._cache = cache
        self._api_key = self._settings.BROWSERBASE_API_KEY
        self._project_id = self._settings.BROWSERBASE_PROJECT_ID
        self._fallback = HttpPageFetcher(cache=cache)
        # Track how many live browser fetches happened this session (for /status)
        self.browser_fetch_count = 0
        self.fallback_fetch_count = 0

    def fetch(self, url: str) -> RawPage | FetchFailure:
        # Cache hit — no browser needed
        if self._cache is not None:
            cached = self._cache.get_page(url)
            if cached:
                try:
                    return RawPage(**cached)
                except Exception:
                    pass

        page = self._fetch_with_browserbase(url)
        if page is None:
            # Session failed — degrade gracefully to httpx
            self.fallback_fetch_count += 1
            return self._fallback.fetch(url)

        self.browser_fetch_count += 1
        if self._cache is not None:
            self._cache.set_page(url, page.model_dump(mode="json"))
        return page

    def _fetch_with_browserbase(self, url: str) -> RawPage | None:
        try:
            from browserbase import Browserbase
            from playwright.sync_api import sync_playwright

            bb = Browserbase(api_key=self._api_key)
            session = bb.sessions.create(project_id=self._project_id)
            logger.info("Browserbase session %s — fetching %s", session.id, url)

            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(session.connect_url)
                context = browser.contexts[0]
                page = context.pages[0]

                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                final_url = page.url
                html = page.content()
                status = 200  # playwright doesn't expose HTTP status cleanly

                page.close()
                browser.close()

            return RawPage(
                url=url,
                final_url=final_url,
                status_code=status,
                content_type="text/html",
                html=html,
                fetched_at=datetime.now(timezone.utc),
            )

        except Exception as exc:
            logger.warning("BrowserbaseFetcher failed for %s — will fall back to httpx: %s", url, exc)
            return None


def get_page_fetcher(cache=None) -> BrowserbaseFetcher | HttpPageFetcher:
    """Return a BrowserbaseFetcher when Browserbase is configured, else HttpPageFetcher."""
    settings = get_settings()
    if settings.BROWSERBASE_API_KEY and settings.BROWSERBASE_PROJECT_ID:
        try:
            import browserbase  # noqa: F401
            from playwright.sync_api import sync_playwright as _p  # noqa: F401
            return BrowserbaseFetcher(cache=cache)
        except ImportError:
            pass
    return HttpPageFetcher(cache=cache)
