"""
Browserbase source verification service.

Demo mode: returns pre-built results from DEMO_VERIFICATIONS.
Real mode (swap-in): opens the live URL with Browserbase, extracts metadata,
compares against stored document, and sets verification_status accordingly.

Three honest status values:
  verified          — live page matches stored metadata
  source_updated    — live title/snippet differs from stored version
  unavailable       — page returned 404 or is paywalled / blocked

Failures are features, not bugs. Showing a metadata mismatch or unavailable
page is more credible than an all-green result.
"""

from config import get_settings
from models.document import Document
from models.report import EvidenceItem


class VerificationService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def verify_source(self, doc: Document) -> dict:
        """
        Returns a verification result dict for a single document.
        Demo mode: looks up pre-built result from DEMO_VERIFICATIONS.
        Real mode: calls Browserbase, visits doc.url, extracts and compares metadata.
        """
        from demo_data import DEMO_VERIFICATIONS

        if self._settings.DEMO_MODE:
            result = DEMO_VERIFICATIONS.get(doc.id)
            if result:
                return result
            # Default for documents not in the verification dict
            return {
                "doc_id": doc.id,
                "url": doc.url,
                "verification_status": "pending",
                "live_title": None,
                "stored_title": doc.title,
                "snippet_match": None,
                "page_available": None,
                "checked_at": None,
            }

        raise NotImplementedError("Real Browserbase call not yet wired. Set DEMO_MODE=True.")

    def verify_evidence_items(self, evidence: list[EvidenceItem], all_docs: list[Document]) -> list[EvidenceItem]:
        """
        Runs verification for each evidence item and updates its status.
        Returns updated evidence list with all three status states represented honestly.
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
