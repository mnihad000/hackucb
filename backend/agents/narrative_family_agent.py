from __future__ import annotations

import json
import logging

from pydantic import BaseModel, Field, ValidationError

from agents.json_utils import validate_no_forbidden_language
from agents.model_client import BaseModelClient, MockModelClient, build_model_client
from agents.prompt_loader import load_prompt
from config import get_settings
from models.document import Document
from models.investigation import (
    CounterNarrativeResult,
    InvestigationPlan,
    NarrativeFamilyResult,
    RetrievalResult,
    TimelineResult,
)
from services.narrative_family_builder import (
    build_narrative_family as build_narrative_family_fallback,
    refresh_narrative_family_result,
)

logger = logging.getLogger(__name__)

_REPAIR_SYSTEM = (
    "You are a JSON repair assistant. The previous response did not match the required schema. "
    "Return ONLY a valid JSON object with no markdown, no explanation, and no preamble. "
    "Use only branch ids and evidence already present in the provided candidate packet."
)


class _BranchAnnotation(BaseModel):
    branch_id: str
    title: str | None = None
    relationship_to_parent: str | None = None
    branch_summary: str | None = None


class _NarrativeFamilyAgentResponse(BaseModel):
    family_title: str | None = None
    parent_frame: str | None = None
    summary: str | None = None
    active_branch_id: str | None = None
    selected_branch_ids: list[str] = Field(default_factory=list)
    branch_annotations: list[_BranchAnnotation] = Field(default_factory=list)
    mutation_summary: str | None = None
    limitations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


def build_narrative_family(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
    timeline: TimelineResult,
    counter_narratives: CounterNarrativeResult,
    model_client: BaseModelClient | None = None,
) -> NarrativeFamilyResult:
    baseline = build_narrative_family_fallback(
        investigation_id,
        plan,
        retrieval,
        documents,
        timeline,
        counter_narratives,
    )

    if model_client is None:
        settings = get_settings()
        if settings.DEMO_MODE:
            return baseline
        model_client = build_model_client("gemini")

    if isinstance(model_client, MockModelClient):
        return _with_limitation(
            baseline,
            "Hybrid narrative family agent was unavailable, so deterministic family grouping was used.",
        )

    system_prompt = load_prompt("narrative_family")
    user_prompt = _build_user_prompt(plan, documents, baseline)

    try:
        response = _call_with_retry(model_client, system_prompt, user_prompt)
        merged = _merge_agent_output(baseline, response, documents)
        return merged
    except Exception as exc:
        logger.warning("Narrative family agent failed and fell back to deterministic builder: %s", exc)
        return _with_limitation(
            baseline,
            "Hybrid narrative family agent could not produce a valid output, so deterministic family grouping was used.",
        )


def _build_user_prompt(
    plan: InvestigationPlan,
    documents: list[Document],
    baseline: NarrativeFamilyResult,
) -> str:
    docs_by_id = {document.id: document for document in documents}
    candidate_packet = {
        "plan": {
            "topic": plan.topic,
            "canonical_phrase": plan.canonical_phrase,
            "intent": plan.intent,
            "risk_notes": plan.risk_notes[:3],
            "uncertainty_requirements": plan.uncertainty_requirements[:3],
        },
        "baseline_family": {
            "family_title": baseline.family_title,
            "parent_frame": baseline.parent_frame,
            "summary": baseline.summary,
            "active_branch_id": baseline.active_branch_id,
            "confidence_score": baseline.confidence_score,
        },
        "branch_candidates": [
            {
                "branch_id": branch.id,
                "title": branch.title,
                "branch_type": branch.branch_type,
                "canonical_phrase": branch.canonical_phrase,
                "related_phrases": branch.related_phrases[:4],
                "relationship_to_parent": branch.relationship_to_parent,
                "branch_summary": branch.branch_summary,
                "growth_status": branch.growth_status,
                "growth_score": branch.growth_score,
                "source_diversity_score": branch.source_diversity_score,
                "source_count": branch.source_count,
                "source_type_count": branch.source_type_count,
                "first_observed": _doc_summary(docs_by_id.get(branch.first_observed_doc_id or "")),
                "supporting_examples": [
                    _doc_summary(docs_by_id.get(doc_id))
                    for doc_id in branch.supporting_document_ids[:2]
                    if docs_by_id.get(doc_id) is not None
                ],
            }
            for branch in baseline.child_narratives
        ],
        "mutation_candidates": [
            {
                "from_phrase": step.from_phrase,
                "to_phrase": step.to_phrase,
                "mutation_type": step.mutation_type,
                "similarity_score": step.similarity_score,
                "time_delta_hours": step.time_delta_hours,
                "source_shift": step.source_shift,
                "from_doc": _doc_summary(docs_by_id.get(step.from_doc_id)),
                "to_doc": _doc_summary(docs_by_id.get(step.to_doc_id)),
                "explanation": step.explanation,
            }
            for step in baseline.mutation_trail[:6]
        ],
    }
    return (
        "Use the deterministic family candidates below to produce a tighter semantic grouping. "
        "Do not invent branches, documents, ids, or facts beyond this packet.\n\n"
        + json.dumps(candidate_packet, separators=(",", ":"), ensure_ascii=True)
    )


def _doc_summary(document: Document | None) -> dict | None:
    if document is None:
        return None
    return {
        "doc_id": document.id,
        "source_name": document.source_name,
        "source_type": document.source_type,
        "published_at": document.published_at.isoformat() if document.published_at else None,
        "title": document.title,
        "snippet": (document.snippet or document.text[:180]).strip()[:180],
    }


def _call_with_retry(
    model_client: BaseModelClient,
    system_prompt: str,
    user_prompt: str,
) -> _NarrativeFamilyAgentResponse:
    def _validate(raw: dict) -> _NarrativeFamilyAgentResponse:
        validate_no_forbidden_language(raw)
        return _NarrativeFamilyAgentResponse.model_validate(raw)

    try:
        return _validate(model_client.generate_json(system_prompt, user_prompt, "narrative_family"))
    except (ValidationError, ValueError, RuntimeError, Exception) as exc:
        logger.warning("Narrative family primary attempt failed: %s", exc)

    repair_user = (
        "Your previous response was invalid for the narrative family schema. "
        f"Original context:\n{user_prompt[:3500]}"
    )
    return _validate(model_client.generate_json(_REPAIR_SYSTEM, repair_user, "narrative_family"))


def _merge_agent_output(
    baseline: NarrativeFamilyResult,
    response: _NarrativeFamilyAgentResponse,
    documents: list[Document],
) -> NarrativeFamilyResult:
    branch_by_id = {branch.id: branch for branch in baseline.child_narratives}
    ordered_ids = []
    seen: set[str] = set()
    invalid_ids = []

    for branch_id in response.selected_branch_ids:
        if branch_id in branch_by_id and branch_id not in seen:
            seen.add(branch_id)
            ordered_ids.append(branch_id)
        elif branch_id not in branch_by_id:
            invalid_ids.append(branch_id)

    for branch in baseline.child_narratives:
        if branch.id in seen:
            continue
        ordered_ids.append(branch.id)

    annotations_by_id = {item.branch_id: item for item in response.branch_annotations if item.branch_id in branch_by_id}
    ordered_branches = []
    for branch_id in ordered_ids:
        branch = branch_by_id[branch_id]
        annotation = annotations_by_id.get(branch_id)
        if annotation is None:
            ordered_branches.append(branch)
            continue
        ordered_branches.append(
            branch.model_copy(
                update={
                    "title": annotation.title or branch.title,
                    "relationship_to_parent": annotation.relationship_to_parent or branch.relationship_to_parent,
                    "branch_summary": annotation.branch_summary or branch.branch_summary,
                }
            )
        )

    active_branch_id = response.active_branch_id if response.active_branch_id in branch_by_id else baseline.active_branch_id
    result = baseline.model_copy(
        update={
            "family_title": response.family_title or baseline.family_title,
            "parent_frame": response.parent_frame or baseline.parent_frame,
            "summary": response.summary or baseline.summary,
            "child_narratives": ordered_branches,
            "active_branch_id": active_branch_id,
            "mutation_summary": response.mutation_summary or baseline.mutation_summary,
            "confidence_score": round(min(max(response.confidence_score, 0.0), 0.95), 3),
            "confidence_label": _confidence_label(round(min(max(response.confidence_score, 0.0), 0.95), 3)),
            "generation_method": "hybrid_agent",
            "limitations": _dedupe_strings(
                [
                    *baseline.limitations,
                    *response.limitations,
                    *(
                        ["Agent output referenced unknown branch ids and those references were ignored."]
                        if invalid_ids
                        else []
                    ),
                    *(
                        ["Agent output did not provide a valid active branch id, so the deterministic active branch was preserved."]
                        if response.active_branch_id and response.active_branch_id not in branch_by_id
                        else []
                    ),
                ]
            ),
        }
    )
    refreshed = refresh_narrative_family_result(
        result,
        documents,
        active_branch_id=active_branch_id,
        generation_method="hybrid_agent",
    )
    if response.mutation_summary:
        refreshed = refreshed.model_copy(update={"mutation_summary": response.mutation_summary})
    return refreshed


def _with_limitation(baseline: NarrativeFamilyResult, limitation: str) -> NarrativeFamilyResult:
    return baseline.model_copy(
        update={
            "limitations": _dedupe_strings([*baseline.limitations, limitation]),
            "generation_method": "deterministic",
        }
    )


def _confidence_label(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.46:
        return "medium"
    return "low"


def _dedupe_strings(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output
