import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.investigation import (
    CounterNarrative,
    CounterNarrativeResult,
    InvestigationPlan,
    InvestigationPlanTimeWindow,
    RetrievalResult,
    TimelineEvent,
    TimelineResult,
)
from models.investigation import NarrativeFamilyResult
from services.narrative_family_builder import build_narrative_family


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        query_text="Trace the hidden energy tax story.",
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="spread",
        entities=["energy", "tax"],
        search_queries=["hidden energy tax"],
        semantic_queries=["trace hidden energy tax spread"],
        target_source_types=["local_news", "national_news", "commentary"],
        requested_outputs=["timeline", "narrative_family"],
        time_window=InvestigationPlanTimeWindow(label="all_time"),
        retrieval_mode="broad",
        risk_notes=[],
        uncertainty_requirements=[],
    )


def _doc(
    doc_id: str,
    source_name: str,
    source_type: str,
    title: str,
    phrases: list[str],
    published_hour: int,
) -> Document:
    return Document(
        id=doc_id,
        source_id=f"domain:{source_name}",
        source_name=source_name,
        source_type=source_type,
        url=f"https://{source_name}/{doc_id}",
        title=title,
        author=None,
        published_at=datetime(2026, 6, 20, published_hour, 0, tzinfo=timezone.utc),
        collected_at=datetime(2026, 6, 20, 23, 0, tzinfo=timezone.utc),
        text=title,
        snippet=title,
        language="en",
        content_type="article",
        geographic_scope="national",
        entities=["energy"],
        phrases=phrases,
        metadata={"retrieval_score": 5.0},
    )


def test_narrative_family_builder_creates_main_counter_and_related_branches():
    plan = _plan()
    docs = [
        _doc("doc_1", "localwatch.com", "local_news", "Hidden energy tax hits local debate", ["hidden energy tax", "ratepayer burden"], 8),
        _doc("doc_2", "wire.com", "national_news", "Hidden energy tax moves national", ["hidden energy tax", "ratepayer burden"], 11),
        _doc("doc_3", "factcheck.org", "commentary", "Fact check disputes hidden energy tax claim", ["hidden energy tax myth", "fact check"], 12),
        _doc("doc_4", "commentary.example", "commentary", "Green mandate costs framing grows", ["green mandate costs"], 13),
        _doc("doc_5", "metroblog.com", "blog", "Green mandate costs return in blogs", ["green mandate costs"], 15),
    ]
    retrieval = RetrievalResult(
        investigation_id="inv_family",
        plan_snapshot=plan,
        retrieved_document_ids=[doc.id for doc in docs],
        high_relevance_document_ids=["doc_1", "doc_2", "doc_3"],
        main_narrative_document_ids=["doc_1", "doc_2"],
        counter_narrative_candidate_ids=["doc_3"],
        context_document_ids=["doc_4", "doc_5"],
        warnings=[],
        evidence_coverage_confidence="high",
    )
    timeline = TimelineResult(
        investigation_id="inv_family",
        plan_snapshot=plan,
        timeline_events=[
            TimelineEvent(
                id="timeline_1",
                document_id="doc_1",
                timestamp=docs[0].published_at,
                source_name=docs[0].source_name,
                source_type=docs[0].source_type,
                title=docs[0].title,
                url=docs[0].url,
                snippet=docs[0].snippet,
                event_type="first_observed",
                narrative_side="main",
                importance_score=0.8,
                explanation="first",
            )
        ],
        first_observed_doc_id="doc_1",
        timeline_summary="summary",
        limitations=[],
        confidence_score=0.7,
        confidence_label="high",
    )
    counter = CounterNarrativeResult(
        investigation_id="inv_family",
        plan_snapshot=plan,
        counter_narratives=[
            CounterNarrative(
                id="counter_1",
                title="Hidden Energy Tax Myth Corrective Frame",
                summary="summary",
                canonical_phrase="hidden energy tax myth",
                related_phrases=["fact check"],
                supporting_document_ids=["doc_3"],
                first_observed_doc_id="doc_3",
                relationship_to_main_narrative="corrective",
                confidence_score=0.68,
            )
        ],
        notes=[],
        limitations=[],
        confidence_score=0.68,
        confidence_label="medium",
    )

    result = build_narrative_family("inv_family", plan, retrieval, docs, timeline, counter)

    assert result.child_narratives
    assert any("Main Branch" in child.title for child in result.child_narratives)
    assert any("Corrective" in child.title for child in result.child_narratives)
    assert any(child.canonical_phrase == "green mandate costs" for child in result.child_narratives)
    assert result.active_branch_id == "family_main"
    assert result.mutation_summary
    assert result.generation_method == "deterministic"
    assert any(child.branch_type == "main" for child in result.child_narratives)
    assert any(child.branch_type == "counter" for child in result.child_narratives)
    assert result.fastest_growing_child is not None
    assert result.broadest_source_diversity_child is not None
    assert result.confidence_label in {"medium", "high"}
    assert all(step.to_phrase != "hidden energy tax myth" for step in result.mutation_trail)


def test_narrative_family_result_accepts_legacy_cached_json_defaults():
    legacy_payload = {
        "investigation_id": "inv_family",
        "plan_snapshot": _plan().model_dump(mode="json"),
        "family_title": "Legacy Family",
        "parent_frame": "Legacy frame",
        "summary": "Legacy summary",
        "child_narratives": [],
        "fastest_growing_child": None,
        "broadest_source_diversity_child": None,
        "limitations": [],
        "confidence_score": 0.4,
        "confidence_label": "low",
    }

    result = NarrativeFamilyResult.model_validate_json(json.dumps(legacy_payload))

    assert result.active_branch_id is None
    assert result.mutation_summary == ""
    assert result.mutation_trail == []
    assert result.generation_method == "deterministic"
