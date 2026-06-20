from __future__ import annotations

import re
from statistics import mean

from models.document import Document
from models.investigation import (
    ClaimReceiptReview,
    ClaimSupportStatus,
    ClaimVerificationState,
    ClaimCounterpointPair,
    ClaimCounterpointResult,
    FinalReportClaim,
    FinalReportResult,
    InvestigationPlan,
    ReceiptEvidence,
    ReceiptVerificationStatus,
    ReceiptsResult,
    ReportCitation,
)

_STOPWORDS = {
    "about",
    "after",
    "against",
    "because",
    "being",
    "between",
    "could",
    "every",
    "from",
    "have",
    "into",
    "just",
    "main",
    "might",
    "other",
    "over",
    "same",
    "should",
    "some",
    "than",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "through",
    "under",
    "with",
    "without",
    "would",
}
_TOPICAL_MATCH_THRESHOLD = 0.42
_SUPPORTED_STRONG_THRESHOLD = 0.62
_SUPPORTED_VERY_STRONG_THRESHOLD = 0.72
_SUPPORTED_SECONDARY_THRESHOLD = 0.50
_CONTRADICTED_THRESHOLD = 0.68
_MODERATE_EVIDENCE_THRESHOLD = 0.45


def build_receipts(
    investigation_id: str,
    plan: InvestigationPlan,
    documents: list[Document],
    report: FinalReportResult,
    claim_counterpoints: ClaimCounterpointResult | None,
    verification_map: dict[str, ReceiptVerificationStatus],
) -> ReceiptsResult:
    docs_by_id = {doc.id: doc for doc in documents}
    pairs_by_claim_id = {
        pair.claim_id: pair for pair in (claim_counterpoints.pairs if claim_counterpoints else [])
    }
    claims_by_id = {claim.claim_id: claim for claim in report.key_claims}

    claim_receipts = [
        _review_main_claim(claim, docs_by_id, pairs_by_claim_id.get(claim.claim_id), verification_map)
        for claim in report.key_claims
    ]
    counter_claim_receipts = [
        _review_counter_claim(pair, docs_by_id, claims_by_id.get(pair.claim_id), verification_map)
        for pair in (claim_counterpoints.pairs if claim_counterpoints else [])
    ]

    reviews = [*claim_receipts, *counter_claim_receipts]
    confidence_score = round(mean(review.confidence_score for review in reviews), 3) if reviews else 0.24
    limitations = [
        "Receipts are limited to the persisted investigation corpus and do not prove truth outside the retrieved dataset.",
        "Support status is assigned deterministically from topical overlap and receipt quality, not from a full semantic reasoning model.",
    ]
    if claim_counterpoints is None or not claim_counterpoints.pairs:
        limitations.append("No linked counter-claims were available, so contradiction checks are limited to the main report evidence packet.")

    return ReceiptsResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        claim_receipts=claim_receipts,
        counter_claim_receipts=counter_claim_receipts,
        limitations=limitations,
        confidence_score=confidence_score,
        confidence_label=_confidence_label(confidence_score),
    )


def _review_main_claim(
    claim: FinalReportClaim,
    docs_by_id: dict[str, Document],
    pair: ClaimCounterpointPair | None,
    verification_map: dict[str, ReceiptVerificationStatus],
) -> ClaimReceiptReview:
    supporting_citations = _dedupe_citations(claim.citations, pair.main_receipts if pair is not None else [])
    contradicting_citations = _dedupe_citations(pair.counter_receipts if pair is not None else [])
    caveats = list(claim.caveats)
    if pair is not None:
        caveats.extend(pair.caveats)
    return _build_review(
        claim_id=claim.claim_id,
        claim_text=claim.claim_text,
        claim_side="main",
        supporting_citations=supporting_citations,
        contradicting_citations=contradicting_citations,
        docs_by_id=docs_by_id,
        verification_map=verification_map,
        caveats=caveats,
    )


def _review_counter_claim(
    pair: ClaimCounterpointPair,
    docs_by_id: dict[str, Document],
    main_claim: FinalReportClaim | None,
    verification_map: dict[str, ReceiptVerificationStatus],
) -> ClaimReceiptReview:
    contradicting_citations = _dedupe_citations(
        pair.main_receipts,
        main_claim.citations if main_claim is not None else [],
    )
    return _build_review(
        claim_id=pair.claim_id,
        claim_text=pair.counter_claim_text,
        claim_side="counter",
        supporting_citations=_dedupe_citations(pair.counter_receipts),
        contradicting_citations=contradicting_citations,
        docs_by_id=docs_by_id,
        verification_map=verification_map,
        caveats=pair.caveats,
    )


def _build_review(
    *,
    claim_id: str,
    claim_text: str,
    claim_side: str,
    supporting_citations: list[ReportCitation],
    contradicting_citations: list[ReportCitation],
    docs_by_id: dict[str, Document],
    verification_map: dict[str, ReceiptVerificationStatus],
    caveats: list[str],
) -> ClaimReceiptReview:
    claim_terms = set(_tokenize(claim_text))
    supporting_matches = _rank_receipts(
        claim_text=claim_text,
        claim_terms=claim_terms,
        citations=supporting_citations,
        docs_by_id=docs_by_id,
        verification_map=verification_map,
        stance="supporting",
    )
    contradicting_matches = _rank_receipts(
        claim_text=claim_text,
        claim_terms=claim_terms,
        citations=contradicting_citations,
        docs_by_id=docs_by_id,
        verification_map=verification_map,
        stance="contradicting",
    )
    support_status = _support_status(supporting_matches, contradicting_matches)
    supporting_receipts = [match["receipt"] for match in supporting_matches[:3]]
    contradicting_receipts = [match["receipt"] for match in contradicting_matches[:3]]
    verification_state = _verification_state([*supporting_receipts, *contradicting_receipts])
    missing_evidence_notes = _missing_evidence_notes(
        support_status,
        supporting_matches,
        contradicting_matches,
    )
    confidence_score = _review_confidence(
        support_status=support_status,
        supporting_matches=supporting_matches,
        contradicting_matches=contradicting_matches,
        verification_state=verification_state,
    )

    return ClaimReceiptReview(
        claim_id=claim_id,
        claim_text=claim_text,
        claim_side=claim_side,
        support_status=support_status,
        support_summary=_support_summary(
            claim_text,
            claim_side,
            support_status,
            supporting_matches,
            contradicting_matches,
        ),
        supporting_receipts=supporting_receipts,
        contradicting_receipts=contradicting_receipts,
        missing_evidence_notes=missing_evidence_notes,
        verification_state=verification_state,
        confidence_score=confidence_score,
        caveats=_dedupe_strings(caveats),
    )


def _rank_receipts(
    *,
    claim_text: str,
    claim_terms: set[str],
    citations: list[ReportCitation],
    docs_by_id: dict[str, Document],
    verification_map: dict[str, ReceiptVerificationStatus],
    stance: str,
) -> list[dict]:
    ranked: list[dict] = []
    for citation in citations:
        doc = docs_by_id.get(citation.document_id)
        match = _match_receipt(
            claim_text=claim_text,
            claim_terms=claim_terms,
            citation=citation,
            document=doc,
            verification_status=verification_map.get(citation.document_id, "pending"),
            stance=stance,
        )
        if match is None:
            continue
        ranked.append(match)

    ranked.sort(
        key=lambda item: (
            -item["score"],
            -len(item["receipt"].matched_terms),
            item["receipt"].document_id,
        )
    )
    return ranked


def _match_receipt(
    *,
    claim_text: str,
    claim_terms: set[str],
    citation: ReportCitation,
    document: Document | None,
    verification_status: ReceiptVerificationStatus,
    stance: str,
) -> dict | None:
    content_parts = [
        citation.title,
        citation.snippet or "",
        document.text if document is not None else "",
        " ".join(document.phrases) if document is not None else "",
        " ".join(document.entities) if document is not None else "",
    ]
    content = " ".join(part for part in content_parts if part).strip()
    if not content:
        return None

    content_tokens = set(_tokenize(content))
    matched_terms = sorted(claim_terms & content_tokens)
    phrase_bonus = _phrase_bonus(claim_text, content)
    if len(matched_terms) < 2 and phrase_bonus == 0.0:
        return None

    evidence_span = _evidence_span(document, citation, matched_terms)
    title_bonus = 0.08 if matched_terms and any(term in citation.title.lower() for term in matched_terms[:3]) else 0.0
    snippet_bonus = 0.1 if citation.snippet else 0.04
    span_bonus = 0.08 if len(evidence_span) >= 80 else 0.03
    overlap_score = min(0.6, len(matched_terms) * 0.12)
    score = round(min(0.94, overlap_score + phrase_bonus + title_bonus + snippet_bonus + span_bonus), 3)
    if score < _TOPICAL_MATCH_THRESHOLD:
        return None

    support_reason = _support_reason(stance, matched_terms, citation.relevance_note)
    return {
        "score": score,
        "receipt": ReceiptEvidence(
            document_id=citation.document_id,
            source_name=citation.source_name,
            source_type=citation.source_type,
            title=citation.title,
            url=citation.url,
            published_at=citation.published_at,
            snippet=citation.snippet,
            evidence_span=evidence_span,
            support_reason=support_reason,
            matched_terms=matched_terms[:6],
            verification_status=verification_status,
        ),
    }


def _support_status(
    supporting_matches: list[dict],
    contradicting_matches: list[dict],
) -> ClaimSupportStatus:
    strongest_support = supporting_matches[0]["score"] if supporting_matches else 0.0
    strongest_contradiction = contradicting_matches[0]["score"] if contradicting_matches else 0.0

    if strongest_support < _TOPICAL_MATCH_THRESHOLD and strongest_contradiction < _TOPICAL_MATCH_THRESHOLD:
        return "insufficient_evidence"
    if (
        strongest_contradiction >= _CONTRADICTED_THRESHOLD
        and strongest_contradiction >= strongest_support + 0.12
    ):
        return "contradicted"

    support_scores = [item["score"] for item in supporting_matches]
    has_two_strong_supporting = len([score for score in support_scores if score >= _SUPPORTED_STRONG_THRESHOLD]) >= 2
    has_one_very_strong_and_one_secondary = (
        len(support_scores) >= 2
        and support_scores[0] >= _SUPPORTED_VERY_STRONG_THRESHOLD
        and support_scores[1] >= _SUPPORTED_SECONDARY_THRESHOLD
    )
    if (has_two_strong_supporting or has_one_very_strong_and_one_secondary) and strongest_contradiction < 0.5:
        return "supported"
    if strongest_support >= _SUPPORTED_SECONDARY_THRESHOLD:
        return "partially_supported"
    if strongest_support >= _MODERATE_EVIDENCE_THRESHOLD and strongest_contradiction >= _MODERATE_EVIDENCE_THRESHOLD:
        return "partially_supported"
    return "unsupported"


def _missing_evidence_notes(
    support_status: ClaimSupportStatus,
    supporting_matches: list[dict],
    contradicting_matches: list[dict],
) -> list[str]:
    if support_status == "insufficient_evidence":
        return ["No retrieved receipt crossed the topical match threshold for this claim."]
    if support_status == "unsupported":
        return ["Related documents were found, but they do not directly substantiate the claim as written."]
    if support_status == "contradicted":
        return ["Contradicting receipts are materially stronger than the supporting record in this dataset."]

    notes: list[str] = []
    if support_status == "partially_supported":
        if len(supporting_matches) < 2:
            notes.append("Support relies on limited corroboration across the retrieved sources.")
        if contradicting_matches:
            notes.append("Counter-evidence remains material and should be read alongside the supporting receipts.")
        return notes

    if len(supporting_matches) < 2:
        notes.append("Support is concentrated in a small number of retrieved receipts.")
    return notes


def _support_summary(
    claim_text: str,
    claim_side: str,
    support_status: ClaimSupportStatus,
    supporting_matches: list[dict],
    contradicting_matches: list[dict],
) -> str:
    supporting_sources = len(supporting_matches)
    contradicting_sources = len(contradicting_matches)
    subject = "Main claim" if claim_side == "main" else "Counter-claim"

    if support_status == "supported":
        return f"{subject} '{claim_text}' is backed by {supporting_sources} focused receipt(s) with limited contradiction in the retrieved corpus."
    if support_status == "partially_supported":
        return f"{subject} '{claim_text}' has some direct support, but the corroboration is limited or materially contested by {contradicting_sources} contradicting receipt(s)."
    if support_status == "unsupported":
        return f"{subject} '{claim_text}' appears in related source material, but the available receipts do not directly support the full claim."
    if support_status == "contradicted":
        return f"{subject} '{claim_text}' is outweighed by {contradicting_sources} stronger contradicting receipt(s) in the retrieved corpus."
    return f"{subject} '{claim_text}' does not yet have sufficient focused receipts in the retrieved corpus."


def _review_confidence(
    *,
    support_status: ClaimSupportStatus,
    supporting_matches: list[dict],
    contradicting_matches: list[dict],
    verification_state: ClaimVerificationState,
) -> float:
    strongest_support = supporting_matches[0]["score"] if supporting_matches else 0.0
    strongest_contradiction = contradicting_matches[0]["score"] if contradicting_matches else 0.0
    evidence_strength = max(strongest_support, strongest_contradiction)
    verification_bonus = {
        "verified": 0.08,
        "mixed": 0.04,
        "metadata_mismatch": 0.02,
        "unavailable": 0.0,
        "pending": 0.0,
        "not_available": -0.04,
    }[verification_state]
    status_bonus = {
        "supported": 0.12,
        "contradicted": 0.12,
        "partially_supported": 0.04,
        "unsupported": 0.0,
        "insufficient_evidence": -0.08,
    }[support_status]
    score = round(min(max(0.18, evidence_strength * 0.78 + verification_bonus + status_bonus), 0.95), 3)
    return score


def _verification_state(receipts: list[ReceiptEvidence]) -> ClaimVerificationState:
    statuses = [receipt.verification_status for receipt in receipts if receipt.verification_status]
    if not statuses:
        return "not_available"
    if all(status == "verified" for status in statuses):
        return "verified"
    if "verified" in statuses and any(status != "verified" for status in statuses):
        return "mixed"
    if "metadata_mismatch" in statuses:
        return "metadata_mismatch"
    if "unavailable" in statuses:
        return "unavailable"
    return "pending"


def _phrase_bonus(claim_text: str, content: str) -> float:
    content_lower = content.lower()
    phrases = []
    lowered_claim = claim_text.lower()
    if lowered_claim:
        phrases.append(lowered_claim)
    claim_tokens = _tokenize(claim_text)
    if len(claim_tokens) >= 3:
        phrases.append(" ".join(claim_tokens[:3]))
    if any(phrase and phrase in content_lower for phrase in phrases):
        return 0.18
    return 0.0


def _evidence_span(
    document: Document | None,
    citation: ReportCitation,
    matched_terms: list[str],
    *,
    limit: int = 240,
) -> str:
    candidates = [
        citation.snippet or "",
        document.snippet if document is not None and document.snippet else "",
        document.text if document is not None else "",
    ]
    for candidate in candidates:
        text = candidate.strip()
        if not text:
            continue
        lowered = text.lower()
        for term in matched_terms:
            index = lowered.find(term.lower())
            if index >= 0:
                start = max(0, index - 70)
                end = min(len(text), index + max(len(term) + 120, limit - 20))
                return _clean_span(text[start:end], start > 0, end < len(text))
    if citation.snippet:
        return _truncate(citation.snippet, limit=limit)
    if document is not None and document.text:
        return _truncate(document.text, limit=limit)
    return citation.title


def _support_reason(stance: str, matched_terms: list[str], fallback: str) -> str:
    if matched_terms:
        term_text = ", ".join(matched_terms[:4])
        if stance == "supporting":
            return f"Direct topical overlap with the claim via: {term_text}."
        return f"Direct topical overlap with the competing claim via: {term_text}."
    return fallback


def _dedupe_citations(*groups: list[ReportCitation]) -> list[ReportCitation]:
    output: list[ReportCitation] = []
    seen: set[str] = set()
    for group in groups:
        for citation in group:
            if citation.document_id in seen:
                continue
            seen.add(citation.document_id)
            output.append(citation)
    return output


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


def _confidence_label(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.46:
        return "medium"
    return "low"


def _clean_span(text: str, prefix_ellipsis: bool, suffix_ellipsis: bool) -> str:
    cleaned = " ".join(text.split())
    if prefix_ellipsis:
        cleaned = f"...{cleaned}"
    if suffix_ellipsis:
        cleaned = f"{cleaned}..."
    return cleaned


def _truncate(text: str, *, limit: int = 240) -> str:
    value = " ".join(text.strip().split())
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def _tokenize(text: str | None) -> list[str]:
    if not text:
        return []
    return [
        token
        for token in re.findall(r"[a-z0-9']+", text.lower())
        if len(token) > 3 and token not in _STOPWORDS
    ]
