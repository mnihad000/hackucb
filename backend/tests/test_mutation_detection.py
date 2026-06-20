import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from demo_data import DEMO_DOCUMENTS, DEMO_NARRATIVES
from services.mutation_detection import MutationDetector


detector = MutationDetector()


def test_detect_mutations_returns_list():
    results = detector.detect_mutations(DEMO_DOCUMENTS)
    assert isinstance(results, list)


def test_detect_mutations_chronological():
    results = detector.detect_mutations(DEMO_DOCUMENTS)
    timestamps = [m["doc_a_timestamp"] for m in results]
    assert timestamps == sorted(timestamps)


def test_detect_mutations_types():
    results = detector.detect_mutations(DEMO_DOCUMENTS)
    for m in results:
        assert m["mutation_type"] in ("mutation", "phrase_reuse")
        assert 0.0 <= m["similarity"] <= 1.0


def test_detect_mutations_finds_energy_tax_mutations():
    results = detector.detect_mutations(DEMO_DOCUMENTS)
    mutation_pairs = [(m["phrase_a"], m["phrase_b"]) for m in results if m["mutation_type"] == "mutation"]
    # Should find at least one mutation between the phrase generations
    assert len(mutation_pairs) > 0


def test_build_mutation_trail_demo_mode():
    cluster = DEMO_NARRATIVES[0]
    mutations = detector.detect_mutations(DEMO_DOCUMENTS[:6])
    trail = detector.build_mutation_trail(mutations, cluster)
    # In demo mode, returns the pre-built cluster trail
    assert len(trail) == 4
    assert trail[0].phrase == "hidden energy tax"
    assert trail[-1].phrase == "ratepayer burden"


def test_detect_mutations_similarity_range():
    results = detector.detect_mutations(DEMO_DOCUMENTS)
    for m in results:
        if m["mutation_type"] == "mutation":
            assert 0.40 <= m["similarity"] <= 0.85
        elif m["mutation_type"] == "phrase_reuse":
            assert m["similarity"] > 0.85
