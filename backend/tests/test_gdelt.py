import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from services.gdelt import (
    GDELTIngestion,
    build_first_observed_label,
    build_timeline,
    _classify_source,
    _extract_phrases,
    _parse_gdelt_date,
)


# ---------------------------------------------------------------------------
# Unit tests — no HTTP calls
# ---------------------------------------------------------------------------

def test_classify_blog_domain():
    assert _classify_source("substack.com") == "blog"
    assert _classify_source("medium.com") == "blog"


def test_classify_national_domain():
    assert _classify_source("reuters.com") == "national_news"
    assert _classify_source("nytimes.com") == "national_news"


def test_classify_local_domain():
    assert _classify_source("springfieldgazette.com") == "local_news"
    assert _classify_source("riverdaleherald.com") == "local_news"


def test_classify_default_national():
    assert _classify_source("unknownsite.net") == "national_news"


def test_parse_gdelt_date_t_format():
    dt = _parse_gdelt_date("20260601T120000Z")
    assert dt.year == 2026
    assert dt.month == 6
    assert dt.day == 1
    assert dt.hour == 12
    assert dt.tzinfo == timezone.utc


def test_parse_gdelt_date_compact_format():
    dt = _parse_gdelt_date("20260601120000")
    assert dt.year == 2026
    assert dt.month == 6


def test_parse_gdelt_date_invalid_returns_now():
    dt = _parse_gdelt_date("not-a-date")
    assert dt.year >= 2026


def test_extract_phrases_finds_bigrams():
    phrases = _extract_phrases("Energy tax hike sparks debate", "energy tax")
    assert any("energy tax" in p for p in phrases)


def test_extract_phrases_caps_at_four():
    phrases = _extract_phrases(
        "energy tax energy tax energy tax energy tax energy tax", "energy tax"
    )
    assert len(phrases) <= 4


def test_map_article_structure():
    ingestion = GDELTIngestion()
    article = {
        "url": "https://reuters.com/energy/tax-2026",
        "domain": "reuters.com",
        "title": "Hidden energy tax sparks consumer anger",
        "seendate": "20260603T090000Z",
        "language": "English",
        "sourcecountry": "United States",
    }
    doc = ingestion._map_article(article, "energy tax", 0)
    assert doc.source_type == "national_news"
    assert doc.source_name == "reuters.com"
    assert doc.published_at.year == 2026
    assert doc.url == "https://reuters.com/energy/tax-2026"
    assert doc.language == "english"
    assert doc.content_type == "article"
    assert doc.geographic_scope == "national"
    assert doc.metadata["dataset"] == "gdelt_doc_2"
    assert len(doc.phrases) > 0


def test_map_article_stable_id():
    ingestion = GDELTIngestion()
    article = {"url": "https://example.com/article", "domain": "example.com", "title": "Test", "seendate": "20260601T000000Z"}
    doc1 = ingestion._map_article(article, "energy", 0)
    doc2 = ingestion._map_article(article, "energy", 99)
    assert doc1.id == doc2.id  # ID is derived from URL, not index


def test_fetch_articles_mocked():
    """Verify mapping logic against a realistic GDELT response payload."""
    fake_response = {
        "articles": [
            {
                "url": "https://politico.com/energy-tax-2026",
                "domain": "politico.com",
                "title": "Senate debates hidden energy tax legislation",
                "seendate": "20260604T140000Z",
                "language": "English",
                "sourcecountry": "United States",
            },
            {
                "url": "https://springfieldgazette.com/local-energy",
                "domain": "springfieldgazette.com",
                "title": "Local utility faces secret energy surcharge scrutiny",
                "seendate": "20260603T080000Z",
                "language": "English",
                "sourcecountry": "United States",
            },
        ]
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = fake_response
    mock_resp.raise_for_status.return_value = None

    ingestion = GDELTIngestion()
    with patch("httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
        docs = ingestion.fetch_articles(
            "energy tax",
            datetime(2026, 6, 1, tzinfo=timezone.utc),
            datetime(2026, 6, 18, tzinfo=timezone.utc),
        )

    assert len(docs) == 2
    assert docs[0].source_type == "local_news"
    assert docs[1].source_type == "national_news"
    assert docs[0].published_at.day == 3
    assert docs[1].published_at.day == 4


def test_build_timeline_groups_by_article_date():
    ingestion = GDELTIngestion()
    docs = [
        ingestion._map_article(
            {
                "url": "https://example.com/a",
                "domain": "example.com",
                "title": "Energy tax item one",
                "seendate": "20260603T080000Z",
            },
            "energy tax",
            0,
        ),
        ingestion._map_article(
            {
                "url": "https://example.com/b",
                "domain": "example.com",
                "title": "Energy tax item two",
                "seendate": "20260603T140000Z",
            },
            "energy tax",
            1,
        ),
        ingestion._map_article(
            {
                "url": "https://example.com/c",
                "domain": "example.com",
                "title": "Energy tax item three",
                "seendate": "20260604T090000Z",
            },
            "energy tax",
            2,
        ),
    ]

    timeline = build_timeline(docs)
    assert timeline == [
        {"date": "2026-06-03", "count": 2},
        {"date": "2026-06-04", "count": 1},
    ]


def test_build_first_observed_label_uses_earliest_document():
    ingestion = GDELTIngestion()
    docs = [
        ingestion._map_article(
            {
                "url": "https://example.com/later",
                "domain": "example.com",
                "title": "Later story",
                "seendate": "20260605T090000Z",
            },
            "energy tax",
            0,
        ),
        ingestion._map_article(
            {
                "url": "https://example.com/earlier",
                "domain": "example.com",
                "title": "Earlier story",
                "seendate": "20260603T090000Z",
            },
            "energy tax",
            1,
        ),
    ]

    first_observed = build_first_observed_label(docs)
    assert first_observed is not None
    assert first_observed["label"] == "first observed in our dataset"
    assert first_observed["title"] == "Earlier story"
