from fastapi import APIRouter, HTTPException
from uuid import uuid4

from agents.planner_agent import plan_investigation
from agents.retriever_agent import RetrieverAgent
from config import get_settings
from demo_data import ALL_DOCUMENTS, DEMO_GRAPHS, DEMO_NARRATIVES
from models.graph import NarrativeGraph
from models.investigation import (
    AnalystRequest,
    AnalystResult,
    CounterNarrativeRequest,
    CounterNarrativeResult,
    FinalReportRequest,
    FinalReportResult,
    InvestigationWorkspace,
    PlannerRequest,
    PlannerResponse,
    RetrieveRequest,
    RetrievalResult,
    TimelineRequest,
    TimelineResult,
)
from services.analyst_builder import build_analyst_result as build_analyst_result_artifact
from models.narrative import NarrativeCluster
from services.counter_narrative_builder import (
    build_counter_narratives as build_counter_narratives_artifact,
)
from services.final_report_builder import build_final_report as build_final_report_artifact
from services.graph_builder import GraphBuilder
from services.ingestion import get_merged_documents
from services.investigation_repository import InvestigationRepository
from services.mutation_detection import MutationDetector
from services.retrieval import Retriever
from services.spike_detection import SpikeDetector
from services.timeline_builder import build_timeline as build_timeline_artifact
from services.verification import VerificationService


def _active_documents():
    """Returns live store + demo corpus merged. Falls back to demo when store is empty."""
    return get_merged_documents(ALL_DOCUMENTS)


router = APIRouter(prefix="/api")

_retriever = Retriever()
_spike_detector = SpikeDetector()
_mutation_detector = MutationDetector()
_graph_builder = GraphBuilder()
_verifier = VerificationService()
_investigation_repo = InvestigationRepository(get_settings().INVESTIGATION_DB_PATH)


def _build_retriever_agent() -> RetrieverAgent:
    return RetrieverAgent(repository=_investigation_repo)


# ---------------------------------------------------------------------------
# GET /api/narratives - list spiking narratives
# ---------------------------------------------------------------------------

@router.get("/narratives", response_model=list[NarrativeCluster])
def list_narratives() -> list[NarrativeCluster]:
    return _spike_detector.get_spiking_narratives(DEMO_NARRATIVES, _active_documents())


# ---------------------------------------------------------------------------
# GET /api/narratives/{id} - get single narrative cluster
# ---------------------------------------------------------------------------

@router.get("/narratives/{narrative_id}", response_model=NarrativeCluster)
def get_narrative(narrative_id: str) -> NarrativeCluster:
    cluster = next((n for n in DEMO_NARRATIVES if n.id == narrative_id), None)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Narrative '{narrative_id}' not found.")
    return cluster


# ---------------------------------------------------------------------------
# GET /api/narratives/{id}/timeline - phrase spike timeline for chart
# ---------------------------------------------------------------------------

@router.get("/narratives/{narrative_id}/timeline")
def get_narrative_timeline(narrative_id: str) -> list[dict]:
    cluster = next((n for n in DEMO_NARRATIVES if n.id == narrative_id), None)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Narrative '{narrative_id}' not found.")
    docs = _retriever.get_related_documents(cluster, _active_documents())
    phrase = cluster.canonical_phrases[0]
    return _spike_detector.compute_phrase_timeline(phrase, docs)


# ---------------------------------------------------------------------------
# GET /api/investigations/{id} - fetch persisted investigation workspace state
# ---------------------------------------------------------------------------

@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationWorkspace,
)
def get_investigation_workspace(investigation_id: str) -> InvestigationWorkspace:
    workspace = _investigation_repo.get_investigation_workspace(investigation_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")
    return workspace


# ---------------------------------------------------------------------------
# POST /api/investigate - create an investigation plan from free-text query
# ---------------------------------------------------------------------------

@router.post("/investigate", response_model=PlannerResponse)
def investigate(request: PlannerRequest) -> PlannerResponse:
    plan = plan_investigation(request.query_text, request.prior_context)
    investigation_id = f"inv_{uuid4().hex}"
    warnings: list[str] = []

    if get_settings().DEMO_MODE:
        warnings.append(
            "Planner ran in deterministic local mode. Retrieval runs as a separate investigation step."
        )

    _investigation_repo.save_plan(investigation_id, request.query_text, plan)
    return PlannerResponse(
        investigation_id=investigation_id,
        query_text=request.query_text,
        plan=plan,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/retrieve - run retriever agent on persisted plan
# ---------------------------------------------------------------------------

@router.post("/investigations/{investigation_id}/retrieve", response_model=RetrievalResult)
def retrieve(investigation_id: str, request: RetrieveRequest) -> RetrievalResult:
    if not _investigation_repo.investigation_exists(investigation_id):
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    plan = _investigation_repo.get_plan(investigation_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Investigation plan for '{investigation_id}' not found.")

    agent = _build_retriever_agent()
    try:
        return agent.retrieve(
            investigation_id=investigation_id,
            plan=plan,
            max_rounds=request.max_rounds,
            force_refresh=request.force_refresh,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Retriever failed: {exc}") from exc


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/timeline - build deterministic timeline artifact
# ---------------------------------------------------------------------------

@router.post("/investigations/{investigation_id}/timeline", response_model=TimelineResult)
def timeline(investigation_id: str, request: TimelineRequest) -> TimelineResult:
    if not _investigation_repo.investigation_exists(investigation_id):
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    plan = _investigation_repo.get_plan(investigation_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Investigation plan for '{investigation_id}' not found.")

    retrieval = _investigation_repo.get_retrieval_result(investigation_id)
    if retrieval is None:
        raise HTTPException(status_code=404, detail=f"Retrieval result for '{investigation_id}' not found.")

    documents = _investigation_repo.get_retrieved_documents(investigation_id)

    if not request.force_refresh:
        cached = _investigation_repo.get_timeline_result(investigation_id)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

    try:
        result = build_timeline_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_timeline_result(result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Timeline build failed: {exc}") from exc


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/counter-narratives - build counter-frame artifact
# ---------------------------------------------------------------------------

@router.post(
    "/investigations/{investigation_id}/counter-narratives",
    response_model=CounterNarrativeResult,
)
def counter_narratives(
    investigation_id: str,
    request: CounterNarrativeRequest,
) -> CounterNarrativeResult:
    if not _investigation_repo.investigation_exists(investigation_id):
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    plan = _investigation_repo.get_plan(investigation_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Investigation plan for '{investigation_id}' not found.")

    retrieval = _investigation_repo.get_retrieval_result(investigation_id)
    if retrieval is None:
        raise HTTPException(status_code=404, detail=f"Retrieval result for '{investigation_id}' not found.")

    documents = _investigation_repo.get_retrieved_documents(investigation_id)

    if not request.force_refresh:
        cached = _investigation_repo.get_counter_narrative_result(investigation_id)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

    try:
        result = build_counter_narratives_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_counter_narrative_result(result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Counter-narrative build failed: {exc}") from exc


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/analyst - build synthesis artifact
# ---------------------------------------------------------------------------

@router.post(
    "/investigations/{investigation_id}/analyst",
    response_model=AnalystResult,
)
def analyst(
    investigation_id: str,
    request: AnalystRequest,
) -> AnalystResult:
    if not _investigation_repo.investigation_exists(investigation_id):
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    plan = _investigation_repo.get_plan(investigation_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Investigation plan for '{investigation_id}' not found.")

    retrieval = _investigation_repo.get_retrieval_result(investigation_id)
    if retrieval is None:
        raise HTTPException(status_code=404, detail=f"Retrieval result for '{investigation_id}' not found.")

    documents = _investigation_repo.get_retrieved_documents(investigation_id)

    if not request.force_refresh:
        cached = _investigation_repo.get_analyst_result(investigation_id)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

    timeline_result = _investigation_repo.get_timeline_result(investigation_id)
    if timeline_result is None:
        timeline_result = build_timeline_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_timeline_result(timeline_result)

    counter_result = _investigation_repo.get_counter_narrative_result(investigation_id)
    if counter_result is None:
        counter_result = build_counter_narratives_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_counter_narrative_result(counter_result)

    try:
        result = build_analyst_result_artifact(
            investigation_id,
            plan,
            retrieval,
            documents,
            timeline_result,
            counter_result,
        )
        _investigation_repo.save_analyst_result(result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analyst build failed: {exc}") from exc


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/report - assemble final investigation report
# ---------------------------------------------------------------------------

@router.post(
    "/investigations/{investigation_id}/report",
    response_model=FinalReportResult,
)
def final_report(
    investigation_id: str,
    request: FinalReportRequest,
) -> FinalReportResult:
    if not _investigation_repo.investigation_exists(investigation_id):
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    plan = _investigation_repo.get_plan(investigation_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Investigation plan for '{investigation_id}' not found.")

    retrieval = _investigation_repo.get_retrieval_result(investigation_id)
    if retrieval is None:
        raise HTTPException(status_code=404, detail=f"Retrieval result for '{investigation_id}' not found.")

    documents = _investigation_repo.get_retrieved_documents(investigation_id)

    if not request.force_refresh:
        cached = _investigation_repo.get_final_report_result(investigation_id)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

    timeline_result = _investigation_repo.get_timeline_result(investigation_id)
    if timeline_result is None:
        timeline_result = build_timeline_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_timeline_result(timeline_result)

    counter_result = _investigation_repo.get_counter_narrative_result(investigation_id)
    if counter_result is None:
        counter_result = build_counter_narratives_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_counter_narrative_result(counter_result)

    analyst_result = _investigation_repo.get_analyst_result(investigation_id)
    if analyst_result is None:
        analyst_result = build_analyst_result_artifact(
            investigation_id,
            plan,
            retrieval,
            documents,
            timeline_result,
            counter_result,
        )
        _investigation_repo.save_analyst_result(analyst_result)

    try:
        result = build_final_report_artifact(
            investigation_id,
            plan,
            retrieval,
            documents,
            timeline_result,
            counter_result,
            analyst_result,
        )
        _investigation_repo.save_final_report_result(result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Final report assembly failed: {exc}") from exc


# ---------------------------------------------------------------------------
# GET /api/graph/{narrative_id} - narrative spread graph
# ---------------------------------------------------------------------------

@router.get("/graph/{narrative_id}", response_model=NarrativeGraph)
def get_graph(narrative_id: str) -> NarrativeGraph:
    settings = get_settings()

    if settings.DEMO_MODE and narrative_id in DEMO_GRAPHS:
        return DEMO_GRAPHS[narrative_id]

    cluster = next((n for n in DEMO_NARRATIVES if n.id == narrative_id), None)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Narrative '{narrative_id}' not found.")

    docs = _retriever.get_related_documents(cluster, _active_documents())
    mutations = _mutation_detector.detect_mutations(docs)
    return _graph_builder.build_graph(docs, mutations, cluster)


# ---------------------------------------------------------------------------
# GET /api/receipts/{narrative_id} - verification receipts for evidence
# ---------------------------------------------------------------------------

@router.get("/receipts/{narrative_id}")
def get_receipts(narrative_id: str) -> list[dict]:
    cluster = next((n for n in DEMO_NARRATIVES if n.id == narrative_id), None)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Narrative '{narrative_id}' not found.")

    top_doc_ids = cluster.document_ids[:6]
    return _verifier.verify_batch(top_doc_ids, _active_documents())


# ---------------------------------------------------------------------------
# GET /api/mutations/{narrative_id} - mutation trail
# ---------------------------------------------------------------------------

@router.get("/mutations/{narrative_id}")
def get_mutations(narrative_id: str) -> list[dict]:
    cluster = next((n for n in DEMO_NARRATIVES if n.id == narrative_id), None)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Narrative '{narrative_id}' not found.")

    if get_settings().DEMO_MODE:
        return [m.model_dump(mode="json") for m in cluster.mutation_trail]

    docs = _retriever.get_related_documents(cluster, _active_documents())
    return _mutation_detector.detect_mutations(docs)
