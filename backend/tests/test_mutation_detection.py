import sys
import os
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from config import get_settings
from demo_data import DEMO_DOCUMENTS, DEMO_NARRATIVES
from models.document import Document
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
        assert 0.0 <= m["similarity_score"] <= 1.0
        assert m["time_delta_hours"] >= 0.0
        assert "from_phrase" in m and "to_phrase" in m
        assert 0.0 <= m["similarity"] <= 1.0


def test_detect_mutations_finds_energy_tax_mutations():
    results = detector.detect_mutations(DEMO_DOCUMENTS)
    mutation_pairs = [(m["from_phrase"], m["to_phrase"]) for m in results if m["mutation_type"] == "mutation"]
    # Should find at least one mutation between the phrase generations
    assert len(mutation_pairs) > 0


def test_build_mutation_trail_demo_mode(monkeypatch):
    cluster = DEMO_NARRATIVES[0]
    monkeypatch.setattr(get_settings(), "DEMO_MODE", True)
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


def test_detect_mutations_rejects_unrelated_phrases():
    docs = [
        Document(
            id="doc_a",
            source_id="domain:a.example",
            source_name="a.example",
            source_type="blog",
            url="https://a.example/doc_a",
            title="Alpha story",
            published_at=datetime(2026, 6, 20, 8, 0, tzinfo=timezone.utc),
            collected_at=datetime(2026, 6, 20, 8, 30, tzinfo=timezone.utc),
            text="alpha phrase only",
            snippet="alpha phrase only",
            language="en",
            content_type="article",
            geographic_scope="national",
            entities=["alpha"],
            phrases=["alpha garden signal"],
            metadata={},
        ),
        Document(
            id="doc_b",
            source_id="domain:b.example",
            source_name="b.example",
            source_type="commentary",
            url="https://b.example/doc_b",
            title="Beta story",
            published_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
            collected_at=datetime(2026, 6, 20, 12, 30, tzinfo=timezone.utc),
            text="beta phrase only",
            snippet="beta phrase only",
            language="en",
            content_type="article",
            geographic_scope="national",
            entities=["beta"],
            phrases=["unrelated harbor ledger"],
            metadata={},
        ),
    ]

    results = detector.detect_mutations(docs)

    assert results == []
