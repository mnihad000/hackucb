import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.receipts_agent import build_receipts
from models.document import Document
from models.investigation import (
    ClaimCounterpointPair,
    ClaimCounterpointResult,
    FinalReportClaim,
    FinalReportResult,
    FinalReportSections,
    InvestigationPlan,
    InvestigationPlanTimeWindow,
    ReportCitation,
)


def _plan(query_text: str = "Trace the hidden energy tax narrative.") -> InvestigationPlan:
    return InvestigationPlan(
        query_text=query_text,
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="origin",
        entities=["energy", "tax"],
        search_queries=["\"hidden energy tax\""],
        semantic_queries=["hidden energy tax narrative"],
        target_source_types=["local_news", "national_news"],
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
) -> Document:
    return Document(
        id=doc_id,
        source_id=f"domain:{source_name}",
        source_name=source_name,
        source_type="national_news",
        url=f"https://{source_name}/{doc_id}",
        title=title,
        author=None,
        published_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
        collected_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        text=text,
        snippet=snippet,
        language="en",
        content_type="article",
        geographic_scope="national",
        entities=["energy", "policy"],
        phrases=["hidden energy tax"],
        metadata={"retrieval_score": 5.0},
    )


def _citation(doc_id: str, *, source_name: str = "example.com", note: str = "Relevant citation.") -> ReportCitation:
    return ReportCitation(
        document_id=doc_id,
        source_name=source_name,
        source_type="national_news",
        title=f"title-{doc_id}",
        url=f"https://{source_name}/{doc_id}",
        published_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
        snippet=f"snippet for {doc_id}",
        relevance_note=note,
    )


def _claim(claim_id: str, claim_text: str, citations: list[ReportCitation]) -> FinalReportClaim:
    return FinalReportClaim(
        claim_id=claim_id,
        claim_text=claim_text,
        claim_type="observed_fact",
        confidence_score=0.7,
        caveats=[],
        citations=citations,
        counterpoint_summary=None,
        counterpoint_type=None,
        counter_citations=[],
    )


def _report(
    claims: list[FinalReportClaim],
    *,
    investigation_id: str = "inv_receipts",
    query_text: str = "Trace the hidden energy tax narrative.",
) -> FinalReportResult:
    return FinalReportResult(
        investigation_id=investigation_id,
        plan_snapshot=_plan(query_text),
        report_title="Investigation Report",
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


def _pair(
    claim_id: str,
    counter_claim_text: str,
    *,
    counter_doc_id: str,
    confidence_score: float,
) -> ClaimCounterpointPair:
    return ClaimCounterpointPair(
        claim_id=claim_id,
        main_claim_text="Hidden energy tax spread widely in coverage.",
        counter_claim_text=counter_claim_text,
        counter_type="corrective",
        relationship_summary="Counter source disputes the main claim.",
        supporting_document_ids=["doc_main"],
        counter_document_ids=[counter_doc_id],
        main_receipts=[_citation("doc_main")],
        counter_receipts=[_citation(counter_doc_id, source_name="factcheck.org")],
        confidence_score=confidence_score,
        caveats=[],
    )


def _counterpoints(pairs: list[ClaimCounterpointPair]) -> ClaimCounterpointResult:
    return ClaimCounterpointResult(
        investigation_id="inv_counter",
        plan_snapshot=_plan("stale query"),
        pairs=pairs,
        unmatched_claim_ids=["claim_missing", "claim_main"],
        limitations=[],
        confidence_score=0.6,
        confidence_label="medium",
    )


def test_receipts_agent_normalizes_duplicate_documents_and_bad_verification_state():
    doc_thin = _doc(
        "doc_main",
        "Hidden energy tax spread",
        "Hidden energy tax spread in coverage.",
        "Hidden energy tax spread.",
    )
    doc_rich = _doc(
        "doc_main",
        "Hidden energy tax spread widely",
        "Hidden energy tax spread widely in local and national coverage.",
        "Hidden energy tax spread widely in local and national coverage with repeated discussion.",
    )
    claim = _claim(
        "claim_main",
        "Hidden energy tax spread widely in coverage.",
        [_citation("doc_main"), _citation("doc_missing")],
    )
    duplicate_claim = _claim(
        "claim_main",
        "Duplicate claim that should be collapsed.",
        [_citation("doc_main")],
    )

    result = build_receipts(
        "inv_receipts",
        _plan(),
        [doc_thin, doc_rich],
        _report(
            [claim, duplicate_claim],
            investigation_id="inv_other",
            query_text="stale query",
        ),
        None,
        {"doc_main": "bad_status", "doc_unused": "verified"},
    )

    assert len(result.claim_receipts) == 1
    assert result.claim_receipts[0].claim_id == "claim_main"
    assert result.claim_receipts[0].verification_state == "pending"
    assert any("Duplicate retrieved document IDs were collapsed" in note for note in result.limitations)
    assert any("Duplicate report claim IDs were collapsed" in note for note in result.limitations)
    assert any("references citation documents not present" in note for note in result.limitations)
    assert any("Invalid verification statuses were normalized to pending" in note for note in result.limitations)
    assert any("report artifact whose investigation_id did not match" in note for note in result.limitations)
    assert any("report/plan query mismatch" in note for note in result.limitations)


def test_receipts_agent_filters_counterpoints_to_current_report_and_highest_confidence_pair():
    main_doc = _doc(
        "doc_main",
        "Hidden energy tax spread widely",
        "Hidden energy tax spread widely in coverage.",
        "Hidden energy tax spread widely in coverage and later national pickup.",
    )
    counter_low = _doc(
        "doc_counter_low",
        "Commentary disputes the claim",
        "A commentary post disputes the claim with limited grounding.",
        "A commentary post disputes the hidden energy tax spread widely claim with limited grounding.",
        source_name="commentary.example",
    )
    counter_high = _doc(
        "doc_counter_high",
        "Fact check says the claim is false",
        "Fact check says the hidden energy tax spread widely claim is false and misleading.",
        "Fact check says the hidden energy tax spread widely claim is false and misleading.",
        source_name="factcheck.org",
    )

    result = build_receipts(
        "inv_receipts",
        _plan(),
        [main_doc, counter_low, counter_high],
        _report([_claim("claim_main", "Hidden energy tax spread widely in coverage.", [_citation("doc_main")])]),
        _counterpoints(
            [
                _pair("claim_main", "Low confidence counter claim.", counter_doc_id="doc_counter_low", confidence_score=0.58),
                _pair("claim_main", "High confidence counter claim.", counter_doc_id="doc_counter_high", confidence_score=0.87),
                _pair("claim_other", "Unlinked counter claim.", counter_doc_id="doc_counter_low", confidence_score=0.93),
            ]
        ),
        {"doc_main": "verified", "doc_counter_low": "pending", "doc_counter_high": "metadata_mismatch"},
    )

    assert len(result.counter_claim_receipts) == 1
    assert result.counter_claim_receipts[0].claim_text == "High confidence counter claim."
    assert any("not linked to current report claims were ignored" in note for note in result.limitations)
    assert any("Duplicate claim counterpoints were reduced to the highest-confidence pair" in note for note in result.limitations)
    assert any("claim counterpoints from a different investigation" in note for note in result.limitations)
