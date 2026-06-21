import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from agents.json_utils import validate_no_forbidden_language
from agents.model_client import BaseModelClient, CachedModelClient, MockModelClient
from agents.planner_agent import plan_investigation
from agents.prompt_loader import load_prompt
from models.investigation import InvestigationPlan


class _AlwaysFailClient(BaseModelClient):
    def __init__(self) -> None:
        self.call_count = 0

    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        self.call_count += 1
        raise RuntimeError("Simulated planner failure")


def test_mock_planner_schema():
    client = MockModelClient()
    raw = client.generate_json("", "", "planner")
    InvestigationPlan.model_validate(raw)


def test_cached_client_loads_planner_fixture():
    client = CachedModelClient()
    raw = client.generate_json("", "", "planner")
    InvestigationPlan.model_validate(raw)


def test_plan_investigation_extracts_origin_phrase():
    plan = plan_investigation(
        "Where did the 'hidden energy tax' narrative come from?",
        model_client=MockModelClient(),
    )
    assert plan.intent == "origin"
    assert plan.canonical_phrase == "hidden energy tax"
    assert plan.retrieval_mode == "broad"
    assert "timeline" in plan.requested_outputs


def test_plan_investigation_handles_no_canonical_phrase():
    plan = plan_investigation(
        "What narratives are forming around immigration this week?",
        model_client=MockModelClient(),
    )
    assert plan.canonical_phrase is None
    assert plan.intent == "general investigation"
    assert plan.time_window.label == "this_week"
    assert plan.retrieval_mode == "broad"


def test_plan_investigation_extracts_unquoted_phrase():
    plan = plan_investigation(
        "Why is everyone suddenly talking about gas stove bans?",
        model_client=MockModelClient(),
    )
    assert plan.canonical_phrase == "gas stove bans"
    assert plan.intent == "spread"
    assert plan.time_window.label == "recent"


def test_plan_investigation_uses_narrow_with_prior_cluster():
    plan = plan_investigation(
        "How is this narrative spreading now?",
        prior_context={"cluster_id": "narrative_001"},
        model_client=MockModelClient(),
    )
    assert plan.retrieval_mode == "narrow"


def test_plan_investigation_uses_narrow_with_prior_phrase_memory():
    plan = plan_investigation(
        "Give me a follow up on this story.",
        prior_context={"canonical_phrase": "hidden energy tax"},
        model_client=MockModelClient(),
    )
    assert plan.retrieval_mode == "narrow"


def test_plan_investigation_adds_requested_outputs_from_query():
    plan = plan_investigation(
        "Give me a graph, report, and receipts for the hidden energy tax narrative.",
        model_client=MockModelClient(),
    )
    assert "graph" in plan.requested_outputs
    assert "report" in plan.requested_outputs
    assert "receipts" in plan.requested_outputs


def test_plan_investigation_expands_source_types_for_official_context():
    plan = plan_investigation(
        "Find source diversity around official government remarks about the hidden energy tax narrative.",
        model_client=MockModelClient(),
    )
    assert plan.intent == "source-ecosystem"
    assert "official_statement" in plan.target_source_types
    assert "community_post" in plan.target_source_types


def test_plan_investigation_falls_back_on_model_failure():
    client = _AlwaysFailClient()
    plan = plan_investigation(
        "Show me the counter-narratives around this education bill.",
        model_client=client,
    )
    assert client.call_count == 2
    assert plan.intent == "counter-narrative"
    assert isinstance(plan, InvestigationPlan)


def test_plan_investigation_ignores_cached_fixture_for_live_queries():
    plan = plan_investigation(
        "What narratives are forming around immigration this week?",
        model_client=CachedModelClient(),
    )
    assert plan.query_text == "What narratives are forming around immigration this week?"
    assert plan.canonical_phrase is None
    assert plan.time_window.label == "this_week"
    assert "hidden energy tax" not in plan.topic.lower()
    assert "hidden energy tax" not in " ".join(plan.search_queries).lower()


def test_plan_investigation_baseline_avoids_forbidden_origin_language():
    client = _AlwaysFailClient()
    plan = plan_investigation(
        "Where did the hidden energy tax narrative come from?",
        model_client=client,
    )
    validate_no_forbidden_language(plan.model_dump())


def test_forbidden_language_rejects_origin_overclaim():
    with pytest.raises(ValueError, match="true origin"):
        validate_no_forbidden_language({"summary": "We found the true origin of the narrative."})


def test_prompt_loader_planner():
    text = load_prompt("planner")
    assert "Query Planner Agent" in text
    assert "InvestigationPlan schema exactly" in text
