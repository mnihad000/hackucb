import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.investigation import InvestigationPlan, InvestigationPlanTimeWindow, RetrievalResult
from services.source_diversity_builder import build_source_diversity
from services.source_profile_enricher import SourceProfileEnricher


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        query_text="Trace the hidden energy tax story.",
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="spread",
        entities=["energy", "tax"],
        search_queries=["hidden energy tax"],
        semantic_queries=["trace hidden energy tax spread"],
        target_source_types=["local_news", "national_news", "speech_transcript", "blog"],
        requested_outputs=["source_diversity"],
        time_window=InvestigationPlanTimeWindow(label="all_time"),
        retrieval_mode="broad",
        risk_notes=[],
        uncertainty_requirements=[],
    )


def _document(
    doc_id: str,
    source_name: str,
    source_type: str,
    *,
    url: str,
    geographic_scope: str | None,
) -> Document:
    return Document(
        id=doc_id,
        source_id=f"domain:{source_name}",
        source_name=source_name,
        source_type=source_type,
        url=url,
        title=f"{doc_id} title",
        author=None,
        published_at=datetime(2026, 6, 3, 8, 0, tzinfo=timezone.utc),
        collected_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
        text="Hidden energy tax coverage",
        snippet="Hidden energy tax coverage",
        language="en",
        content_type="article",
        geographic_scope=geographic_scope,
        entities=["energy"],
        phrases=["hidden energy tax"],
        metadata={},
    )


def _retrieval(plan: InvestigationPlan, document_ids: list[str]) -> RetrievalResult:
    return RetrievalResult(
        investigation_id="inv_source_diversity",
        plan_snapshot=plan,
        retrieved_document_ids=document_ids,
        high_relevance_document_ids=document_ids,
        main_narrative_document_ids=document_ids,
        counter_narrative_candidate_ids=[],
        context_document_ids=[],
        warnings=[],
        evidence_coverage_confidence="high",
    )


def test_source_profile_enricher_classifies_known_and_unknown_sources():
    enricher = SourceProfileEnricher()
    docs = [
        _document(
            "doc_reuters",
            "reuters.com",
            "national_news",
            url="https://reuters.com/story",
            geographic_scope="national",
        ),
        _document(
            "doc_official",
            "statehouse.gov",
            "speech_transcript",
            url="https://statehouse.gov/remarks",
            geographic_scope="state",
        ),
        _document(
            "doc_blog",
            "civicblog.com",
            "blog",
            url="https://civicblog.com/post",
            geographic_scope="local",
        ),
        _document(
            "doc_unknown",
            "odd.example",
            "commentary",
            url="https://odd.example/view",
            geographic_scope=None,
        ),
    ]

    enriched = enricher.enrich_documents(docs)

    assert enriched[0].source_profile is not None
    assert enriched[0].source_profile.classification_method == "registry"
    assert enriched[0].source_profile.ideology == "center"
    assert enriched[1].source_profile is not None
    assert enriched[1].source_profile.institution_kind == "official"
    assert enriched[1].source_profile.content_form == "transcript"
    assert enriched[2].source_profile is not None
    assert enriched[2].source_profile.institution_kind == "independent"
    assert enriched[2].source_profile.content_form == "opinion"
    assert enriched[3].source_profile is not None
    assert enriched[3].source_profile.ideology == "unknown"


def test_source_diversity_builder_produces_distributions_and_confidence():
    plan = _plan()
    docs = SourceProfileEnricher().enrich_documents(
        [
            _document("doc_1", "reuters.com", "national_news", url="https://reuters.com/1", geographic_scope="national"),
            _document("doc_2", "springfieldgazette.com", "local_news", url="https://springfieldgazette.com/2", geographic_scope="local"),
            _document("doc_3", "statehouse.gov", "speech_transcript", url="https://statehouse.gov/3", geographic_scope="state"),
            _document("doc_4", "civicblog.com", "blog", url="https://civicblog.com/4", geographic_scope="local"),
        ]
    )
    retrieval = _retrieval(plan, [doc.id for doc in docs])

    result = build_source_diversity("inv_source_diversity", plan, retrieval, docs)

    assert result.total_documents == 4
    assert result.classified_documents == 4
    assert result.source_type_distribution["local_news"] == 1
    assert result.institution_distribution["official"] == 1
    assert result.content_form_distribution["transcript"] == 1
    assert result.ideology_distribution["center"] == 1
    assert result.findings
    assert result.confidence_label in {"medium", "high"}


def test_source_diversity_confidence_drops_with_unknown_labels():
    plan = _plan()
    docs = [
        _document("doc_1", "unknown-one.example", "commentary", url="https://unknown-one.example/1", geographic_scope=None),
        _document("doc_2", "unknown-two.example", "commentary", url="https://unknown-two.example/2", geographic_scope=None),
    ]
    retrieval = _retrieval(plan, [doc.id for doc in docs]).model_copy(
        update={"evidence_coverage_confidence": "low"}
    )

    result = build_source_diversity("inv_source_diversity", plan, retrieval, docs)

    assert result.institution_distribution["unknown"] == 2
    assert result.confidence_label == "low"
    assert any("unknown" in finding.detail.lower() for finding in result.findings)
