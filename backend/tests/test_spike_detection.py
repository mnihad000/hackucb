import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from demo_data import DEMO_DOCUMENTS, DEMO_NARRATIVES
from services.spike_detection import SpikeDetector


detector = SpikeDetector()


def test_compute_spike_score_returns_float():
    score = detector.compute_spike_score("hidden energy tax", DEMO_DOCUMENTS)
    assert isinstance(score, float)
    assert score >= 0.0


def test_compute_spike_score_known_phrase():
    score = detector.compute_spike_score("hidden energy tax", DEMO_DOCUMENTS)
    # "hidden energy tax" appears in docs 1–6, all within 2 days — score >= 1.0
    assert score >= 1.0


def test_compute_spike_score_unknown_phrase():
    score = detector.compute_spike_score("nonexistent phrase xyz", DEMO_DOCUMENTS)
    assert score == 0.0


def test_get_spiking_narratives_sorted():
    results = detector.get_spiking_narratives(DEMO_NARRATIVES, DEMO_DOCUMENTS)
    assert len(results) == len(DEMO_NARRATIVES)
    scores = [n.spike_score for n in results]
    assert scores == sorted(scores, reverse=True)


def test_get_spiking_narratives_first_is_energy():
    results = detector.get_spiking_narratives(DEMO_NARRATIVES, DEMO_DOCUMENTS)
    assert results[0].id == "narrative_001"


def test_compute_phrase_timeline_returns_sorted_dates():
    timeline = detector.compute_phrase_timeline("hidden energy tax", DEMO_DOCUMENTS)
    assert isinstance(timeline, list)
    dates = [entry["date"] for entry in timeline]
    assert dates == sorted(dates)


def test_compute_phrase_timeline_counts():
    timeline = detector.compute_phrase_timeline("hidden energy tax", DEMO_DOCUMENTS)
    total = sum(e["count"] for e in timeline)
    assert total >= 6  # At least 6 docs contain this phrase
