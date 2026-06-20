import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.investigation import (
    ClaimCounterpointPair,
    ClaimCounterpointResult,
    FinalReportClaim,
    FinalReportResult,
    FinalReportSections,
    InvestigationPlan,
    InvestigationPlanTimeWindow,
    ReceiptVerificationStatus,
    ReportCitation,
    RetrievalResult,
)
from services.investigation_repository import InvestigationRepository
from services.receipts_builder import build_receipts


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        query_text="Trace the hidden energy tax narrative.",
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="origin",
        entities=["energy", "tax", "policy"],
        search_queries=["\"hidden energy tax\""],
        semantic_queries=["hidden energy tax narrative"],
        target_source_types=["local_news", "national_news", "commentary"],
        requested_outputs=["claim_counterpoints", "receipts", "report"],
        time_window=InvestigationPlanTimeWindow(label="all_time"),
        retrieval_mode="broad",
        risk_notes=[],
        uncertainty_requirements=[],
    )


def _doc(
    doc_id: str,
    title: str,
    snippet: str,
    text: str,
    *,
    source_name: str = "example.com",
    source_type: str = "national_news",
    phrases: list[str] | None = None,
) -> Document:
    return Document(
        id=doc_id,
        source_id=f"domain:{source_name}",
        source_name=source_name,
        source_type=source_type,
        url=f"https://{source_name}/{doc_id}",
        title=title,
        published_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
        collected_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        text=text,
        snippet=snippet,
        language="en",
        content_type="article",
        geographic_scope="national",
        entities=["energy", "policy"],
        phrases=phrases or ["hidden energy tax"],
        metadata={"retrieval_score": 5.0},
    )


def _citation(doc: Document, note: str = "Relevant citation.") -> ReportCitation:
    return ReportCitation(
        document_id=doc.id,
        source_name=doc.source_name,
        source_type=doc.source_type,
        title=doc.title,
        url=doc.url,
        published_at=doc.published_at,
        snippet=doc.snippet,
        relevance_note=note,
    )


def _report(claims: list[FinalReportClaim]) -> FinalReportResult:
    return FinalReportResult(
        investigation_id="inv_receipts",
        plan_snapshot=_plan(),
        report_title="Investigation Report: hidden energy tax",
        report_summary="summary",
        sections=FinalReportSections(
            headline="headline",
            executive_summary="summary",
            observed_facts="facts",
            reasonable_inferences="inferences",
            timeline_summary="timeline",
            counter_narrative_summary="counter",
            limitations="limitations",
            recommended_human_checks="checks",
        ),
        key_claims=claims,
        evidence_packet=[],
        limitations=[],
        recommended_human_checks=[],
        confidence_score=0.7,
        confidence_label="high",
    )


def _claim(
    claim_id: str,
    claim_text: str,
    citations: list[ReportCitation],
) -> FinalReportClaim:
    return FinalReportClaim(
        claim_id=claim_id,
        claim_text=claim_text,
        claim_type="observed_fact",
        confidence_score=0.72,
        caveats=[],
        citations=citations,
        counterpoint_summary="No strong counterpoint found in retrieved evidence.",
        counterpoint_type=None,
        counter_citations=[],
    )


def _counterpoints(pairs: list[ClaimCounterpointPair]) -> ClaimCounterpointResult:
    return ClaimCounterpointResult(
        investigation_id="inv_receipts",
        plan_snapshot=_plan(),
        pairs=pairs,
        unmatched_claim_ids=[],
        limitations=[],
        confidence_score=0.64,
        confidence_label="medium",
    )


def _pair(
    claim_id: str,
    main_claim_text: str,
    counter_claim_text: str,
    *,
    main_receipts: list[ReportCitation],
    counter_receipts: list[ReportCitation],
) -> ClaimCounterpointPair:
    return ClaimCounterpointPair(
        claim_id=claim_id,
        main_claim_text=main_claim_text,
        counter_claim_text=counter_claim_text,
        counter_type="corrective",
        relationship_summary="Counter source disputes the main claim.",
        supporting_document_ids=[receipt.document_id for receipt in main_receipts],
        counter_document_ids=[receipt.document_id for receipt in counter_receipts],
        main_receipts=main_receipts,
        counter_receipts=counter_receipts,
        confidence_score=0.7,
        caveats=[],
    )


def _verification_map(*pairs: tuple[str, ReceiptVerificationStatus]) -> dict[str, ReceiptVerificationStatus]:
    return dict(pairs)


def _retrieval(documents: list[Document]) -> RetrievalResult:
    ids = [doc.id for doc in documents]
    return RetrievalResult(
        investigation_id="inv_receipts",
        plan_snapshot=_plan(),
        retrieved_document_ids=ids,
        high_relevance_document_ids=ids,
        main_narrative_document_ids=ids[:2],
        counter_narrative_candidate_ids=ids[2:],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="high",
    )


def test_receipts_builder_marks_main_claim_supported():
    support_a = _doc(
        "support_a",
        "Hidden energy tax spread widely",
        "Hidden energy tax spread widely across local coverage.",
        "Hidden energy tax spread widely across local coverage and later national coverage.",
    )
    support_b = _doc(
        "support_b",
        "National outlet says hidden energy tax spread widely",
        "A second report says the hidden energy tax spread widely in national coverage.",
        "A second report says the hidden energy tax spread widely in national coverage.",
        source_name="wire.com",
    )
    claim = _claim(
        "claim_supported",
        "Hidden energy tax spread widely in coverage.",
        [_citation(support_a), _citation(support_b)],
    )

    result = build_receipts(
        "inv_receipts",
        _plan(),
        [support_a, support_b],
        _report([claim]),
        _counterpoints([]),
        _verification_map(("support_a", "verified"), ("support_b", "verified")),
    )

    review = result.claim_receipts[0]
    assert review.support_status == "supported"
    assert review.verification_state == "verified"
    assert len(review.supporting_receipts) == 2


def test_receipts_builder_marks_main_claim_partially_supported():
    support = _doc(
        "support_partial",
        "Hidden energy tax spread widely",
        "Hidden energy tax spread widely across a subset of the retrieved sources.",
        "Hidden energy tax spread widely across a subset of the retrieved sources.",
    )
    claim = _claim(
        "claim_partial",
        "Hidden energy tax spread widely in coverage.",
        [_citation(support)],
    )

    result = build_receipts(
        "inv_receipts",
        _plan(),
        [support],
        _report([claim]),
        _counterpoints([]),
        _verification_map(("support_partial", "pending")),
    )

    review = result.claim_receipts[0]
    assert review.support_status == "partially_supported"
    assert review.missing_evidence_notes


def test_receipts_builder_marks_main_claim_unsupported():
    weak = _doc(
        "weak_support",
        "Energy policy debate continues",
        "Energy coverage continues in policy coverage.",
        "Energy coverage continues in policy coverage without confirming the broader narrative.",
        phrases=["policy debate"],
    )
    claim = _claim(
        "claim_unsupported",
        "Hidden energy tax spread widely in coverage.",
        [_citation(weak)],
    )

    result = build_receipts(
        "inv_receipts",
        _plan(),
        [weak],
        _report([claim]),
        _counterpoints([]),
        _verification_map(("weak_support", "pending")),
    )

    review = result.claim_receipts[0]
    assert review.support_status == "unsupported"
    assert review.supporting_receipts


def test_receipts_builder_marks_main_claim_contradicted_and_reviews_counterclaim():
    weak_support = _doc(
        "weak_main",
        "Energy tax debate continues",
        "Energy tax debate continues in policy coverage.",
        "Energy tax debate continues in policy coverage without confirming the full claim.",
        phrases=["energy tax debate"],
    )
    strong_counter = _doc(
        "counter_strong",
        "Fact check says hidden energy tax spread widely is false",
        "Fact check says the hidden energy tax spread widely claim is false and misleading.",
        "Fact check says the hidden energy tax spread widely claim is false and misleading.",
        source_name="factcheck.org",
    )
    claim_text = "Hidden energy tax spread widely in coverage."
    counter_text = "Fact check says the hidden energy tax spread widely claim is false and misleading."
    claim = _claim("claim_contradicted", claim_text, [_citation(weak_support)])
    pair = _pair(
        "claim_contradicted",
        claim_text,
        counter_text,
        main_receipts=[_citation(weak_support)],
        counter_receipts=[_citation(strong_counter)],
    )

    result = build_receipts(
        "inv_receipts",
        _plan(),
        [weak_support, strong_counter],
        _report([claim]),
        _counterpoints([pair]),
        _verification_map(("weak_main", "pending"), ("counter_strong", "metadata_mismatch")),
    )

    main_review = result.claim_receipts[0]
    counter_review = result.counter_claim_receipts[0]
    assert main_review.support_status == "contradicted"
    assert main_review.verification_state == "metadata_mismatch"
    assert counter_review.support_status in {"partially_supported", "supported"}


def test_receipts_builder_marks_claim_insufficient_evidence():
    unrelated = _doc(
        "unrelated",
        "Transit policy gets debate",
        "Transit policy gets debate from local leaders.",
        "Transit policy gets debate from local leaders.",
        phrases=["transit policy"],
    )
    claim = _claim(
        "claim_insufficient",
        "Hidden energy tax spread widely in coverage.",
        [_citation(unrelated)],
    )

    result = build_receipts(
        "inv_receipts",
        _plan(),
        [unrelated],
        _report([claim]),
        _counterpoints([]),
        _verification_map(("unrelated", "pending")),
    )

    review = result.claim_receipts[0]
    assert review.support_status == "insufficient_evidence"
    assert review.supporting_receipts == []


def test_receipts_result_persists_and_reloads_in_workspace(tmp_path):
    support = _doc(
        "support_a",
        "Hidden energy tax spread widely",
        "Hidden energy tax spread widely across local coverage.",
        "Hidden energy tax spread widely across local coverage and later national coverage.",
    )
    claim = _claim("claim_supported", "Hidden energy tax spread widely in coverage.", [_citation(support)])
    result = build_receipts(
        "inv_receipts",
        _plan(),
        [support],
        _report([claim]),
        _counterpoints([]),
        _verification_map(("support_a", "verified")),
    )

    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    repo.save_plan("inv_receipts", _plan().query_text, _plan())
    repo.save_retrieval_result(_retrieval([support]), [support])
    repo.save_receipts_result(result)

    loaded = repo.get_receipts_result("inv_receipts")
    workspace = repo.get_investigation_workspace("inv_receipts")
    assert loaded is not None
    assert loaded.claim_receipts[0].claim_id == "claim_supported"
    assert workspace is not None
    assert workspace.receipts is not None
    assert workspace.receipts.claim_receipts[0].support_status in {"supported", "partially_supported"}
