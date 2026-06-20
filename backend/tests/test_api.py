import sys
import os
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DEMO_MODE"] = "true"

import pytest
from fastapi.testclient import TestClient
from main import app
from api import narratives as narratives_api
from models.document import Document
from models.investigation import InvestigationPlan, RetrievalResult, TimelineResult
from services.document_store import live_store
from services.investigation_repository import InvestigationRepository

client = TestClient(app)


def _timeline_docs() -> list[Document]:
    return [
        Document(
            id="doc_1",
            source_id="domain:springfieldgazette.com",
            source_name="springfieldgazette.com",
            source_type="local_news",
            url="https://springfieldgazette.com/doc_1",
            title="Hidden energy tax appears locally",
            published_at=datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
            collected_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
            text="Hidden energy tax appears locally",
            snippet="Hidden energy tax appears locally",
            language="en",
            content_type="article",
            geographic_scope="local",
            entities=[],
            phrases=["hidden energy tax"],
            metadata={"retrieval_score": 5.0},
        ),
        Document(
            id="doc_2",
            source_id="domain:reuters.com",
            source_name="reuters.com",
            source_type="national_news",
            url="https://reuters.com/doc_2",
            title="National coverage follows",
            published_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
            collected_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
            text="National coverage follows the hidden energy tax claim",
            snippet="National coverage follows the hidden energy tax claim",
            language="en",
            content_type="article",
            geographic_scope="national",
            entities=[],
            phrases=["hidden energy tax"],
            metadata={"retrieval_score": 4.5},
        ),
    ]


def _timeline_retrieval(investigation_id: str, plan: InvestigationPlan) -> RetrievalResult:
    return RetrievalResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        retrieved_document_ids=["doc_1", "doc_2"],
        high_relevance_document_ids=["doc_1", "doc_2"],
        main_narrative_document_ids=["doc_1", "doc_2"],
        counter_narrative_candidate_ids=[],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="medium",
    )


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["demo_mode"] is True


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "endpoints" in data
    assert any("/api/investigate" in endpoint for endpoint in data["endpoints"])
    assert any("/api/investigations/{id}" in endpoint for endpoint in data["endpoints"])
    assert any("/api/investigations/{id}/timeline" in endpoint for endpoint in data["endpoints"])
    assert any("/api/investigations/{id}/counter-narratives" in endpoint for endpoint in data["endpoints"])
    assert any("/api/investigations/{id}/analyst" in endpoint for endpoint in data["endpoints"])
    assert any("/api/investigations/{id}/report" in endpoint for endpoint in data["endpoints"])
    assert any("/api/trending" in endpoint for endpoint in data["endpoints"])


def test_list_narratives():
    r = client.get("/api/narratives")
    assert r.status_code == 200
    narratives = r.json()
    assert len(narratives) == 2
    # Should be sorted by spike_score descending
    assert narratives[0]["spike_score"] >= narratives[1]["spike_score"]


def test_get_narrative_energy():
    r = client.get("/api/narratives/narrative_001")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "narrative_001"
    assert data["label"] == "Hidden Energy Tax"
    assert len(data["mutation_trail"]) == 4


def test_get_narrative_immigration():
    r = client.get("/api/narratives/narrative_002")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "narrative_002"


def test_get_narrative_not_found():
    r = client.get("/api/narratives/narrative_999")
    assert r.status_code == 404


def test_narrative_timeline():
    r = client.get("/api/narratives/narrative_001/timeline")
    assert r.status_code == 200
    timeline = r.json()
    assert isinstance(timeline, list)
    assert len(timeline) > 0
    dates = [e["date"] for e in timeline]
    assert dates == sorted(dates)


def test_investigate_returns_planner_artifact():
    r = client.post("/api/investigate", json={"query_text": "Where did the 'hidden energy tax' narrative come from?"})
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "planning_completed"
    assert payload["current_stage"] == "planner"
    assert payload["query_text"] == "Where did the 'hidden energy tax' narrative come from?"
    assert "plan" in payload
    assert payload["plan"]["intent"] == "origin"
    assert payload["plan"]["retrieval_mode"] == "broad"
    assert "timeline" in payload["plan"]["requested_outputs"]
    assert payload["investigation_id"].startswith("inv_")


def test_retrieve_endpoint_returns_retrieval_artifact(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    assert plan_response.status_code == 200
    investigation_id = plan_response.json()["investigation_id"]

    expected = RetrievalResult(
        investigation_id=investigation_id,
        plan_snapshot=repo.get_plan(investigation_id),
        retrieved_document_ids=["doc_1", "doc_2"],
        high_relevance_document_ids=["doc_1"],
        main_narrative_document_ids=["doc_1"],
        counter_narrative_candidate_ids=["doc_2"],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="medium",
    )

    class _StubRetrieverAgent:
        def retrieve(self, investigation_id, plan, max_rounds=None, force_refresh=False):
            return expected

    monkeypatch.setattr(narratives_api, "_build_retriever_agent", lambda: _StubRetrieverAgent())

    response = client.post(f"/api/investigations/{investigation_id}/retrieve", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["investigation_id"] == investigation_id
    assert payload["retrieved_document_ids"] == ["doc_1", "doc_2"]
    assert payload["evidence_coverage_confidence"] == "medium"


def test_retrieve_endpoint_404s_for_unknown_investigation(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)
    response = client.post("/api/investigations/inv_missing/retrieve", json={})
    assert response.status_code == 404


def test_retrieve_endpoint_uses_local_corpus_in_demo_mode(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the hidden energy tax narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]

    response = client.post(f"/api/investigations/{investigation_id}/retrieve", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieved_document_ids"]
    assert payload["search_rounds"][0]["provider"] == "local_demo"


def test_get_investigation_workspace_returns_persisted_artifacts(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]
    plan = repo.get_plan(investigation_id)
    assert plan is not None

    repo.save_retrieval_result(_timeline_retrieval(investigation_id, plan), _timeline_docs())
    repo.save_timeline_result(
        TimelineResult(
            investigation_id=investigation_id,
            plan_snapshot=plan,
            timeline_events=[],
            first_observed_doc_id="doc_1",
            timeline_summary="cached timeline",
            limitations=[],
            confidence_score=0.45,
            confidence_label="medium",
        )
    )

    response = client.get(f"/api/investigations/{investigation_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["investigation_id"] == investigation_id
    assert payload["query_text"] == "Where did the 'hidden energy tax' narrative come from?"
    assert payload["plan"]["query_text"] == "Where did the 'hidden energy tax' narrative come from?"
    assert payload["retrieval"]["retrieved_document_ids"] == ["doc_1", "doc_2"]
    assert len(payload["retrieved_documents"]) == 2
    assert payload["timeline"]["timeline_summary"] == "cached timeline"


def test_get_investigation_workspace_404s_when_missing(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    response = client.get("/api/investigations/inv_missing")
    assert response.status_code == 404


def test_timeline_endpoint_builds_artifact_from_persisted_state(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    assert plan_response.status_code == 200
    investigation_id = plan_response.json()["investigation_id"]
    plan = repo.get_plan(investigation_id)
    assert plan is not None

    repo.save_retrieval_result(_timeline_retrieval(investigation_id, plan), _timeline_docs())

    response = client.post(f"/api/investigations/{investigation_id}/timeline", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["first_observed_doc_id"] == "doc_1"
    assert payload["confidence_label"] in {"low", "medium", "high"}
    assert len(payload["timeline_events"]) == 2


def test_timeline_endpoint_404s_for_unknown_investigation(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)
    response = client.post("/api/investigations/inv_missing/timeline", json={})
    assert response.status_code == 404


def test_timeline_endpoint_404s_without_retrieval_result(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]

    response = client.post(f"/api/investigations/{investigation_id}/timeline", json={})
    assert response.status_code == 404


def test_timeline_endpoint_force_refresh_recomputes(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]
    plan = repo.get_plan(investigation_id)
    assert plan is not None
    retrieval = _timeline_retrieval(investigation_id, plan)
    docs = _timeline_docs()
    repo.save_retrieval_result(retrieval, docs)

    cached = TimelineResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        timeline_events=[],
        first_observed_doc_id=None,
        timeline_summary="cached timeline",
        limitations=[],
        confidence_score=0.15,
        confidence_label="low",
    )
    repo.save_timeline_result(cached)

    calls = {"count": 0}

    def _stub_build_timeline(inv_id, plan_arg, retrieval_arg, docs_arg):
        calls["count"] += 1
        return TimelineResult(
            investigation_id=inv_id,
            plan_snapshot=plan_arg,
            timeline_events=[],
            first_observed_doc_id="doc_1",
            timeline_summary="fresh timeline",
            limitations=[],
            confidence_score=0.55,
            confidence_label="medium",
        )

    monkeypatch.setattr(narratives_api, "build_timeline_artifact", _stub_build_timeline)

    response = client.post(
        f"/api/investigations/{investigation_id}/timeline",
        json={"force_refresh": True},
    )
    assert response.status_code == 200
    assert response.json()["timeline_summary"] == "fresh timeline"
    assert calls["count"] == 1


def test_timeline_endpoint_returns_cached_artifact_when_available(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]
    plan = repo.get_plan(investigation_id)
    assert plan is not None
    repo.save_retrieval_result(_timeline_retrieval(investigation_id, plan), _timeline_docs())
    repo.save_timeline_result(
        TimelineResult(
            investigation_id=investigation_id,
            plan_snapshot=plan,
            timeline_events=[],
            first_observed_doc_id="doc_1",
            timeline_summary="cached timeline",
            limitations=[],
            confidence_score=0.45,
            confidence_label="medium",
        )
    )

    def _unexpected_build(*args, **kwargs):
        raise AssertionError("timeline builder should not run when cache is available")

    monkeypatch.setattr(narratives_api, "build_timeline_artifact", _unexpected_build)

    response = client.post(f"/api/investigations/{investigation_id}/timeline", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["timeline_summary"] == "cached timeline"
    assert payload["cached"] is True


def test_counter_narratives_endpoint_builds_artifact_from_persisted_state(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    assert plan_response.status_code == 200
    investigation_id = plan_response.json()["investigation_id"]
    plan = repo.get_plan(investigation_id)
    assert plan is not None

    retrieval = _timeline_retrieval(investigation_id, plan).model_copy(
        update={"counter_narrative_candidate_ids": ["doc_2"]}
    )
    repo.save_retrieval_result(retrieval, _timeline_docs())

    response = client.post(f"/api/investigations/{investigation_id}/counter-narratives", json={})
    assert response.status_code == 200
    payload = response.json()
    assert "counter_narratives" in payload
    assert payload["investigation_id"] == investigation_id


def test_counter_narratives_endpoint_404s_without_retrieval_result(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]

    response = client.post(f"/api/investigations/{investigation_id}/counter-narratives", json={})
    assert response.status_code == 404


def test_analyst_endpoint_builds_artifact_from_persisted_state(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    assert plan_response.status_code == 200
    investigation_id = plan_response.json()["investigation_id"]
    plan = repo.get_plan(investigation_id)
    assert plan is not None

    retrieval = _timeline_retrieval(investigation_id, plan).model_copy(
        update={
            "counter_narrative_candidate_ids": ["doc_2"],
            "main_narrative_document_ids": ["doc_1"],
        }
    )
    repo.save_retrieval_result(retrieval, _timeline_docs())

    response = client.post(f"/api/investigations/{investigation_id}/analyst", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["investigation_id"] == investigation_id
    assert "draft_report_sections" in payload
    assert len(payload["candidate_claims"]) > 0


def test_analyst_endpoint_404s_without_retrieval_result(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]

    response = client.post(f"/api/investigations/{investigation_id}/analyst", json={})
    assert response.status_code == 404


def test_final_report_endpoint_builds_artifact_from_persisted_state(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    assert plan_response.status_code == 200
    investigation_id = plan_response.json()["investigation_id"]
    plan = repo.get_plan(investigation_id)
    assert plan is not None

    retrieval = _timeline_retrieval(investigation_id, plan).model_copy(
        update={
            "counter_narrative_candidate_ids": ["doc_2"],
            "main_narrative_document_ids": ["doc_1"],
        }
    )
    repo.save_retrieval_result(retrieval, _timeline_docs())

    response = client.post(f"/api/investigations/{investigation_id}/report", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["investigation_id"] == investigation_id
    assert payload["report_title"]
    assert payload["key_claims"]
    assert payload["evidence_packet"]


def test_final_report_endpoint_404s_without_retrieval_result(tmp_path, monkeypatch):
    repo = InvestigationRepository(str(tmp_path / "investigations.sqlite3"))
    monkeypatch.setattr(narratives_api, "_investigation_repo", repo)

    plan_response = client.post(
        "/api/investigate",
        json={"query_text": "Where did the 'hidden energy tax' narrative come from?"},
    )
    investigation_id = plan_response.json()["investigation_id"]

    response = client.post(f"/api/investigations/{investigation_id}/report", json={})
    assert response.status_code == 404


def test_investigate_missing_query_text():
    r = client.post("/api/investigate", json={"narrative_id": "narrative_001"})
    assert r.status_code == 422


def test_investigate_rejects_extra_fields():
    r = client.post(
        "/api/investigate",
        json={"query_text": "Trace the TikTok ban story.", "narrative_id": "narrative_001"},
    )
    assert r.status_code == 422


def test_get_graph_energy():
    r = client.get("/api/graph/narrative_001")
    assert r.status_code == 200
    graph = r.json()
    assert graph["narrative_id"] == "narrative_001"
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0


def test_get_receipts():
    r = client.get("/api/receipts/narrative_001")
    assert r.status_code == 200
    receipts = r.json()
    assert isinstance(receipts, list)
    statuses = {rec["verification_status"] for rec in receipts}
    # Should have at least one verified receipt
    assert "verified" in statuses


def test_get_mutations():
    r = client.get("/api/mutations/narrative_001")
    assert r.status_code == 200
    mutations = r.json()
    assert isinstance(mutations, list)
    assert len(mutations) == 4  # demo mode returns pre-built trail


def test_gdelt_search_returns_normalized_documents_timeline_and_first_observed(monkeypatch):
    live_store.clear()

    fake_documents = [
        {
            "id": "gdelt_a",
            "source_id": "domain:springfieldgazette.com",
            "source_name": "springfieldgazette.com",
            "source_type": "local_news",
            "url": "https://springfieldgazette.com/a",
            "title": "Earlier local story",
            "published_at": "2026-06-03T08:00:00Z",
            "collected_at": "2026-06-19T00:00:00Z",
            "text": "Earlier local story",
            "snippet": "Earlier local story",
            "language": "english",
            "content_type": "article",
            "geographic_scope": "local",
            "entities": [],
            "phrases": ["tiktok ban"],
            "claims": None,
            "embedding": None,
            "duplicate_of_doc_id": None,
            "is_seeded_demo_data": None,
            "metadata": {"dataset": "gdelt_doc_2"},
        },
        {
            "id": "gdelt_b",
            "source_id": "domain:reuters.com",
            "source_name": "reuters.com",
            "source_type": "national_news",
            "url": "https://reuters.com/b",
            "title": "Later national story",
            "published_at": "2026-06-04T10:00:00Z",
            "collected_at": "2026-06-19T00:00:00Z",
            "text": "Later national story",
            "snippet": "Later national story",
            "language": "english",
            "content_type": "article",
            "geographic_scope": "national",
            "entities": [],
            "phrases": ["tiktok ban"],
            "claims": None,
            "embedding": None,
            "duplicate_of_doc_id": None,
            "is_seeded_demo_data": None,
            "metadata": {"dataset": "gdelt_doc_2"},
        },
    ]

    from models.document import Document

    monkeypatch.setattr(
        "api.ingest._gdelt.fetch_articles",
        lambda query, start_dt, end_dt, max_records: [Document(**doc) for doc in fake_documents],
    )

    r = client.get(
        "/api/gdelt/search",
        params={
            "query": "tiktok ban",
            "start_date": "2026-06-01",
            "end_date": "2026-06-19",
            "max_records": 25,
            "store": "true",
        },
    )

    assert r.status_code == 200
    payload = r.json()
    assert payload["query"] == "tiktok ban"
    assert len(payload["documents"]) == 2
    assert payload["timeline"] == [
        {"date": "2026-06-03", "count": 1},
        {"date": "2026-06-04", "count": 1},
    ]
    assert payload["first_observed_in_dataset"]["label"] == "first observed in our dataset"
    assert payload["first_observed_in_dataset"]["title"] == "Earlier local story"
    assert live_store.count() == 2
