import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from demo_data import DEMO_DOCUMENTS, DEMO_NARRATIVES
from services.graph_builder import GraphBuilder
from services.mutation_detection import MutationDetector


builder = GraphBuilder()
detector = MutationDetector()


def _build(docs=None, cluster=None):
    docs = docs or DEMO_DOCUMENTS
    cluster = cluster or DEMO_NARRATIVES[0]
    mutations = detector.detect_mutations(docs)
    return builder.build_graph(docs, mutations, cluster)


def test_graph_has_nodes():
    graph = _build()
    assert len(graph.nodes) == len(DEMO_DOCUMENTS)


def test_graph_node_ids_match_docs():
    graph = _build()
    node_ids = {n.id for n in graph.nodes}
    doc_ids = {d.id for d in DEMO_DOCUMENTS}
    assert node_ids == doc_ids


def test_graph_has_edges():
    graph = _build()
    assert len(graph.edges) > 0


def test_graph_edge_types_valid():
    valid_types = {"phrase_reuse", "phrase_mutation", "semantic_similarity", "entity_overlap", "temporal_sequence"}
    graph = _build()
    for edge in graph.edges:
        assert edge.edge_type in valid_types


def test_graph_edges_reference_valid_nodes():
    graph = _build()
    node_ids = {n.id for n in graph.nodes}
    for edge in graph.edges:
        assert edge.source in node_ids
        assert edge.target in node_ids


def test_graph_edge_weights_in_range():
    graph = _build()
    for edge in graph.edges:
        assert 0.0 <= edge.weight <= 1.0


def test_graph_narrative_id():
    graph = _build()
    assert graph.narrative_id == "narrative_001"
