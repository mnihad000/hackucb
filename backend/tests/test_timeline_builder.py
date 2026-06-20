import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.investigation import (
    InvestigationPlan,
    InvestigationPlanTimeWindow,
    RetrievalResult,
)
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
        requested_outputs=["timeline", "counter_narratives", "source_diversity"],
        time_window=InvestigationPlanTimeWindow(label="all_time"),
        retrieval_mode="broad",
        risk_notes=[],
        uncertainty_requirements=[],
    )


def _document(
    doc_id: str,
    source_name: str,
    source_type: str,
    published_at: datetime | None,
    *,
    title: str,
    text: str | None = None,
    snippet: str | None = None,
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
        text=text or title,
        snippet=snippet or title,
        language="en",
        content_type="article",
        geographic_scope="national",
        entities=[],
        phrases=["hidden energy tax"],
        metadata=metadata or {},
    )


def _documents() -> list[Document]:
    return [
        _document(
            "doc_1",
            "springfieldgazette.com",
            "local_news",
            datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
            title="Hidden energy tax appears locally",
            metadata={"retrieval_score": 5.5, "retrieval_reason_tags": ["exact_phrase"]},
        ),
        _document(
            "doc_2",
            "civicblog.com",
            "blog",
            datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc),
            title="Blog amplifies hidden energy tax claim",
            metadata={"retrieval_score": 4.2},
        ),
        _document(
            "doc_3",
            "reuters.com",
            "national_news",
            datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
            title="National outlet covers hidden energy tax",
            metadata={"retrieval_score": 5.1},
        ),
        _document(
            "doc_4",
            "statehouse.gov",
            "speech_transcript",
            datetime(2026, 6, 2, 18, 0, tzinfo=timezone.utc),
            title="Governor remarks on hidden energy tax",
            metadata={"retrieval_score": 3.5},
        ),
        _document(
            "doc_5",
            "analysisdesk.com",
            "commentary",
            datetime(2026, 6, 3, 9, 0, tzinfo=timezone.utc),
            title="Counter framing rejects hidden energy tax",
            metadata={"retrieval_score": 4.0, "retrieval_reason_tags": ["counter_signal"]},
        ),
        _document(
            "doc_6",
            "cityobserver.com",
            "local_news",
            datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
            title="Hidden energy tax resurfaces after several days",
            metadata={"retrieval_score": 3.2},
        ),
        _document(
            "doc_7",
            "forum.example",
            "forum",
            None,
            title="Undated forum post",
        ),
    ]


def _retrieval(plan: InvestigationPlan) -> RetrievalResult:
    return RetrievalResult(
        investigation_id="inv_1",
        plan_snapshot=plan,
        retrieved_document_ids=[f"doc_{index}" for index in range(1, 8)],
        high_relevance_document_ids=["doc_1", "doc_3", "doc_4", "doc_5"],
        main_narrative_document_ids=["doc_1", "doc_2", "doc_3", "doc_4", "doc_6"],
        counter_narrative_candidate_ids=["doc_5"],
        context_document_ids=["doc_7"],
        warnings=[],
        evidence_coverage_confidence="high",
    )


def test_timeline_builder_orders_events_and_sets_first_observed():
    plan = _plan()
    result = build_timeline("inv_1", plan, _retrieval(plan), _documents())

    assert result.first_observed_doc_id == "doc_1"
    assert [event.document_id for event in result.timeline_events] == [
        "doc_1",
        "doc_2",
        "doc_3",
        "doc_4",
        "doc_5",
        "doc_6",
    ]
    assert result.timeline_events[0].event_type == "first_observed"


def test_timeline_builder_handles_undated_documents_and_limitations():
    plan = _plan()
    result = build_timeline("inv_1", plan, _retrieval(plan), _documents())

    assert len(result.timeline_events) == 6
    assert any("published dates were unavailable" in limitation for limitation in result.limitations)
    assert "first observed in our dataset" in result.timeline_summary.lower()


def test_timeline_builder_assigns_expected_event_types():
    plan = _plan()
    result = build_timeline("inv_1", plan, _retrieval(plan), _documents())
    by_doc_id = {event.document_id: event for event in result.timeline_events}

    assert by_doc_id["doc_2"].event_type == "early_amplification"
    assert by_doc_id["doc_3"].event_type == "broader_pickup"
    assert by_doc_id["doc_4"].event_type == "official_mention"
    assert by_doc_id["doc_5"].event_type == "counter_narrative_entry"
    assert by_doc_id["doc_6"].event_type == "resurfacing"


def test_timeline_builder_confidence_drops_with_weak_timestamp_coverage():
    plan = _plan()
    docs = [
        _document(
            "doc_a",
            "example.com",
            "local_news",
            datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
            title="Hidden energy tax local hit",
        ),
        _document(
            "doc_b",
            "example-two.com",
            "blog",
            None,
            title="Undated follow-up",
        ),
    ]
    retrieval = RetrievalResult(
        investigation_id="inv_low",
        plan_snapshot=plan,
        retrieved_document_ids=["doc_a", "doc_b"],
        high_relevance_document_ids=["doc_a"],
        main_narrative_document_ids=["doc_a"],
        counter_narrative_candidate_ids=[],
        context_document_ids=["doc_b"],
        warnings=[],
        evidence_coverage_confidence="low",
    )

    result = build_timeline("inv_low", plan, retrieval, docs)

    assert result.confidence_label == "low"
    assert 0.15 <= result.confidence_score <= 0.44
    assert any("small number of dated documents" in limitation for limitation in result.limitations)


def test_timeline_result_persists_and_reloads(tmp_path):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    plan = _plan()
    retrieval = _retrieval(plan)
    docs = _documents()
    repo.save_plan("inv_1", plan.query_text, plan)
    repo.save_retrieval_result(retrieval, docs)

    result = build_timeline("inv_1", plan, retrieval, docs)
    repo.save_timeline_result(result)

    loaded = repo.get_timeline_result("inv_1")
    assert loaded is not None
    assert loaded.first_observed_doc_id == "doc_1"
    assert loaded.timeline_events[2].event_type == "broader_pickup"
