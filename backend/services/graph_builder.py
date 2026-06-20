from datetime import timedelta, datetime, timezone

from config import get_settings
from models.document import Document
from models.graph import GraphEdge, GraphNode, NarrativeGraph
from models.narrative import NarrativeCluster


class GraphBuilder:
    def __init__(self) -> None:
        self._settings = get_settings()

    def build_graph(
        self,
        documents: list[Document],
        mutations: list[dict],
        cluster: NarrativeCluster | None = None,
    ) -> NarrativeGraph:
        narrative_id = cluster.id if cluster else "unknown"

        # Build nodes — one per document
        nodes: list[GraphNode] = []
        for doc in sorted(documents, key=lambda d: d.published_at or datetime.max.replace(tzinfo=timezone.utc)):
            phrase_used = doc.phrases[0] if doc.phrases else ""
            nodes.append(
                GraphNode(
                    id=doc.id,
                    label=doc.source_name,
                    source_type=doc.source_type,
                    timestamp=doc.published_at,
                    title=doc.title,
                    url=doc.url,
                    phrase_used=phrase_used,
                )
            )

        doc_map = {d.id: d for d in documents}
        edges: list[GraphEdge] = []
        seen_edges: set[tuple[str, str]] = set()

        def add_edge(edge: GraphEdge) -> None:
            key = (edge.source, edge.target)
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append(edge)

        # Rule 1 — phrase_mutation / phrase_reuse from mutation detection
        for m in mutations:
            doc_a = doc_map.get(m["doc_a_id"])
            doc_b = doc_map.get(m["doc_b_id"])
            if not doc_a or not doc_b:
                continue
            if doc_a.published_at is None or doc_b.published_at is None:
                continue
            delta_hours = (doc_b.published_at - doc_a.published_at).total_seconds() / 3600
            # mutation_detection uses "mutation"; GraphEdge literal uses "phrase_mutation"
            edge_type = "phrase_mutation" if m["mutation_type"] == "mutation" else m["mutation_type"]
            add_edge(
                GraphEdge(
                    source=doc_a.id,
                    target=doc_b.id,
                    edge_type=edge_type,
                    weight=round(m["similarity"], 2),
                    evidence=(
                        f"'{m['phrase_a']}' → '{m['phrase_b']}'. "
                        f"Similarity {m['similarity']:.2f}."
                    ),
                    time_delta_hours=round(delta_hours, 2),
                )
            )

        # Rule 2 — entity_overlap: shared entity + within ENTITY_OVERLAP_WINDOW_HOURS
        window = timedelta(hours=self._settings.ENTITY_OVERLAP_WINDOW_HOURS)
        sorted_docs = sorted(documents, key=lambda d: d.published_at or datetime.max.replace(tzinfo=timezone.utc))
        for i, doc_a in enumerate(sorted_docs):
            for doc_b in sorted_docs[i + 1:]:
                if doc_a.published_at is None or doc_b.published_at is None:
                    continue
                delta = doc_b.published_at - doc_a.published_at
                if delta > window:
                    break
                shared = set(e.lower() for e in doc_a.entities) & set(
                    e.lower() for e in doc_b.entities
                )
                if shared:
                    delta_hours = delta.total_seconds() / 3600
                    add_edge(
                        GraphEdge(
                            source=doc_a.id,
                            target=doc_b.id,
                            edge_type="entity_overlap",
                            weight=round(min(1.0, len(shared) * 0.3), 2),
                            evidence=f"Shared entities: {', '.join(sorted(shared)[:3])}.",
                            time_delta_hours=round(delta_hours, 2),
                        )
                    )

        # Rule 3 — temporal_sequence: consecutive docs in timeline within 48 hours
        for i in range(len(sorted_docs) - 1):
            doc_a = sorted_docs[i]
            doc_b = sorted_docs[i + 1]
            if doc_a.published_at is None or doc_b.published_at is None:
                continue
            delta = doc_b.published_at - doc_a.published_at
            delta_hours = delta.total_seconds() / 3600
            if delta_hours <= 48:
                add_edge(
                    GraphEdge(
                        source=doc_a.id,
                        target=doc_b.id,
                        edge_type="temporal_sequence",
                        weight=round(max(0.3, 1.0 - delta_hours / 48), 2),
                        evidence=f"Consecutive documents in timeline. Gap: {delta_hours:.1f}h.",
                        time_delta_hours=round(delta_hours, 2),
                    )
                )

        return NarrativeGraph(narrative_id=narrative_id, nodes=nodes, edges=edges)
