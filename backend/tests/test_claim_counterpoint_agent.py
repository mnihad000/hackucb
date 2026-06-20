import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.claim_counterpoint_agent import build_claim_counterpoints
from models.document import Document
from models.investigation import (
    AnalystResult,
    CandidateClaim,
    ClaimCounterpointResult,
    CounterNarrative,
    CounterNarrativeResult,
    DraftReportSections,
    InvestigationPlan,
    InvestigationPlanTimeWindow,
    RetrievalResult,
)
from services.investigation_repository import InvestigationRepository


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        query_text="Trace the hidden energy tax narrative.",
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="origin",
        entities=["energy", "policy", "tax"],
        search_queries=["\"hidden energy tax\""],
        semantic_queries=["hidden energy tax narrative"],
        target_source_types=["local_news", "national_news", "commentary"],
        requested_outputs=["counter_narratives", "claim_counterpoints", "report"],
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
    snippet: str,
    text: str,
    *,
    phrases: list[str],
    entities: list[str] | None = None,
    retrieval_score: float = 4.4,
) -> Document:
    return Document(
        id=doc_id,
        source_id=f"domain:{source_name}",
        source_name=source_name,
        source_type=source_type,
        url=f"https://{source_name}/{doc_id}",
        title=title,
        published_at=datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
        collected_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
        text=text,
        snippet=snippet,
        language="en",
        content_type="article",
        geographic_scope="national",
        entities=entities or ["energy", "policy"],
        phrases=phrases,
        metadata={"retrieval_score": retrieval_score},
    )


def _analyst(claims: list[CandidateClaim]) -> AnalystResult:
    return AnalystResult(
        investigation_id="inv_counterpoints",
        plan_snapshot=_plan(),
        draft_report_sections=DraftReportSections(
            executive_summary="summary",
            observed_facts="facts",
            reasonable_inferences="inferences",
            timeline_summary="timeline",
            counter_narrative_summary="counter",
            uncertainties="uncertain",
        ),
        candidate_claims=claims,
        limitations=[],
        recommended_human_checks=[],
        confidence_score=0.72,
        confidence_label="high",
    )


def _retrieval(documents: list[Document], counter_ids: list[str]) -> RetrievalResult:
    ids = [doc.id for doc in documents]
    return RetrievalResult(
        investigation_id="inv_counterpoints",
        plan_snapshot=_plan(),
        retrieved_document_ids=ids,
        high_relevance_document_ids=ids,
        main_narrative_document_ids=[ids[0]],
        counter_narrative_candidate_ids=counter_ids,
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="high",
    )


def _counter_result(counter_doc_ids: list[str]) -> CounterNarrativeResult:
    return CounterNarrativeResult(
        investigation_id="inv_counterpoints",
        plan_snapshot=_plan(),
        counter_narratives=[
            CounterNarrative(
                id="counter_1",
                title="Alternative energy savings frame",
                summary="Supporters argue the policy is an investment with long-term savings.",
                canonical_phrase="energy savings",
                related_phrases=["long-term savings"],
                supporting_document_ids=counter_doc_ids,
                first_observed_doc_id=counter_doc_ids[0] if counter_doc_ids else None,
                relationship_to_main_narrative="reframing",
                confidence_score=0.68,
            )
        ]
        if counter_doc_ids
        else [],
        notes=[],
        limitations=[],
        confidence_score=0.6,
        confidence_label="medium",
    )


def test_claim_counterpoint_agent_builds_opposing_corrective_and_reframing_pairs():
    docs = [
        _doc(
            "main_1",
            "localwatch.com",
            "local_news",
            "Hidden energy tax spreads",
            "Coverage says the hidden energy tax claim is spreading.",
            "Coverage says the hidden energy tax claim is spreading.",
            phrases=["hidden energy tax"],
        ),
        _doc(
            "oppose_1",
            "commentaryhub.com",
            "commentary",
            "Critics oppose hidden energy tax framing",
            "Critics oppose the hidden energy tax line and challenge the policy claim.",
            "Critics oppose the hidden energy tax line and challenge the policy claim.",
            phrases=["hidden energy tax"],
        ),
        _doc(
            "correct_1",
            "factcheck.org",
            "national_news",
            "Fact check refutes hidden energy tax claim",
            "Fact check refutes the hidden energy tax claim as misleading.",
            "Fact check refutes the hidden energy tax claim as misleading.",
            phrases=["hidden energy tax"],
        ),
        _doc(
            "reframe_1",
            "analysisdesk.com",
            "commentary",
            "Supporters say policy brings savings",
            "However, supporters argue the policy delivers energy savings instead.",
            "However, supporters argue the policy delivers energy savings instead.",
            phrases=["energy savings", "policy benefits"],
            entities=["energy", "policy"],
        ),
    ]
    claims = [
        CandidateClaim(
            id="claim_oppose",
            claim_text="Critics accepted the hidden energy tax line.",
            claim_type="observed_fact",
            supporting_document_ids=["main_1"],
            confidence_score=0.8,
        ),
        CandidateClaim(
            id="claim_correct",
            claim_text="The hidden energy tax allegation is accurate and not misleading.",
            claim_type="inference",
            supporting_document_ids=["main_1"],
            confidence_score=0.72,
        ),
        CandidateClaim(
            id="claim_reframe",
            claim_text="The policy brings no benefits or long-term savings and is only a hidden energy tax.",
            claim_type="inference",
            supporting_document_ids=["main_1"],
            confidence_score=0.7,
        ),
    ]

    result = build_claim_counterpoints(
        "inv_counterpoints",
        _plan(),
        _retrieval(docs, ["oppose_1", "correct_1", "reframe_1"]),
        docs,
        _counter_result(["reframe_1"]),
        _analyst(claims),
    )

    assert len(result.pairs) == 3
    pair_types = {pair.claim_id: pair.counter_type for pair in result.pairs}
    assert pair_types["claim_oppose"] == "opposing"
    assert pair_types["claim_correct"] == "corrective"
    assert pair_types["claim_reframe"] == "reframing"


def test_claim_counterpoint_agent_marks_claim_unmatched_when_no_valid_counter_exists():
    docs = [
        _doc(
            "main_1",
            "localwatch.com",
            "local_news",
            "Hidden energy tax spreads",
            "Coverage says the hidden energy tax claim is spreading.",
            "Coverage says the hidden energy tax claim is spreading.",
            phrases=["hidden energy tax"],
        ),
        _doc(
            "generic_1",
            "opinionwire.com",
            "commentary",
            "Critics oppose the mayor",
            "Critics oppose the mayor for unrelated reasons.",
            "Critics oppose the mayor for unrelated reasons.",
            phrases=["city hall"],
            entities=["mayor"],
        ),
    ]
    claim = CandidateClaim(
        id="claim_main",
        claim_text="The hidden energy tax claim spread widely.",
        claim_type="observed_fact",
        supporting_document_ids=["main_1"],
        confidence_score=0.8,
    )

    result = build_claim_counterpoints(
        "inv_counterpoints",
        _plan(),
        _retrieval(docs, ["generic_1"]),
        docs,
        _counter_result([]),
        _analyst([claim]),
    )

    assert result.pairs == []
    assert result.unmatched_claim_ids == ["claim_main"]


def test_claim_counterpoint_agent_prefers_better_topic_match_over_noisier_candidate():
    docs = [
        _doc(
            "main_1",
            "localwatch.com",
            "local_news",
            "Hidden energy tax spreads",
            "Coverage says the hidden energy tax claim is spreading.",
            "Coverage says the hidden energy tax claim is spreading.",
            phrases=["hidden energy tax"],
        ),
        _doc(
            "noisy_1",
            "commentaryhub.com",
            "commentary",
            "Critics challenge leaders",
            "Critics challenge leaders over broad political concerns.",
            "Critics challenge leaders over broad political concerns.",
            phrases=["political concerns"],
            entities=["leaders"],
            retrieval_score=4.9,
        ),
        _doc(
            "best_1",
            "factcheck.org",
            "national_news",
            "Fact check refutes hidden energy tax claim",
            "Fact check refutes the hidden energy tax claim directly.",
            "Fact check refutes the hidden energy tax claim directly.",
            phrases=["hidden energy tax"],
            retrieval_score=4.3,
        ),
    ]
    claim = CandidateClaim(
        id="claim_main",
        claim_text="The hidden energy tax allegation is accurate.",
        claim_type="inference",
        supporting_document_ids=["main_1"],
        confidence_score=0.76,
    )

    result = build_claim_counterpoints(
        "inv_counterpoints",
        _plan(),
        _retrieval(docs, ["noisy_1", "best_1"]),
        docs,
        _counter_result(["best_1"]),
        _analyst([claim]),
    )

    assert len(result.pairs) == 1
    assert result.pairs[0].counter_document_ids == ["best_1"]


def test_claim_counterpoint_result_persists_and_reloads_in_workspace(tmp_path):
    docs = [
        _doc(
            "main_1",
            "localwatch.com",
            "local_news",
            "Hidden energy tax spreads",
            "Coverage says the hidden energy tax claim is spreading.",
            "Coverage says the hidden energy tax claim is spreading.",
            phrases=["hidden energy tax"],
        ),
        _doc(
            "correct_1",
            "factcheck.org",
            "national_news",
            "Fact check refutes hidden energy tax claim",
            "Fact check refutes the hidden energy tax claim as misleading.",
            "Fact check refutes the hidden energy tax claim as misleading.",
            phrases=["hidden energy tax"],
        ),
    ]
    claim = CandidateClaim(
        id="claim_main",
        claim_text="The hidden energy tax allegation is accurate.",
        claim_type="inference",
        supporting_document_ids=["main_1"],
        confidence_score=0.76,
    )
    result = build_claim_counterpoints(
        "inv_counterpoints",
        _plan(),
        _retrieval(docs, ["correct_1"]),
        docs,
        _counter_result(["correct_1"]),
        _analyst([claim]),
    )

    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    repo.save_plan("inv_counterpoints", _plan().query_text, _plan())
    repo.save_retrieval_result(_retrieval(docs, ["correct_1"]), docs)
    repo.save_claim_counterpoint_result(result)

    loaded: ClaimCounterpointResult | None = repo.get_claim_counterpoint_result("inv_counterpoints")
    workspace = repo.get_investigation_workspace("inv_counterpoints")
    assert loaded is not None
    assert loaded.pairs[0].claim_id == "claim_main"
    assert workspace is not None
    assert workspace.claim_counterpoints is not None
    assert workspace.claim_counterpoints.pairs[0].counter_type == "corrective"
