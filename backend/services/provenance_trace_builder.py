from __future__ import annotations

from collections import defaultdict

from models.document import Document
from models.investigation import (
    InvestigationPlan,
    ProvenanceTraceNode,
    ProvenanceTraceResult,
    RetrievalResult,
)


def build_provenance_trace(
    investigation_id: str,
    plan: InvestigationPlan,
    retrieval: RetrievalResult,
    documents: list[Document],
) -> ProvenanceTraceResult:
    docs_by_id = {doc.id: doc for doc in documents}
    sorted_docs = sorted(
        [doc for doc in documents if doc.published_at is not None],
        key=lambda doc: (doc.published_at, doc.source_name, doc.id),
    )
    earliest = sorted_docs[0] if sorted_docs else None
    duplicate_clusters: dict[str, list[str]] = defaultdict(list)
    for pair in retrieval.possible_duplicate_pairs:
        if pair.cluster_id is None:
            continue
        duplicate_clusters[pair.cluster_id].extend([pair.left_doc_id, pair.right_doc_id])
    duplicate_clusters = {
        cluster_id: list(dict.fromkeys(doc_ids)) for cluster_id, doc_ids in duplicate_clusters.items()
    }

    official_doc = next(
        (doc for doc in sorted_docs if doc.source_name.endswith(".gov") or doc.source_type == "speech_transcript"),
        None,
    )
    likely_upstream_source = None
    trace_nodes: list[ProvenanceTraceNode] = []
    limitations: list[str] = []

    if earliest is not None:
        trace_nodes.append(
            ProvenanceTraceNode(
                document_id=earliest.id,
                source_name=earliest.source_name,
                published_at=earliest.published_at,
                role="earliest_anchor",
                citation_hint=_citation_hint(earliest),
            )
        )
        likely_upstream_source = earliest.source_name
    else:
        limitations.append("No dated document was available to anchor provenance in the retrieved corpus.")

    if official_doc is not None and (earliest is None or official_doc.id != earliest.id):
        trace_nodes.append(
            ProvenanceTraceNode(
                document_id=official_doc.id,
                source_name=official_doc.source_name,
                published_at=official_doc.published_at,
                role="official_anchor",
                citation_hint=_citation_hint(official_doc),
            )
        )

    for annotation in retrieval.document_annotations:
        if annotation.provenance_hint and annotation.document_id in docs_by_id:
            doc = docs_by_id[annotation.document_id]
            trace_nodes.append(
                ProvenanceTraceNode(
                    document_id=doc.id,
                    source_name=doc.source_name,
                    published_at=doc.published_at,
                    role="upstream_reference" if "citation" in annotation.provenance_hint else "context",
                    citation_hint=annotation.provenance_hint,
                )
            )

    if not duplicate_clusters:
        limitations.append("No duplicate or syndication cluster was strong enough to build a source-chain cluster.")
    if plan.intent == "origin" and earliest is None:
        limitations.append("True origin remains unknown because the retrieved corpus lacks a reliable earliest anchor.")
    elif plan.intent == "origin":
        limitations.append("Earliest anchor reflects the retrieved corpus, not guaranteed true origin.")

    confidence = _confidence_score(earliest, official_doc, duplicate_clusters)
    earliest_summary = (
        f"Earliest anchor in the retrieved corpus is {earliest.source_name}."
        if earliest is not None
        else "Earliest anchor could not be established in the retrieved corpus."
    )

    return ProvenanceTraceResult(
        investigation_id=investigation_id,
        plan_snapshot=plan,
        earliest_anchor_document_id=earliest.id if earliest is not None else None,
        earliest_anchor_summary=earliest_summary,
        trace_nodes=_dedupe_trace_nodes(trace_nodes),
        duplicate_clusters=duplicate_clusters,
        likely_upstream_source=likely_upstream_source,
        official_anchor_document_id=official_doc.id if official_doc is not None else None,
        provenance_limitations=limitations,
        confidence_score=confidence,
    )


def _citation_hint(doc: Document) -> str | None:
    lowered = f"{doc.title} {doc.snippet or ''}".lower()
    if "according to" in lowered:
        return "secondary citation language present"
    if doc.source_name.endswith(".gov"):
        return "official domain"
    return None


def _confidence_score(
    earliest: Document | None,
    official_doc: Document | None,
    duplicate_clusters: dict[str, list[str]],
) -> float:
    score = 0.18
    if earliest is not None:
        score += 0.34
    if official_doc is not None:
        score += 0.18
    if duplicate_clusters:
        score += 0.14
    return round(min(score, 0.92), 3)


def _dedupe_trace_nodes(nodes: list[ProvenanceTraceNode]) -> list[ProvenanceTraceNode]:
    output: list[ProvenanceTraceNode] = []
    seen: set[tuple[str, str]] = set()
    for node in nodes:
        key = (node.document_id, node.role)
        if key in seen:
            continue
        seen.add(key)
        output.append(node)
    return output
