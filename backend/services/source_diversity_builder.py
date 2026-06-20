from __future__ import annotations

from collections import Counter

from models.document import Document
from models.investigation import (
    InvestigationPlan,
    RetrievalResult,
    SourceDiversityFinding,
    SourceDiversityResult,
)

_CONFIDENCE_SCORES = {"low": 0.32, "medium": 0.58, "high": 0.82}


def build_source_diversity(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
) -> SourceDiversityResult:
    source_type_distribution = Counter(doc.source_type for doc in documents)
    geographic_distribution = Counter((doc.geographic_scope or "unknown") for doc in documents)
    institution_distribution = Counter(
        (doc.source_profile.institution_kind if doc.source_profile else "unknown")
        for doc in documents
    )
    content_form_distribution = Counter(
        (doc.source_profile.content_form if doc.source_profile else "unknown")
        for doc in documents
    )
    ideology_distribution = Counter(
        (doc.source_profile.ideology if doc.source_profile else "unknown")
        for doc in documents
    )

    classified_documents = sum(1 for doc in documents if doc.source_profile is not None)
    findings = _build_findings(
        documents,
        source_type_distribution,
        geographic_distribution,
        institution_distribution,
    )
    limitations = _build_limitations(documents, ideology_distribution)
    confidence_score, confidence_label = _confidence(
        retrieval,
        documents,
        institution_distribution,
        content_form_distribution,
    )

    return SourceDiversityResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        total_documents=len(documents),
        classified_documents=classified_documents,
        source_type_distribution=dict(source_type_distribution),
        geographic_distribution=dict(geographic_distribution),
        institution_distribution=dict(institution_distribution),
        content_form_distribution=dict(content_form_distribution),
        ideology_distribution=dict(ideology_distribution),
        findings=findings,
        limitations=limitations,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
    )


def _build_findings(
    documents: list[Document],
    source_type_distribution: Counter[str],
    geographic_distribution: Counter[str],
    institution_distribution: Counter[str],
) -> list[SourceDiversityFinding]:
    findings: list[SourceDiversityFinding] = []
    total = len(documents)
    if not documents:
        return findings

    top_source_type, top_source_count = source_type_distribution.most_common(1)[0]
    if top_source_count / total >= 0.6:
        findings.append(
            SourceDiversityFinding(
                id="source_type_concentration",
                label="Concentrated source type",
                detail=(
                    f"{top_source_count} of {total} retrieved documents come from "
                    f"{top_source_type.replace('_', ' ')} sources."
                ),
            )
        )
    else:
        findings.append(
            SourceDiversityFinding(
                id="source_type_spread",
                label="Mixed source types",
                detail=(
                    f"The retrieved corpus spans {len(source_type_distribution)} source type categories "
                    "rather than a single dominant channel."
                ),
            )
        )

    top_geo, top_geo_count = geographic_distribution.most_common(1)[0]
    findings.append(
        SourceDiversityFinding(
            id="geographic_mix",
            label="Geographic footprint",
            detail=(
                f"The largest geographic slice is {top_geo.replace('_', ' ')} at "
                f"{top_geo_count} of {total} documents."
            ),
        )
    )

    official_count = institution_distribution.get("official", 0)
    if official_count > 0:
        findings.append(
            SourceDiversityFinding(
                id="official_presence",
                label="Official participation",
                detail=f"{official_count} retrieved document(s) are classified as official or transcript-style sources.",
            )
        )
    else:
        findings.append(
            SourceDiversityFinding(
                id="official_absence",
                label="No official sources observed",
                detail="The retrieved corpus does not currently include an official or transcript-style source.",
            )
        )

    unknown_count = institution_distribution.get("unknown", 0)
    if unknown_count / total >= 0.35:
        findings.append(
            SourceDiversityFinding(
                id="unknown_share",
                label="Classification gaps",
                detail=(
                    f"{unknown_count} of {total} documents still have unknown institutional labels, "
                    "so ecosystem conclusions should remain cautious."
                ),
            )
        )
    return findings[:5]


def _build_limitations(
    documents: list[Document],
    ideology_distribution: Counter[str],
) -> list[str]:
    limitations: list[str] = []
    if not documents:
        limitations.append("No retrieved documents were available for source diversity analysis.")
        return limitations
    if ideology_distribution and ideology_distribution.get("unknown", 0) == len(documents):
        limitations.append(
            "Ideology labels are registry-backed only in v1, so most or all sources may remain unknown."
        )
    limitations.append(
        "Source diversity describes the observed dataset and should not be interpreted as a truth score."
    )
    return limitations


def _confidence(
    retrieval: RetrievalResult,
    documents: list[Document],
    institution_distribution: Counter[str],
    content_form_distribution: Counter[str],
) -> tuple[float, str]:
    if not documents:
        return 0.0, "low"

    known_institution_share = 1 - (institution_distribution.get("unknown", 0) / len(documents))
    known_content_share = 1 - (content_form_distribution.get("unknown", 0) / len(documents))
    distinct_source_types = len(retrieval.coverage_summary.source_type_distribution)
    diversity_factor = min(1.0, distinct_source_types / 4)
    retrieval_factor = _CONFIDENCE_SCORES.get(retrieval.evidence_coverage_confidence, 0.32)
    score = round(
        min(
            0.95,
            (known_institution_share * 0.35)
            + (known_content_share * 0.2)
            + (diversity_factor * 0.2)
            + (retrieval_factor * 0.25),
        ),
        3,
    )
    if score >= 0.72:
        return score, "high"
    if score >= 0.46:
        return score, "medium"
    return score, "low"
