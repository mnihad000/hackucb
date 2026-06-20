import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.investigation import InvestigationPlan, InvestigationPlanTimeWindow, RetrievalResult
from services.analyst_builder import build_analyst_result
from services.counter_narrative_builder import build_counter_narratives
from services.investigation_repository import InvestigationRepository
from services.timeline_builder import build_timeline


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        query_text="Where did the 'hidden energy tax' narrative come from?",
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="origin",
        entities=["hidden", "energy", "tax"],
        search_queries=["\"hidden energy tax\""],
        semantic_queries=["Investigate hidden energy tax"],
        target_source_types=["blog", "local_news", "national_news", "commentary"],
        requested_outputs=["timeline", "counter_narratives", "report", "receipts"],
        time_window=InvestigationPlanTimeWindow(label="all_time"),
        retrieval_mode="broad",
        risk_notes=[],
        uncertainty_requirements=["State clearly when earlier sources may exist outside the dataset."],
    )


def _document(
    doc_id: str,
    source_name: str,
    source_type: str,
    published_at: datetime | None,
    *,
    title: str,
    text: str,
    snippet: str,
    phrases: list[str],
    metadata: dict | None = None,
) -> Document:
    return Document(
        id=doc_id,
        source_id=f"domain:{source_name}",
        source_name=source_name,
        source_type=source_type,
        url=f"https://{source_name}/{doc_id}",
        title=title,
        published_at=published_at,
        collected_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
        text=text,
        snippet=snippet,
        language="en",
        content_type="article",
        geographic_scope="national",
        entities=["energy", "policy"],
        phrases=phrases,
        metadata=metadata or {},
    )


def _documents() -> list[Document]:
    return [
        _document(
            "doc_1",
            "localwatch.com",
            "local_news",
            datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
            title="Hidden energy tax appears locally",
            text="The hidden energy tax phrase appears in local coverage.",
            snippet="The hidden energy tax phrase appears in local coverage.",
            phrases=["hidden energy tax"],
            metadata={"retrieval_score": 5.4, "retrieval_reason_tags": ["exact_phrase"]},
        ),
        _document(
            "doc_2",
            "civicblog.com",
            "blog",
            datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            title="Blog repeats hidden energy tax claim",
            text="Blog coverage repeats the hidden energy tax claim.",
            snippet="Blog coverage repeats the hidden energy tax claim.",
            phrases=["hidden energy tax"],
            metadata={"retrieval_score": 4.6},
        ),
        _document(
            "doc_3",
            "reuters.com",
            "national_news",
            datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
            title="National outlet covers hidden energy tax",
            text="National coverage takes up the hidden energy tax phrase.",
            snippet="National coverage takes up the hidden energy tax phrase.",
            phrases=["hidden energy tax"],
            metadata={"retrieval_score": 5.1},
        ),
        _document(
            "doc_4",
            "statehouse.gov",
            "speech_transcript",
            datetime(2026, 6, 2, 17, 0, tzinfo=timezone.utc),
            title="Official remarks mention hidden energy tax",
            text="The governor mentions the hidden energy tax criticism in remarks.",
            snippet="The governor mentions the hidden energy tax criticism.",
            phrases=["hidden energy tax"],
            metadata={"retrieval_score": 4.1},
        ),
        _document(
            "doc_5",
            "analysisdesk.com",
            "commentary",
            datetime(2026, 6, 3, 8, 0, tzinfo=timezone.utc),
            title="Infrastructure investment rebuttal",
            text="However, supporters argue the policy is infrastructure investment and long-term savings.",
            snippet="Supporters argue the policy is infrastructure investment and long-term savings.",
            phrases=["infrastructure investment", "long-term savings"],
            metadata={"retrieval_score": 4.0, "retrieval_reason_tags": ["counter_signal"]},
        ),
    ]


def _retrieval(plan: InvestigationPlan) -> RetrievalResult:
    return RetrievalResult(
        investigation_id="inv_analyst",
        plan_snapshot=plan,
        retrieved_document_ids=["doc_1", "doc_2", "doc_3", "doc_4", "doc_5"],
        high_relevance_document_ids=["doc_1", "doc_3", "doc_4", "doc_5"],
        main_narrative_document_ids=["doc_1", "doc_2", "doc_3", "doc_4"],
        counter_narrative_candidate_ids=["doc_5"],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="high",
    )


def test_analyst_builder_produces_sections_and_claims():
    plan = _plan()
    docs = _documents()
    retrieval = _retrieval(plan)
    timeline = build_timeline("inv_analyst", plan, retrieval, docs)
    counter = build_counter_narratives("inv_analyst", plan, retrieval, docs)

    result = build_analyst_result("inv_analyst", plan, retrieval, docs, timeline, counter)

    assert "first observed" in result.draft_report_sections.executive_summary.lower()
    assert result.candidate_claims
    claim_types = {claim.claim_type for claim in result.candidate_claims}
    assert "observed_fact" in claim_types
    assert "inference" in claim_types
    assert "uncertainty" in claim_types
    assert result.recommended_human_checks
    assert result.confidence_label in {"medium", "high"}


def test_analyst_result_persists_and_reloads(tmp_path):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    plan = _plan()
    docs = _documents()
    retrieval = _retrieval(plan)
    timeline = build_timeline("inv_analyst", plan, retrieval, docs)
    counter = build_counter_narratives("inv_analyst", plan, retrieval, docs)
    result = build_analyst_result("inv_analyst", plan, retrieval, docs, timeline, counter)

    repo.save_plan("inv_analyst", plan.query_text, plan)
    repo.save_retrieval_result(retrieval, docs)
    repo.save_timeline_result(timeline)
    repo.save_counter_narrative_result(counter)
    repo.save_analyst_result(result)

    loaded = repo.get_analyst_result("inv_analyst")
    assert loaded is not None
    assert loaded.candidate_claims[0].id == result.candidate_claims[0].id
