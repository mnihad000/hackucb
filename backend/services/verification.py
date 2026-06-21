"""
Source verification service for RhetoriQ.

Priority order for each document URL:
  1. Redis verification cache  — result from a prior Browserbase session
  2. Demo fixtures             — pre-built results for seeded narratives
  3. Pending                   — not yet verified; caller should trigger /verify

The service never calls Browserbase directly — that lives in
BrowserbaseAgent and is triggered via POST /investigations/{id}/verify.
Once Browserbase runs, it writes results to the Redis cache, and this
service finds them automatically on the next report build.
"""

from datetime import datetime, timezone

from config import get_settings
from models.document import Document
from models.report import EvidenceItem


# Map Browserbase verified_status values → the three statuses the frontend understands
_STATUS_MAP: dict[str, str] = {
    "verified": "verified",
    "source_updated": "metadata_mismatch",
    "blocked": "unavailable",
    "unavailable": "unavailable",
    "needs_manual_review": "pending",
}


class VerificationService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def verify_source(self, doc: Document) -> dict:
        """
        Returns a verification result dict for a single document.

        Checks Redis (populated by BrowserbaseAgent) first.
        Falls back to demo fixtures, then returns pending.
        """
        from services.verification_cache import get_verification_cache

        # 1. Redis cache — populated whenever BrowserbaseAgent verified this URL
        cached = get_verification_cache().get(doc.url)
        if cached:
            raw_status = cached.get("verified_status", "needs_manual_review")
            mapped = _STATUS_MAP.get(raw_status, "pending")
            return {
                "doc_id": doc.id,
                "url": doc.url,
                "verification_status": mapped,
                "live_title": cached.get("live_title"),
                "stored_title": cached.get("stored_title") or doc.title,
                "snippet_match": cached.get("evidence_snippet") is not None,
                "page_available": mapped != "unavailable",
                "checked_at": cached.get("checked_at"),
                "source": "browserbase_cache",
            }

        # 2. Demo fixtures (always available for seeded narrative IDs)
        from demo_data import DEMO_VERIFICATIONS
        demo = DEMO_VERIFICATIONS.get(doc.id)
        if demo:
            return demo

        # 3. Pending — trigger POST /investigations/{id}/verify to populate cache
        return {
            "doc_id": doc.id,
            "url": doc.url,
            "verification_status": "pending",
            "live_title": None,
            "stored_title": doc.title,
            "snippet_match": None,
            "page_available": None,
            "checked_at": None,
            "source": "not_verified",
        }

    def verify_evidence_items(
        self, evidence: list[EvidenceItem], all_docs: list[Document]
    ) -> list[EvidenceItem]:
        """
        Runs verification for each evidence item and updates its status.
        """
        doc_map = {d.id: d for d in all_docs}
        updated: list[EvidenceItem] = []

        for item in evidence:
            doc = doc_map.get(item.doc_id)
            if not doc:
                updated.append(item)
                continue

            result = self.verify_source(doc)
            status = result.get("verification_status", "pending")
            verified = status == "verified"

            updated.append(
                item.model_copy(update={
                    "verified": verified,
                    "verification_status": status,
                })
            )

        return updated

    def verify_batch(self, doc_ids: list[str], all_docs: list[Document]) -> list[dict]:
        """Returns verification results for a list of doc IDs."""
        doc_map = {d.id: d for d in all_docs}
        results: list[dict] = []
        for doc_id in doc_ids:
            doc = doc_map.get(doc_id)
            if doc:
                results.append(self.verify_source(doc))
        return results
