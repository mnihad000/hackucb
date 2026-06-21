import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.model_client import BaseModelClient
from agents.narrative_family_agent import build_narrative_family
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


class _StaticClient(BaseModelClient):
    def __init__(self, payload: dict):
        self.payload = payload

    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        return self.payload


class _FailingClient(BaseModelClient):
    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        raise RuntimeError("boom")


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


def _inputs():
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
    return plan, docs, retrieval, timeline, counter


def test_narrative_family_agent_ignores_unknown_branch_ids():
    plan, docs, retrieval, timeline, counter = _inputs()
    client = _StaticClient(
        {
            "family_title": "Hybrid family",
            "parent_frame": "Cost burden frame",
            "summary": "Hybrid summary",
            "active_branch_id": "family_main",
            "selected_branch_ids": ["family_main", "invented_branch", "family_related_1"],
            "branch_annotations": [
                {
                    "branch_id": "family_related_1",
                    "title": "Green Costs Mutation Branch",
                    "relationship_to_parent": "Mutation branch",
                    "branch_summary": "Tracks a nearby phrase mutation.",
                }
            ],
            "mutation_summary": "Hybrid mutation summary",
            "limitations": [],
            "confidence_score": 0.74,
        }
    )

    result = build_narrative_family("inv_family", plan, retrieval, docs, timeline, counter, model_client=client)

    assert result.generation_method == "hybrid_agent"
    assert result.child_narratives[0].id == "family_main"
    assert all(branch.id != "invented_branch" for branch in result.child_narratives)
    assert any("unknown branch ids" in item.lower() for item in result.limitations)
    assert result.mutation_summary == "Hybrid mutation summary"


def test_narrative_family_agent_falls_back_cleanly_on_failure():
    plan, docs, retrieval, timeline, counter = _inputs()

    result = build_narrative_family(
        "inv_family",
        plan,
        retrieval,
        docs,
        timeline,
        counter,
        model_client=_FailingClient(),
    )

    assert result.generation_method == "deterministic"
    assert any("deterministic family grouping was used" in item.lower() for item in result.limitations)
