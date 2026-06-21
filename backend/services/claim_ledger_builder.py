from __future__ import annotations

from models.investigation import (
    AnalystResult,
    ClaimLedgerEntry,
    ClaimLedgerResult,
    ReceiptsResult,
    SkepticReviewResult,
)


def build_claim_ledger(
    investigation_id: str,
    analyst: AnalystResult,
    receipts: ReceiptsResult | None,
    skeptic: SkepticReviewResult | None,
) -> ClaimLedgerResult:
    skeptic_by_claim_id = {
        review.claim_id: review for review in (skeptic.claim_reviews if skeptic is not None else [])
    }
    receipts_by_claim_id = {
        review.claim_id: review for review in (receipts.claim_receipts if receipts is not None else [])
    }
    entries: list[ClaimLedgerEntry] = []
    for claim in analyst.candidate_claims:
        skeptic_review = skeptic_by_claim_id.get(claim.id)
        receipt_review = receipts_by_claim_id.get(claim.id)
        state = "proposed"
        notes: list[str] = []
        verification_state = receipt_review.verification_state if receipt_review is not None else "not_available"
        counter_document_ids = [
            receipt.document_id for receipt in (receipt_review.contradicting_receipts if receipt_review is not None else [])
        ]

        if skeptic_review is not None and skeptic_review.decision == "pass_with_softening":
            state = "softened"
            notes.append(skeptic_review.reason)
        elif skeptic_review is not None and skeptic_review.decision == "claim_rejected":
            state = "rejected"
            notes.append(skeptic_review.reason)

        if receipt_review is not None:
            state = _state_from_support_status(receipt_review.support_status, fallback=state)
            notes.extend(receipt_review.missing_evidence_notes)

        entries.append(
            ClaimLedgerEntry(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                state=state,
                supporting_document_ids=list(claim.supporting_document_ids),
                counter_document_ids=counter_document_ids,
                verification_state=verification_state,
                survived_to_report=state in {"supported", "partially_supported", "softened"},
                pass_number=skeptic.pass_number if skeptic is not None else 1,
                notes=_dedupe(notes),
            )
        )
    return ClaimLedgerResult(investigation_id=investigation_id, entries=entries)


def _state_from_support_status(support_status: str, *, fallback: str) -> str:
    mapping = {
        "supported": "supported",
        "partially_supported": "partially_supported",
        "contradicted": "contradicted",
        "unsupported": "unresolved",
        "insufficient_evidence": "unresolved",
    }
    return mapping.get(support_status, fallback)


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output
