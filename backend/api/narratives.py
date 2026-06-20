from fastapi import APIRouter, HTTPException
from uuid import uuid4

from agents.claim_counterpoint_agent import build_claim_counterpoints
from agents.planner_agent import plan_investigation
from agents.retriever_agent import RetrieverAgent
from config import get_settings
from demo_data import ALL_DOCUMENTS, DEMO_GRAPHS, DEMO_NARRATIVES
from models.graph import NarrativeGraph
from models.investigation import (
    AnalystRequest,
    AnalystResult,
    ClaimCounterpointRequest,
    ClaimCounterpointResult,
    CounterNarrativeRequest,
    CounterNarrativeResult,
    FinalReportRequest,
    FinalReportResult,
    InvestigationWorkspace,
    PlannerRequest,
    PlannerResponse,
    ReceiptsRequest,
    ReceiptsResult,
    RetrieveRequest,
    RetrievalResult,
    SourceDiversityRequest,
    SourceDiversityResult,
    TimelineRequest,
    TimelineResult,
)
from services.analyst_builder import build_analyst_result as build_analyst_result_artifact
from models.narrative import NarrativeCluster
from services.counter_narrative_builder import (
    build_counter_narratives as build_counter_narratives_artifact,
)
from services.final_report_builder import (
    apply_receipts_annotations,
    build_final_report as build_final_report_artifact,
)
from services.graph_builder import GraphBuilder
from services.ingestion import get_merged_documents
from services.investigation_cache import get_investigation_cache
from services.investigation_repository import InvestigationRepository
from services.mutation_detection import MutationDetector
from services.receipts_builder import build_receipts as build_receipts_artifact
from services.retrieval import Retriever
from services.source_diversity_builder import build_source_diversity as build_source_diversity_artifact
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
_investigation_cache = get_investigation_cache()


def _build_retriever_agent() -> RetrieverAgent:
    return RetrieverAgent(repository=_investigation_repo)


def _ensure_counter_narrative_result(
    investigation_id: str,
    plan,
    retrieval,
    documents,
) -> CounterNarrativeResult:
    counter_result = _investigation_repo.get_counter_narrative_result(investigation_id)
    if counter_result is None:
        counter_result = build_counter_narratives_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_counter_narrative_result(counter_result)
    return counter_result


def _ensure_timeline_result(
    investigation_id: str,
    plan,
    retrieval,
    documents,
) -> TimelineResult:
    timeline_result = _investigation_repo.get_timeline_result(investigation_id)
    if timeline_result is None:
        timeline_result = build_timeline_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_timeline_result(timeline_result)
    return timeline_result


def _ensure_analyst_result(
    investigation_id: str,
    plan,
    retrieval,
    documents,
) -> AnalystResult:
    analyst_result = _investigation_repo.get_analyst_result(investigation_id)
    if analyst_result is not None:
        return analyst_result

    timeline_result = _ensure_timeline_result(investigation_id, plan, retrieval, documents)
    counter_result = _ensure_counter_narrative_result(investigation_id, plan, retrieval, documents)
    analyst_result = build_analyst_result_artifact(
        investigation_id,
        plan,
        retrieval,
        documents,
        timeline_result,
        counter_result,
    )
    _investigation_repo.save_analyst_result(analyst_result)
    return analyst_result


def _ensure_claim_counterpoint_result(
    investigation_id: str,
    plan,
    retrieval,
    documents,
) -> ClaimCounterpointResult:
    claim_counterpoint_result = _investigation_repo.get_claim_counterpoint_result(investigation_id)
    if claim_counterpoint_result is not None:
        return claim_counterpoint_result

    counter_result = _ensure_counter_narrative_result(investigation_id, plan, retrieval, documents)
    analyst_result = _ensure_analyst_result(investigation_id, plan, retrieval, documents)
    claim_counterpoint_result = build_claim_counterpoints(
        investigation_id,
        plan,
        retrieval,
        documents,
        counter_result,
        analyst_result,
    )
    _investigation_repo.save_claim_counterpoint_result(claim_counterpoint_result)
    return claim_counterpoint_result


def _build_base_report_result(
    investigation_id: str,
    plan,
    retrieval,
    documents,
) -> FinalReportResult:
    timeline_result = _ensure_timeline_result(investigation_id, plan, retrieval, documents)
    counter_result = _ensure_counter_narrative_result(investigation_id, plan, retrieval, documents)
    analyst_result = _ensure_analyst_result(investigation_id, plan, retrieval, documents)
    claim_counterpoint_result = _ensure_claim_counterpoint_result(
        investigation_id,
        plan,
        retrieval,
        documents,
    )
    return build_final_report_artifact(
        investigation_id,
        plan,
        retrieval,
        documents,
        timeline_result,
        counter_result,
        analyst_result,
        claim_counterpoint_result,
    )


def _collect_verification_map(documents, report, claim_counterpoint_result) -> dict[str, str]:
    doc_ids: list[str] = []
    for claim in report.key_claims:
        for citation in [*claim.citations, *claim.counter_citations]:
            doc_ids.append(citation.document_id)
    if claim_counterpoint_result is not None:
        for pair in claim_counterpoint_result.pairs:
            for citation in [*pair.main_receipts, *pair.counter_receipts]:
                doc_ids.append(citation.document_id)

    unique_doc_ids = list(dict.fromkeys(doc_ids))
    results = _verifier.verify_batch(unique_doc_ids, documents)
    verification_map = {
        item["doc_id"]: item.get("verification_status", "pending")
        for item in results
        if item.get("doc_id")
    }
    for doc_id in unique_doc_ids:
        verification_map.setdefault(doc_id, "pending")
    return verification_map


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
    if _investigation_cache:
        cached = _investigation_cache.get_workspace(investigation_id)
        if cached is not None:
            return cached

    workspace = _investigation_repo.get_investigation_workspace(investigation_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    if _investigation_cache:
        _investigation_cache.cache_workspace(workspace)

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
        result = agent.retrieve(
            investigation_id=investigation_id,
            plan=plan,
            max_rounds=request.max_rounds,
            force_refresh=request.force_refresh,
        )
        if _investigation_cache:
            _investigation_cache.invalidate(investigation_id)
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Retriever failed: {exc}") from exc


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/source-diversity - build deterministic source diversity artifact
# ---------------------------------------------------------------------------

@router.post(
    "/investigations/{investigation_id}/source-diversity",
    response_model=SourceDiversityResult,
)
def source_diversity(
    investigation_id: str,
    request: SourceDiversityRequest,
) -> SourceDiversityResult:
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
        cached = _investigation_repo.get_source_diversity_result(investigation_id)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

    try:
        result = build_source_diversity_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_source_diversity_result(result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Source diversity build failed: {exc}") from exc


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
        if _investigation_cache:
            _investigation_cache.invalidate(investigation_id)
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
        if _investigation_cache:
            _investigation_cache.invalidate(investigation_id)
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

    source_diversity_result = _investigation_repo.get_source_diversity_result(investigation_id)
    if source_diversity_result is None:
        source_diversity_result = build_source_diversity_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_source_diversity_result(source_diversity_result)

    timeline_result = _investigation_repo.get_timeline_result(investigation_id)
    if timeline_result is None:
        timeline_result = build_timeline_artifact(investigation_id, plan, retrieval, documents)
        _investigation_repo.save_timeline_result(timeline_result)

    counter_result = _investigation_repo.get_counter_narrative_result(investigation_id)
    if counter_result is None:
        counter_result = _ensure_counter_narrative_result(investigation_id, plan, retrieval, documents)

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
        if _investigation_cache:
            _investigation_cache.invalidate(investigation_id)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analyst build failed: {exc}") from exc


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/claim-counterpoints - build claim-level counterpoint artifact
# ---------------------------------------------------------------------------

@router.post(
    "/investigations/{investigation_id}/claim-counterpoints",
    response_model=ClaimCounterpointResult,
)
def claim_counterpoints(
    investigation_id: str,
    request: ClaimCounterpointRequest,
) -> ClaimCounterpointResult:
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
        cached = _investigation_repo.get_claim_counterpoint_result(investigation_id)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

    try:
        result = _ensure_claim_counterpoint_result(
            investigation_id,
            plan,
            retrieval,
            documents,
        )
        if request.force_refresh:
            counter_result = _ensure_counter_narrative_result(investigation_id, plan, retrieval, documents)
            analyst_result = _ensure_analyst_result(investigation_id, plan, retrieval, documents)
            result = build_claim_counterpoints(
                investigation_id,
                plan,
                retrieval,
                documents,
                counter_result,
                analyst_result,
            )
            _investigation_repo.save_claim_counterpoint_result(result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claim counterpoint build failed: {exc}") from exc


# ---------------------------------------------------------------------------
# POST /api/investigations/{id}/receipts - build grounding artifact for claims and counter-claims
# ---------------------------------------------------------------------------

@router.post(
    "/investigations/{investigation_id}/receipts",
    response_model=ReceiptsResult,
)
def receipts(
    investigation_id: str,
    request: ReceiptsRequest,
) -> ReceiptsResult:
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
        cached = _investigation_repo.get_receipts_result(investigation_id)
        if cached is not None:
            return cached.model_copy(update={"cached": True})

    claim_counterpoint_result = _ensure_claim_counterpoint_result(
        investigation_id,
        plan,
        retrieval,
        documents,
    )

    try:
        base_report = _build_base_report_result(
            investigation_id,
            plan,
            retrieval,
            documents,
        )
        # Persist the base report first so receipts can be attached to workspace state.
        _investigation_repo.save_final_report_result(base_report)
        verification_map = _collect_verification_map(documents, base_report, claim_counterpoint_result)
        result = build_receipts_artifact(
            investigation_id,
            plan,
            documents,
            base_report,
            claim_counterpoint_result,
            verification_map,
        )
        _investigation_repo.save_receipts_result(result)
        annotated_report = apply_receipts_annotations(base_report, result)
        _investigation_repo.save_final_report_result(annotated_report, update_stage=False)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Receipts build failed: {exc}") from exc


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

    try:
        cached_report = None if request.force_refresh else _investigation_repo.get_final_report_result(investigation_id)
        cached_receipts = None if request.force_refresh else _investigation_repo.get_receipts_result(investigation_id)
        if cached_report is not None and cached_receipts is not None:
            return cached_report.model_copy(update={"cached": True})

        source_diversity_result = _investigation_repo.get_source_diversity_result(investigation_id)
        if source_diversity_result is None:
            source_diversity_result = build_source_diversity_artifact(investigation_id, plan, retrieval, documents)
            _investigation_repo.save_source_diversity_result(source_diversity_result)

        claim_counterpoint_result = _ensure_claim_counterpoint_result(
            investigation_id,
            plan,
            retrieval,
            documents,
        )
        base_report = cached_report or _build_base_report_result(
            investigation_id,
            plan,
            retrieval,
            documents,
        )

        receipts_result = cached_receipts
        if request.force_refresh or receipts_result is None:
            verification_map = _collect_verification_map(documents, base_report, claim_counterpoint_result)
            receipts_result = build_receipts_artifact(
                investigation_id,
                plan,
                documents,
                base_report,
                claim_counterpoint_result,
                verification_map,
            )
            _investigation_repo.save_receipts_result(receipts_result)

        result = apply_receipts_annotations(base_report, receipts_result)
        _investigation_repo.save_final_report_result(result)
        if _investigation_cache:
            _investigation_cache.invalidate(investigation_id)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Final report assembly failed: {exc}") from exc


# ---------------------------------------------------------------------------
# GET /api/cache/stats - Redis cache statistics (sponsor evidence)
# ---------------------------------------------------------------------------

@router.get("/cache/stats")
def cache_stats() -> dict:
    if _investigation_cache is None:
        return {"redis_cache": "disabled", "reason": "Redis unavailable or cache disabled"}
    stats = _investigation_cache.get_stats()
    stats["redis_cache"] = "enabled"
    stats["cached_investigations"] = _investigation_cache.list_cached_investigations(limit=20)
    return stats


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
# POST /api/investigations/{id}/verify - run Browserbase verification on top docs
# ---------------------------------------------------------------------------

@router.post("/investigations/{investigation_id}/verify")
def verify_investigation_sources(investigation_id: str, max_docs: int = 6) -> list[dict]:
    from agents.browserbase_agent import get_browserbase_agent

    if not _investigation_repo.investigation_exists(investigation_id):
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")

    documents = _investigation_repo.get_retrieved_documents(investigation_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No retrieved documents for this investigation.")

    agent = get_browserbase_agent()
    receipts = agent.verify_documents(documents[:max_docs])
    return [r.to_dict() for r in receipts]


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
