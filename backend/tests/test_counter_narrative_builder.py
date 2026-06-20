import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.investigation import InvestigationPlan, InvestigationPlanTimeWindow, RetrievalResult
from services.counter_narrative_builder import build_counter_narratives
from services.investigation_repository import InvestigationRepository


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
        entities=[],
        phrases=phrases,
        metadata=metadata or {},
    )


def test_counter_narrative_builder_detects_opposing_frame():
    plan = _plan()
    docs = [
        _document(
            "doc_1",
            "localnews.com",
            "local_news",
            datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
            title="Hidden energy tax claim spreads",
            text="The hidden energy tax claim spread quickly.",
            snippet="The hidden energy tax claim spread quickly.",
            phrases=["hidden energy tax"],
            metadata={"retrieval_reason_tags": ["exact_phrase"]},
        ),
        _document(
            "doc_2",
            "policyblog.com",
            "commentary",
            datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            title="Infrastructure investment rebuttal",
            text="However, supporters argue the proposal is infrastructure investment and long-term savings.",
            snippet="Supporters argue the proposal is infrastructure investment and long-term savings.",
            phrases=["infrastructure investment", "long-term savings"],
            metadata={"retrieval_reason_tags": ["counter_signal"]},
        ),
        _document(
            "doc_3",
            "statehouse.gov",
            "speech_transcript",
            datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc),
            title="Officials reject the hidden energy tax label",
            text="Officials reject the hidden energy tax label and say the plan lowers future costs.",
            snippet="Officials reject the hidden energy tax label.",
            phrases=["lower future costs"],
            metadata={"retrieval_reason_tags": ["counter_signal"]},
        ),
    ]
    retrieval = RetrievalResult(
        investigation_id="inv_counter",
        plan_snapshot=plan,
        retrieved_document_ids=["doc_1", "doc_2", "doc_3"],
        high_relevance_document_ids=["doc_1", "doc_2", "doc_3"],
        main_narrative_document_ids=["doc_1"],
        counter_narrative_candidate_ids=["doc_2", "doc_3"],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="medium",
    )

    result = build_counter_narratives("inv_counter", plan, retrieval, docs)

    assert len(result.counter_narratives) >= 1
    first = result.counter_narratives[0]
    assert first.supporting_document_ids
    assert first.first_observed_doc_id in {"doc_2", "doc_3"}
    assert first.relationship_to_main_narrative in {"corrective", "reframing", "opposing"}
    assert result.confidence_label in {"medium", "high"}


def test_counter_narrative_builder_handles_absence_case():
    plan = _plan()
    docs = [
        _document(
            "doc_1",
            "localnews.com",
            "local_news",
            datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
            title="Hidden energy tax claim spreads",
            text="The hidden energy tax claim spread quickly.",
            snippet="The hidden energy tax claim spread quickly.",
            phrases=["hidden energy tax"],
        )
    ]
    retrieval = RetrievalResult(
        investigation_id="inv_none",
        plan_snapshot=plan,
        retrieved_document_ids=["doc_1"],
        high_relevance_document_ids=["doc_1"],
        main_narrative_document_ids=["doc_1"],
        counter_narrative_candidate_ids=[],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="low",
    )

    result = build_counter_narratives("inv_none", plan, retrieval, docs)

    assert result.counter_narratives == []
    assert result.confidence_label == "low"
    assert any("No clear counter-narrative candidates" in note for note in result.notes)


def test_counter_narrative_result_persists_and_reloads(tmp_path):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    plan = _plan()
    docs = [
        _document(
            "doc_1",
            "policyblog.com",
            "commentary",
            datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            title="Infrastructure investment rebuttal",
            text="However, supporters argue the proposal is infrastructure investment.",
            snippet="Supporters argue the proposal is infrastructure investment.",
            phrases=["infrastructure investment"],
            metadata={"retrieval_reason_tags": ["counter_signal"]},
        )
    ]
    retrieval = RetrievalResult(
        investigation_id="inv_persist",
        plan_snapshot=plan,
        retrieved_document_ids=["doc_1"],
        high_relevance_document_ids=["doc_1"],
        main_narrative_document_ids=[],
        counter_narrative_candidate_ids=["doc_1"],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="low",
    )
    repo.save_plan("inv_persist", plan.query_text, plan)
    repo.save_retrieval_result(retrieval, docs)

    result = build_counter_narratives("inv_persist", plan, retrieval, docs)
    repo.save_counter_narrative_result(result)

    loaded = repo.get_counter_narrative_result("inv_persist")
    assert loaded is not None
    assert loaded.counter_narratives[0].supporting_document_ids == ["doc_1"]
