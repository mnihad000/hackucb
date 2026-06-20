from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    source_type: str
    timestamp: datetime
    title: str
    url: str
    phrase_used: str


class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: Literal[
        "phrase_reuse",
        "phrase_mutation",
        "semantic_similarity",
        "entity_overlap",
        "temporal_sequence",
    ]
    weight: float
    evidence: str
    time_delta_hours: float


class NarrativeGraph(BaseModel):
    narrative_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
