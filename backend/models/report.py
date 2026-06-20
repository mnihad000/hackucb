from datetime import datetime
from typing import Literal
from pydantic import BaseModel

from .narrative import MutationEntry


class EvidenceItem(BaseModel):
    doc_id: str
    source: str
    source_type: str
    timestamp: datetime
    excerpt: str
    reason: str
    verified: bool = False
    verification_status: Literal[
        "verified", "unavailable", "metadata_mismatch", "pending"
    ] = "pending"


class ArizeEval(BaseModel):
    grounding_score_before: float
    grounding_score_after: float
    overclaim_risk_before: Literal["low", "medium", "high"]
    overclaim_risk_after: Literal["low", "medium", "high"]
    uncertainty_present: bool
    revised_by_skeptic: bool


class InvestigationReport(BaseModel):
    id: str
    cluster_id: str
    generated_at: datetime
    narrative_title: str
    summary: str
    spread_pattern: Literal[
        "grassroots",
        "reactive_amplification",
        "top_down",
        "coordination_signals_present",
        "insufficient_evidence",
    ]
    first_observed: dict
    mutation_trail: list[MutationEntry]
    coordination_signals: list[str]
    counter_signals: list[str]
    evidence: list[EvidenceItem]
    confidence: float
    limitations: list[str]
    recommended_human_checks: list[str]
    arize_eval: ArizeEval
    cached: bool = False
