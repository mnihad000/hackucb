from __future__ import annotations

from collections import Counter
from typing import Any

from models.document import Document
from models.investigation import (
    ReceiptVerificationStatus,
    SourceVerificationReceipt,
    SourceVerificationResult,
)

_STATUS_MAP: dict[str, ReceiptVerificationStatus] = {
    "verified": "verified",
    "source_updated": "metadata_mismatch",
    "blocked": "unavailable",
    "unavailable": "unavailable",
    "needs_manual_review": "pending",
}


def build_source_verification(
    investigation_id: str,
    documents: list[Document],
    *,
    cited_document_ids: list[str] | None = None,
    max_documents: int | None = None,
    agent: Any | None = None,
) -> SourceVerificationResult:
    selected = _select_documents(documents, cited_document_ids, max_documents)
    limitations: list[str] = []
    if cited_document_ids is not None:
        missing = [doc_id for doc_id in cited_document_ids if doc_id not in {doc.id for doc in documents}]
        if missing:
            limitations.append(
                f"{len(missing)} cited document id(s) were not present in the retrieved corpus and could not be verified."
            )
    if not selected:
        return SourceVerificationResult(
            investigation_id=investigation_id,
            limitations=["No documents were available for source verification.", *limitations],
        )

    if agent is None:
        from agents.browserbase_agent import get_browserbase_agent

        agent = get_browserbase_agent()

    raw_receipts = agent.verify_documents(selected)
    docs_by_id = {doc.id: doc for doc in selected}
    receipts = [
        _to_source_receipt(raw_receipt, docs_by_id.get(_raw_value(raw_receipt, "source_id", "")))
        for raw_receipt in raw_receipts
    ]
    status_counts = Counter(receipt.verification_status for receipt in receipts)
    backend_counts = Counter(receipt.backend for receipt in receipts)
    if any(receipt.backend == "httpx_fallback" for receipt in receipts):
        limitations.append(
            "Some URLs were checked with the HTTP fallback because Browserbase real-browser verification was not configured."
        )
    if any(receipt.verification_status == "pending" for receipt in receipts):
        limitations.append("Some sources still need manual review before their claims should be treated as fully verified.")

    return SourceVerificationResult(
        investigation_id=investigation_id,
        receipts=receipts,
        status_counts=dict(status_counts),
        backend_counts=dict(backend_counts),
        verified_count=status_counts.get("verified", 0),
        browserbase_verified_count=sum(
            1 for receipt in receipts if receipt.backend == "browserbase" and receipt.verification_status == "verified"
        ),
        fallback_checked_count=backend_counts.get("httpx_fallback", 0),
        pending_count=status_counts.get("pending", 0),
        unavailable_count=status_counts.get("unavailable", 0),
        metadata_mismatch_count=status_counts.get("metadata_mismatch", 0),
        limitations=limitations,
    )


def verification_map_from_result(result: SourceVerificationResult | None) -> dict[str, ReceiptVerificationStatus]:
    if result is None:
        return {}
    return {
        receipt.document_id: receipt.verification_status
        for receipt in result.receipts
    }


def _select_documents(
    documents: list[Document],
    cited_document_ids: list[str] | None,
    max_documents: int | None,
) -> list[Document]:
    if cited_document_ids is None:
        selected = list(documents)
    else:
        wanted = list(dict.fromkeys(cited_document_ids))
        by_id = {doc.id: doc for doc in documents}
        selected = [by_id[doc_id] for doc_id in wanted if doc_id in by_id]
    if max_documents is not None:
        selected = selected[:max_documents]
    return selected


def _to_source_receipt(raw_receipt: Any, document: Document | None) -> SourceVerificationReceipt:
    raw_status = str(_raw_value(raw_receipt, "verified_status", "needs_manual_review"))
    mapped_status = _STATUS_MAP.get(raw_status, "pending")
    backend = str(_raw_value(raw_receipt, "backend", "browserbase") or "browserbase")
    if backend not in {"browserbase", "httpx_fallback", "cache", "demo_fixture", "not_verified"}:
        backend = "browserbase"
    return SourceVerificationReceipt(
        document_id=str(_raw_value(raw_receipt, "source_id", document.id if document else "")),
        url=str(_raw_value(raw_receipt, "url", document.url if document else "")),
        source_name=document.source_name if document else "",
        title=document.title if document else (_raw_value(raw_receipt, "stored_title", "") or ""),
        raw_status=raw_status,
        verification_status=mapped_status,
        backend=backend,  # type: ignore[arg-type]
        live_title=_raw_value(raw_receipt, "live_title", None),
        stored_title=_raw_value(raw_receipt, "stored_title", None) or (document.title if document else None),
        evidence_snippet=_raw_value(raw_receipt, "evidence_snippet", None),
        support_reason=_raw_value(raw_receipt, "support_reason", None),
        checked_at=_raw_value(raw_receipt, "checked_at", None),
        error=_raw_value(raw_receipt, "error", None),
    )


def _raw_value(raw_receipt: Any, key: str, default: Any = None) -> Any:
    if isinstance(raw_receipt, dict):
        return raw_receipt.get(key, default)
    return getattr(raw_receipt, key, default)
