from datetime import datetime
from pydantic import BaseModel


class MutationEntry(BaseModel):
    phrase: str
    first_doc_id: str
    timestamp: datetime
    source_type: str


class NarrativeCluster(BaseModel):
    id: str
    label: str
    canonical_phrases: list[str]
    mutation_trail: list[MutationEntry]
    first_observed_doc_id: str
    first_observed_at: datetime
    document_ids: list[str]
    spike_score: float
    confidence: float
    source_type_breakdown: dict[str, int]
