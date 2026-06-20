"""
Browserbase Evidence Verification Agent for RhetoriQ.

Opens candidate source URLs using Browserbase's real browser, extracts metadata,
and produces verified receipt objects for the investigation report.

Sponsor Track: Browserbase — verifies source pages before RhetoriQ cites them.

Each receipt has one of five statuses:
  verified           — live page matches stored metadata and snippet is present
  source_updated     — page exists but title/content has changed since indexed
  blocked            — page returned 403, paywall, or CAPTCHA
  unavailable        — 404 or DNS failure
  needs_manual_review — unexpected content or structure
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from config import get_settings
from models.document import Document

logger = logging.getLogger(__name__)

VerifiedStatus = str  # "verified" | "source_updated" | "blocked" | "unavailable" | "needs_manual_review"


class Receipt:
    """Verified source receipt produced by BrowserbaseAgent."""

    def __init__(
        self,
        receipt_id: str,
        source_id: str,
        url: str,
        verified_status: VerifiedStatus,
        live_title: str | None = None,
        stored_title: str | None = None,
        evidence_snippet: str | None = None,
        support_reason: str | None = None,
        author: str | None = None,
        published_at: str | None = None,
        checked_at: str | None = None,
        error: str | None = None,
    ) -> None:
        self.receipt_id = receipt_id
        self.source_id = source_id
        self.url = url
        self.verified_status = verified_status
        self.live_title = live_title
        self.stored_title = stored_title
        self.evidence_snippet = evidence_snippet
        self.support_reason = support_reason
        self.author = author
        self.published_at = published_at
        self.checked_at = checked_at or datetime.now(timezone.utc).isoformat()
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "source_id": self.source_id,
            "url": self.url,
            "verified_status": self.verified_status,
            "live_title": self.live_title,
            "stored_title": self.stored_title,
            "evidence_snippet": self.evidence_snippet,
            "support_reason": self.support_reason,
            "author": self.author,
            "published_at": self.published_at,
            "checked_at": self.checked_at,
            "error": self.error,
        }


class BrowserbaseAgent:
    """
    Verifies source URLs using Browserbase real-browser sessions.

    In demo mode (no API key) falls back to HTTP metadata extraction via httpx,
    so the rest of the pipeline still works during development.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._api_key = self._settings.BROWSERBASE_API_KEY
        self._project_id = self._settings.BROWSERBASE_PROJECT_ID
        self._use_real_browser = bool(self._api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_document(self, doc: Document) -> Receipt:
        """
        Verify a single document URL and return a Receipt.

        Uses Browserbase if configured, otherwise falls back to httpx.
        """
        receipt_id = f"receipt_{doc.id}"
        if self._use_real_browser:
            return self._verify_with_browserbase(doc, receipt_id)
        return self._verify_with_httpx(doc, receipt_id)

    def verify_documents(self, docs: list[Document]) -> list[Receipt]:
        """Verify a batch of documents. Returns one Receipt per doc."""
        receipts = []
        for doc in docs:
            try:
                receipts.append(self.verify_document(doc))
            except Exception as exc:
                logger.error("Verification failed for %s: %s", doc.id, exc)
                receipts.append(Receipt(
                    receipt_id=f"receipt_{doc.id}",
                    source_id=doc.id,
                    url=doc.url,
                    verified_status="needs_manual_review",
                    stored_title=doc.title,
                    error=str(exc),
                ))
        return receipts

    # ------------------------------------------------------------------
    # Browserbase real-browser path
    # ------------------------------------------------------------------

    def _verify_with_browserbase(self, doc: Document, receipt_id: str) -> Receipt:
        """Open URL with Browserbase real browser, extract metadata, compare to stored doc."""
        try:
            from browserbase import Browserbase
            from playwright.sync_api import sync_playwright

            bb = Browserbase(api_key=self._api_key)
            session = bb.sessions.create(project_id=self._project_id)
            logger.info("Browserbase session %s — verifying %s", session.id, doc.url)

            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(session.connect_url)
                context = browser.contexts[0]
                page = context.pages[0]

                page.goto(doc.url, timeout=30000, wait_until="domcontentloaded")
                live_title = page.title() or None
                html = page.content()

                page.close()
                browser.close()

            return self._build_receipt(
                receipt_id=receipt_id,
                doc=doc,
                live_title=live_title,
                html=html,
                http_status=200,
            )

        except Exception as exc:
            logger.error("Browserbase verification failed for %s: %s", doc.url, exc)
            return Receipt(
                receipt_id=receipt_id,
                source_id=doc.id,
                url=doc.url,
                verified_status="needs_manual_review",
                stored_title=doc.title,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Fallback: plain HTTP via httpx
    # ------------------------------------------------------------------

    def _verify_with_httpx(self, doc: Document, receipt_id: str) -> Receipt:
        """Lightweight HTTP fallback when Browserbase is not configured."""
        import httpx

        try:
            with httpx.Client(timeout=10, follow_redirects=True, headers={
                "User-Agent": "RhetoriQ/0.1 (source verifier)"
            }) as client:
                response = client.get(doc.url)

            if response.status_code == 404:
                return Receipt(
                    receipt_id=receipt_id, source_id=doc.id, url=doc.url,
                    verified_status="unavailable", stored_title=doc.title,
                    error="HTTP 404",
                )
            if response.status_code in (401, 403):
                return Receipt(
                    receipt_id=receipt_id, source_id=doc.id, url=doc.url,
                    verified_status="blocked", stored_title=doc.title,
                    error=f"HTTP {response.status_code}",
                )
            if response.status_code >= 400:
                return Receipt(
                    receipt_id=receipt_id, source_id=doc.id, url=doc.url,
                    verified_status="unavailable", stored_title=doc.title,
                    error=f"HTTP {response.status_code}",
                )

            html = response.text
            live_title = self._extract_title(html)
            return self._build_receipt(
                receipt_id=receipt_id,
                doc=doc,
                live_title=live_title,
                html=html,
                http_status=response.status_code,
            )

        except httpx.TimeoutException:
            return Receipt(
                receipt_id=receipt_id, source_id=doc.id, url=doc.url,
                verified_status="unavailable", stored_title=doc.title,
                error="timeout",
            )
        except Exception as exc:
            return Receipt(
                receipt_id=receipt_id, source_id=doc.id, url=doc.url,
                verified_status="unavailable", stored_title=doc.title,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Shared receipt builder
    # ------------------------------------------------------------------

    def _build_receipt(
        self,
        receipt_id: str,
        doc: Document,
        live_title: str | None,
        html: str,
        http_status: int,
    ) -> Receipt:
        snippet_found = self._snippet_present(doc.snippet, html) if doc.snippet else False
        title_matches = self._titles_match(doc.title, live_title)

        if title_matches and snippet_found:
            status: VerifiedStatus = "verified"
            support_reason = "Live page title and evidence snippet both match stored document."
        elif title_matches and not snippet_found:
            status = "source_updated"
            support_reason = "Title matches but the exact snippet was not found — page may have been updated."
        elif not title_matches and snippet_found:
            status = "source_updated"
            support_reason = "Snippet found but title differs — page may have been edited or republished."
        elif live_title and not title_matches:
            status = "source_updated"
            support_reason = "Page accessible but title has changed since this document was indexed."
        else:
            status = "needs_manual_review"
            support_reason = "Page accessible but could not confirm metadata match."

        author = self._extract_author(html)

        return Receipt(
            receipt_id=receipt_id,
            source_id=doc.id,
            url=doc.url,
            verified_status=status,
            live_title=live_title,
            stored_title=doc.title,
            evidence_snippet=doc.snippet,
            support_reason=support_reason,
            author=author,
        )

    # ------------------------------------------------------------------
    # HTML extraction helpers
    # ------------------------------------------------------------------

    def _extract_title(self, html: str) -> str | None:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1).strip())
        og = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html, re.IGNORECASE)
        if og:
            return og.group(1).strip()
        return None

    def _extract_author(self, html: str) -> str | None:
        patterns = [
            r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)',
            r'"author"\s*:\s*\{"name"\s*:\s*"([^"]+)"',
            r'class=["\'][^"\']*byline[^"\']*["\'][^>]*>(?:[^<]*<[^>]+>)*\s*(?:By\s+)?([A-Z][a-z]+ [A-Z][a-z]+)',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _snippet_present(self, snippet: str, html: str) -> bool:
        if not snippet or len(snippet) < 20:
            return False
        # Check for a 15-word window from the snippet
        words = snippet.split()[:15]
        short = " ".join(words).lower()
        return short in html.lower()

    def _titles_match(self, stored: str | None, live: str | None) -> bool:
        if not stored or not live:
            return False
        def norm(s: str) -> str:
            return re.sub(r"[^\w\s]", "", s.lower()).strip()
        s, l = norm(stored), norm(live)
        # Accept if either contains the other (handles " | Site Name" suffixes)
        return s in l or l in s or self._word_overlap(s, l) >= 0.6

    def _word_overlap(self, a: str, b: str) -> float:
        wa, wb = set(a.split()), set(b.split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / max(len(wa), len(wb))


# Module-level singleton
_agent: BrowserbaseAgent | None = None


def get_browserbase_agent() -> BrowserbaseAgent:
    global _agent
    if _agent is None:
        _agent = BrowserbaseAgent()
    return _agent
