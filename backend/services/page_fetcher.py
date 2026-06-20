from __future__ import annotations

from datetime import datetime, timezone

import httpx

from config import get_settings
from models.investigation import FetchFailure, RawPage


class HttpPageFetcher:
    def __init__(self) -> None:
        self._settings = get_settings()

    def fetch(self, url: str) -> RawPage | FetchFailure:
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

        return RawPage(
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            content_type=content_type,
            html=response.text,
            fetched_at=datetime.now(timezone.utc),
        )
