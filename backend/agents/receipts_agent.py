from __future__ import annotations

from dataclasses import dataclass

from models.document import Document
from models.investigation import (
    ClaimCounterpointPair,
    ClaimCounterpointResult,
    FinalReportClaim,
    FinalReportResult,
    InvestigationPlan,
    ReceiptVerificationStatus,
    ReceiptsResult,
)
from services.receipts_builder import build_receipts as build_receipts_artifact

_VALID_VERIFICATION_STATUSES: set[ReceiptVerificationStatus] = {
    "verified",
    "unavailable",
    "metadata_mismatch",
    "pending",
}


@dataclass
class _PreparedInputs:
    documents: list[Document]
    report: FinalReportResult
    claim_counterpoints: ClaimCounterpointResult | None
    verification_map: dict[str, ReceiptVerificationStatus]
    audit_notes: list[str]


class ReceiptsAgent:
    """Orchestrates claim-grounding receipt reviews with preflight validation."""

    def build(
        self,
        investigation_id: str,
        plan: InvestigationPlan,
        documents: list[Document],
        report: FinalReportResult,
        claim_counterpoints: ClaimCounterpointResult | None,
        verification_map: dict[str, ReceiptVerificationStatus],
    ) -> ReceiptsResult:
        prepared = self._prepare_inputs(
            investigation_id=investigation_id,
            plan=plan,
            documents=documents,
            report=report,
            claim_counterpoints=claim_counterpoints,
            verification_map=verification_map,
        )
        result = build_receipts_artifact(
            investigation_id=investigation_id,
            plan=plan,
            documents=prepared.documents,
            report=prepared.report,
            claim_counterpoints=prepared.claim_counterpoints,
            verification_map=prepared.verification_map,
        )
        if prepared.audit_notes:
            result = result.model_copy(
                update={
                    "limitations": _dedupe_strings([*result.limitations, *prepared.audit_notes]),
                }
            )
        return result

    def _prepare_inputs(
        self,
        *,
        investigation_id: str,
        plan: InvestigationPlan,
        documents: list[Document],
        report: FinalReportResult,
        claim_counterpoints: ClaimCounterpointResult | None,
        verification_map: dict[str, ReceiptVerificationStatus],
    ) -> _PreparedInputs:
        audit_notes: list[str] = []

        cleaned_documents, document_notes = self._prepare_documents(documents)
        audit_notes.extend(document_notes)

        cleaned_report, report_notes = self._prepare_report(report, cleaned_documents)
        audit_notes.extend(report_notes)

        cleaned_counterpoints, counterpoint_notes = self._prepare_counterpoints(
            claim_counterpoints,
            cleaned_report,
        )
        audit_notes.extend(counterpoint_notes)

        cleaned_verification_map, verification_notes = self._prepare_verification_map(
            verification_map,
            cleaned_documents,
        )
        audit_notes.extend(verification_notes)

        if report.investigation_id != investigation_id:
            audit_notes.append(
                "Receipts agent received a report artifact whose investigation_id did not match the active investigation."
            )
        if report.plan_snapshot.query_text != plan.query_text:
            audit_notes.append(
                "Receipts agent detected a report/plan query mismatch and used the active investigation plan for receipt output."
            )
        if cleaned_counterpoints is not None and cleaned_counterpoints.investigation_id != investigation_id:
            audit_notes.append(
                "Receipts agent received claim counterpoints from a different investigation and normalized them to the active investigation."
            )

        return _PreparedInputs(
            documents=cleaned_documents,
            report=cleaned_report.model_copy(
                update={
                    "investigation_id": investigation_id,
                    "plan_snapshot": plan,
                }
            ),
            claim_counterpoints=(
                None
                if cleaned_counterpoints is None
                else cleaned_counterpoints.model_copy(
                    update={
                        "investigation_id": investigation_id,
                        "plan_snapshot": plan,
                    }
                )
            ),
            verification_map=cleaned_verification_map,
            audit_notes=_dedupe_strings(audit_notes),
        )

    def _prepare_documents(self, documents: list[Document]) -> tuple[list[Document], list[str]]:
        notes: list[str] = []
        if not documents:
            return [], ["Receipts agent received an empty retrieved-document corpus."]

        deduped: dict[str, Document] = {}
        duplicate_ids: set[str] = set()
        for document in documents:
            existing = deduped.get(document.id)
            if existing is None:
                deduped[document.id] = document
                continue
            duplicate_ids.add(document.id)
            deduped[document.id] = self._prefer_richer_document(existing, document)

        if duplicate_ids:
            notes.append(
                f"Duplicate retrieved document IDs were collapsed before receipt scoring: {', '.join(sorted(duplicate_ids)[:6])}."
            )
        return list(deduped.values()), notes

    def _prepare_report(
        self,
        report: FinalReportResult,
        documents: list[Document],
    ) -> tuple[FinalReportResult, list[str]]:
        notes: list[str] = []
        available_doc_ids = {document.id for document in documents}
        seen_claim_ids: set[str] = set()
        cleaned_claims: list[FinalReportClaim] = []
        duplicate_claim_ids: set[str] = set()

        for claim in report.key_claims:
            if claim.claim_id in seen_claim_ids:
                duplicate_claim_ids.add(claim.claim_id)
                continue
            seen_claim_ids.add(claim.claim_id)
            cleaned_claims.append(claim)

            missing_citation_ids = [
                citation.document_id
                for citation in claim.citations
                if citation.document_id not in available_doc_ids
            ]
            if missing_citation_ids:
                notes.append(
                    f"Claim '{claim.claim_id}' references citation documents not present in the retrieved corpus: {', '.join(missing_citation_ids[:4])}."
                )
            if claim.claim_type in {"observed_fact", "inference"} and not claim.citations:
                notes.append(
                    f"Claim '{claim.claim_id}' has no direct citations and may remain unsupported unless counterpoint-linked receipts cover it."
                )

        if duplicate_claim_ids:
            notes.append(
                f"Duplicate report claim IDs were collapsed before receipt scoring: {', '.join(sorted(duplicate_claim_ids)[:6])}."
            )

        return report.model_copy(update={"key_claims": cleaned_claims}), notes

    def _prepare_counterpoints(
        self,
        claim_counterpoints: ClaimCounterpointResult | None,
        report: FinalReportResult,
    ) -> tuple[ClaimCounterpointResult | None, list[str]]:
        if claim_counterpoints is None:
            return None, []

        notes: list[str] = []
        report_claim_ids = {claim.claim_id for claim in report.key_claims}
        best_pairs: dict[str, ClaimCounterpointPair] = {}
        dropped_unlinked: list[str] = []
        dropped_duplicates: list[str] = []

        for pair in claim_counterpoints.pairs:
            if pair.claim_id not in report_claim_ids:
                dropped_unlinked.append(pair.claim_id)
                continue
            existing = best_pairs.get(pair.claim_id)
            if existing is None or pair.confidence_score > existing.confidence_score:
                if existing is not None:
                    dropped_duplicates.append(pair.claim_id)
                best_pairs[pair.claim_id] = pair
            else:
                dropped_duplicates.append(pair.claim_id)

        if dropped_unlinked:
            notes.append(
                f"Claim counterpoints not linked to current report claims were ignored: {', '.join(sorted(set(dropped_unlinked))[:6])}."
            )
        if dropped_duplicates:
            notes.append(
                f"Duplicate claim counterpoints were reduced to the highest-confidence pair per claim: {', '.join(sorted(set(dropped_duplicates))[:6])}."
            )

        cleaned_pairs = [
            best_pairs[claim.claim_id]
            for claim in report.key_claims
            if claim.claim_id in best_pairs
        ]
        cleaned_unmatched = [
            claim_id for claim_id in claim_counterpoints.unmatched_claim_ids if claim_id in report_claim_ids
        ]
        return (
            claim_counterpoints.model_copy(
                update={
                    "pairs": cleaned_pairs,
                    "unmatched_claim_ids": cleaned_unmatched,
                }
            ),
            notes,
        )

    def _prepare_verification_map(
        self,
        verification_map: dict[str, ReceiptVerificationStatus],
        documents: list[Document],
    ) -> tuple[dict[str, ReceiptVerificationStatus], list[str]]:
        notes: list[str] = []
        available_doc_ids = {document.id for document in documents}
        cleaned_map: dict[str, ReceiptVerificationStatus] = {}
        invalid_doc_ids: list[str] = []

        for doc_id, status in verification_map.items():
            if doc_id not in available_doc_ids:
                continue
            if status not in _VALID_VERIFICATION_STATUSES:
                invalid_doc_ids.append(doc_id)
                cleaned_map[doc_id] = "pending"
                continue
            cleaned_map[doc_id] = status

        missing_status_ids = sorted(available_doc_ids - set(cleaned_map))
        for doc_id in missing_status_ids:
            cleaned_map[doc_id] = "pending"

        if invalid_doc_ids:
            notes.append(
                f"Invalid verification statuses were normalized to pending for document IDs: {', '.join(sorted(invalid_doc_ids)[:6])}."
            )
        if missing_status_ids:
            notes.append(
                f"Verification status defaulted to pending for {len(missing_status_ids)} retrieved document(s) with no verification record."
            )
        return cleaned_map, notes

    def _prefer_richer_document(self, left: Document, right: Document) -> Document:
        return right if _document_richness_score(right) > _document_richness_score(left) else left


def build_receipts(
    investigation_id: str,
    plan: InvestigationPlan,
    documents: list[Document],
    report: FinalReportResult,
    claim_counterpoints: ClaimCounterpointResult | None,
    verification_map: dict[str, ReceiptVerificationStatus],
) -> ReceiptsResult:
    return ReceiptsAgent().build(
        investigation_id=investigation_id,
        plan=plan,
        documents=documents,
        report=report,
        claim_counterpoints=claim_counterpoints,
        verification_map=verification_map,
    )


def _document_richness_score(document: Document) -> int:
    return sum(
        [
            len(document.text or ""),
            len(document.snippet or ""),
            len(document.title or ""),
            len(document.entities) * 8,
            len(document.phrases) * 8,
        ]
    )


def _dedupe_strings(values: list[str]) -> list[str]:
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
