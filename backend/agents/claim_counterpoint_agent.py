from __future__ import annotations

import re
from statistics import mean

from models.document import Document
from models.investigation import (
    AnalystResult,
    CandidateClaim,
    ClaimCounterpointPair,
    ClaimCounterpointResult,
    ClaimCounterpointType,
    CounterNarrative,
    CounterNarrativeResult,
    InvestigationPlan,
    ReportCitation,
    RetrievalResult,
)

_STOPWORDS = {
    "about",
    "after",
    "against",
    "argues",
    "around",
    "because",
    "before",
    "being",
    "between",
    "could",
    "every",
    "from",
    "have",
    "into",
    "just",
    "main",
    "might",
    "other",
    "over",
    "same",
    "should",
    "some",
    "than",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "through",
    "under",
    "with",
    "without",
    "would",
}
_CORRECTIVE_TERMS = {
    "correct",
    "corrects",
    "debunk",
    "debunks",
    "dispute",
    "disputes",
    "false",
    "fact",
    "inaccurate",
    "misleading",
    "refute",
    "refutes",
    "reject",
    "rejects",
}
_OPPOSING_TERMS = {
    "against",
    "challenge",
    "challenges",
    "critic",
    "critics",
    "criticize",
    "criticizes",
    "deny",
    "denies",
    "oppose",
    "opposes",
    "opposing",
    "opponents",
    "pushback",
    "reject",
    "rejects",
}
_REFRAMING_TERMS = {
    "alternative",
    "benefit",
    "benefits",
    "however",
    "instead",
    "investment",
    "reframe",
    "reframes",
    "savings",
    "supporters",
}


def build_claim_counterpoints(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
    counter_narratives: CounterNarrativeResult,
    analyst: AnalystResult,
) -> ClaimCounterpointResult:
    docs_by_id = {doc.id: doc for doc in documents}
    counter_clusters_by_doc_id = _counter_clusters_by_doc_id(counter_narratives.counter_narratives)
    candidate_docs = _counter_candidate_documents(retrieval, docs_by_id)
    eligible_claims = [
        claim
        for claim in analyst.candidate_claims
        if claim.claim_type not in {"limitation", "recommendation"}
    ]

    pairs: list[ClaimCounterpointPair] = []
    unmatched_claim_ids: list[str] = []
    limitations = [
        "Claim counterpoints are limited to the retrieved evidence packet and may miss off-dataset responses.",
        "Pairs are ranked heuristically and should be read as approximate opposition, correction, or reframing rather than definitive adjudication.",
    ]

    for claim in eligible_claims:
        pair = _match_claim(
            claim=claim,
            plan=plan,
            docs_by_id=docs_by_id,
            candidate_docs=candidate_docs,
            counter_clusters_by_doc_id=counter_clusters_by_doc_id,
        )
        if pair is None:
            unmatched_claim_ids.append(claim.id)
            continue
        pairs.append(pair)

    confidence_score = round(mean(pair.confidence_score for pair in pairs), 3) if pairs else 0.28
    confidence_label = _confidence_label(confidence_score)
    return ClaimCounterpointResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        pairs=pairs,
        unmatched_claim_ids=unmatched_claim_ids,
        limitations=limitations,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
    )


def _match_claim(
    *,
    claim: CandidateClaim,
    plan: InvestigationPlan,
    docs_by_id: dict[str, Document],
    candidate_docs: list[Document],
    counter_clusters_by_doc_id: dict[str, CounterNarrative],
) -> ClaimCounterpointPair | None:
    main_docs = [docs_by_id[doc_id] for doc_id in claim.supporting_document_ids if doc_id in docs_by_id]
    main_terms = _claim_terms(claim, plan, main_docs)
    main_entities = {entity.lower() for doc in main_docs for entity in doc.entities}
    main_sources = {doc.source_name for doc in main_docs}

    ranked: list[tuple[float, ClaimCounterpointType, Document, CounterNarrative | None, list[str]]] = []
    for doc in candidate_docs:
        counter_type = _counter_type(doc)
        if counter_type is None:
            continue
        doc_terms = _document_terms(doc)
        shared_terms = sorted(main_terms & doc_terms)
        shared_entities = sorted(main_entities & {entity.lower() for entity in doc.entities})
        cluster = counter_clusters_by_doc_id.get(doc.id)
        if cluster is not None:
            shared_terms = sorted(set(shared_terms) | {token for token in _tokenize(cluster.title) if token in main_terms})

        # Reject generic disagreement that does not appear to address the same topic.
        if not shared_terms and not shared_entities:
            continue

        score = _score_candidate(
            doc=doc,
            counter_type=counter_type,
            shared_terms=shared_terms,
            shared_entities=shared_entities,
            cluster=cluster,
            main_sources=main_sources,
        )
        if score < 0.5:
            continue
        ranked.append((score, counter_type, doc, cluster, shared_terms))

    if not ranked:
        return None

    ranked.sort(
        key=lambda item: (
            -item[0],
            item[1] != "corrective",
            item[1] != "opposing",
            item[2].id,
        )
    )
    score, counter_type, best_doc, cluster, shared_terms = ranked[0]
    main_receipts = [_to_receipt(doc, _main_relevance_note(claim)) for doc in main_docs[:2]]
    counter_docs = [best_doc]
    counter_receipts = [_to_receipt(best_doc, _counter_relevance_note(counter_type, claim))]
    caveats = list(claim.caveats)
    if cluster is None:
        caveats.append("Counterpoint is inferred from one retrieved document rather than a broader counter-frame cluster.")

    return ClaimCounterpointPair(
        claim_id=claim.id,
        main_claim_text=claim.claim_text,
        counter_claim_text=_counter_claim_text(best_doc, cluster),
        counter_type=counter_type,
        relationship_summary=_relationship_summary(counter_type, claim.claim_text, best_doc, shared_terms),
        supporting_document_ids=[doc.id for doc in main_docs],
        counter_document_ids=[doc.id for doc in counter_docs],
        main_receipts=main_receipts,
        counter_receipts=counter_receipts,
        confidence_score=round(min(score, 0.94), 3),
        caveats=caveats,
    )


def _counter_candidate_documents(
    retrieval: RetrievalResult,
    docs_by_id: dict[str, Document],
) -> list[Document]:
    seen: set[str] = set()
    ordered_ids = [
        *retrieval.counter_narrative_candidate_ids,
        *retrieval.context_document_ids,
        *retrieval.retrieved_document_ids,
    ]
    docs: list[Document] = []
    for doc_id in ordered_ids:
        if doc_id in seen or doc_id not in docs_by_id:
            continue
        seen.add(doc_id)
        docs.append(docs_by_id[doc_id])
    return docs


def _counter_clusters_by_doc_id(
    counter_narratives: list[CounterNarrative],
) -> dict[str, CounterNarrative]:
    mapping: dict[str, CounterNarrative] = {}
    for cluster in counter_narratives:
        for doc_id in cluster.supporting_document_ids:
            mapping[doc_id] = cluster
    return mapping


def _claim_terms(
    claim: CandidateClaim,
    plan: InvestigationPlan,
    main_docs: list[Document],
) -> set[str]:
    terms = set(_tokenize(claim.claim_text))
    terms.update(_tokenize(plan.canonical_phrase or plan.topic))
    for doc in main_docs:
        for phrase in doc.phrases:
            terms.update(_tokenize(phrase))
        for entity in doc.entities:
            terms.update(_tokenize(entity))
    return terms


def _document_terms(doc: Document) -> set[str]:
    terms = set(_tokenize(doc.title))
    if doc.snippet:
        terms.update(_tokenize(doc.snippet))
    if doc.text:
        terms.update(_tokenize(doc.text))
    for phrase in doc.phrases:
        terms.update(_tokenize(phrase))
    for entity in doc.entities:
        terms.update(_tokenize(entity))
    return terms


def _counter_type(doc: Document) -> ClaimCounterpointType | None:
    haystack = " ".join(
        filter(
            None,
            [doc.title.lower(), (doc.snippet or "").lower(), doc.text.lower()],
        )
    )
    tokens = set(_tokenize(haystack))
    if tokens & _CORRECTIVE_TERMS:
        return "corrective"
    if tokens & _OPPOSING_TERMS:
        return "opposing"
    if tokens & _REFRAMING_TERMS:
        return "reframing"
    return None


def _score_candidate(
    *,
    doc: Document,
    counter_type: ClaimCounterpointType,
    shared_terms: list[str],
    shared_entities: list[str],
    cluster: CounterNarrative | None,
    main_sources: set[str],
) -> float:
    base = {"corrective": 0.39, "opposing": 0.34, "reframing": 0.3}[counter_type]
    score = base
    score += min(0.26, len(shared_terms) * 0.06)
    score += min(0.1, len(shared_entities) * 0.05)
    score += min(0.12, (doc.metadata or {}).get("retrieval_score", 0.0) / 40)
    if doc.snippet:
        score += 0.06
    if cluster is not None:
        score += 0.08
    if doc.source_name not in main_sources:
        score += 0.05
    return round(score, 3)


def _counter_claim_text(doc: Document, cluster: CounterNarrative | None) -> str:
    if doc.snippet:
        return doc.snippet.strip()
    if cluster is not None:
        return cluster.summary
    return doc.title


def _relationship_summary(
    counter_type: ClaimCounterpointType,
    claim_text: str,
    doc: Document,
    shared_terms: list[str],
) -> str:
    type_text = {
        "corrective": "directly corrects or disputes",
        "opposing": "pushes back against",
        "reframing": "reframes",
    }[counter_type]
    overlap = f" Shared topic terms: {', '.join(shared_terms[:4])}." if shared_terms else ""
    return f"This source {type_text} the claim '{claim_text}' in {doc.source_name}.{overlap}"


def _main_relevance_note(claim: CandidateClaim) -> str:
    return f"Supports the main claim '{claim.claim_text}'."


def _counter_relevance_note(counter_type: ClaimCounterpointType, claim: CandidateClaim) -> str:
    label = {
        "corrective": "Provides a corrective counterpoint to",
        "opposing": "Provides an opposing counterpoint to",
        "reframing": "Provides an alternative framing for",
    }[counter_type]
    return f"{label} '{claim.claim_text}'."


def _to_receipt(doc: Document, relevance_note: str) -> ReportCitation:
    return ReportCitation(
        document_id=doc.id,
        source_name=doc.source_name,
        source_type=doc.source_type,
        title=doc.title,
        url=doc.url,
        published_at=doc.published_at,
        snippet=doc.snippet or _truncate(doc.text),
        relevance_note=relevance_note,
    )


def _truncate(text: str, limit: int = 220) -> str:
    value = text.strip()
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def _confidence_label(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.48:
        return "medium"
    return "low"


def _tokenize(text: str | None) -> list[str]:
    if not text:
        return []
    return [
        token
        for token in re.findall(r"[a-z0-9']+", text.lower())
        if len(token) > 3 and token not in _STOPWORDS
    ]
