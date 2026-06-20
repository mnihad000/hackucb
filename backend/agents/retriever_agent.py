from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
import logging
import re

from config import get_settings
from demo_data import ALL_DOCUMENTS
from models.document import Document
from models.investigation import (
    CoverageSummary,
    DuplicateCandidate,
    InvestigationPlan,
    RetrievalResult,
    RetrievalRound,
    SearchResult,
)
from services.ingestion import get_merged_documents
from services.document_normalizer import DocumentNormalizer
from services.document_store import live_store
from services.investigation_repository import InvestigationRepository
from services.page_fetcher import HttpPageFetcher
from services.redis_vector_store import get_redis_vector_store
from services.search_provider import SearchProvider, build_search_provider

logger = logging.getLogger(__name__)

_COUNTER_SIGNAL_TERMS = {
    "however", "but", "despite", "critics", "supporters", "opponents",
    "denies", "refutes", "debunks", "fact check", "counter", "rebuttal",
}
_TIMELINE_SOURCE_TYPES = {"local_news", "forum", "speech_transcript", "blog"}
_SOURCE_DIVERSITY_OUTPUT = "source_diversity"
_COUNTER_OUTPUT = "counter_narratives"
_TIMELINE_OUTPUT = "timeline"
_GRAPH_OUTPUT = "graph"
_RECEIPTS_OUTPUT = "receipts"


class RetrieverAgent:
    def __init__(
        self,
        repository: InvestigationRepository,
        search_provider: SearchProvider | None = None,
        page_fetcher: HttpPageFetcher | None = None,
        normalizer: DocumentNormalizer | None = None,
    ) -> None:
        self._settings = get_settings()
        self._repository = repository
        self._provider = search_provider
        if self._provider is None and not self._settings.DEMO_MODE:
            self._provider = build_search_provider()
        self._fetcher = page_fetcher or HttpPageFetcher()
        self._normalizer = normalizer or DocumentNormalizer()
        self._vector_store = get_redis_vector_store()

    def retrieve(
        self,
        investigation_id: str,
        plan: InvestigationPlan,
        max_rounds: int | None = None,
        force_refresh: bool = False,
    ) -> RetrievalResult:
        if not force_refresh:
            cached = self._repository.get_retrieval_result(investigation_id)
            if cached is not None:
                return cached.model_copy(update={"cached": True})

        if self._settings.DEMO_MODE:
            return self._retrieve_from_local_corpus(
                investigation_id=investigation_id,
                plan=plan,
            )

        effective_max_rounds = max_rounds or self._settings.RETRIEVER_MAX_ROUNDS
        seen_urls: set[str] = set()
        seen_doc_ids: set[str] = set()
        all_documents: list[Document] = []
        all_rounds: list[RetrievalRound] = []
        warnings: list[str] = []
        all_duplicates: list[DuplicateCandidate] = []
        search_results_by_round: dict[int, list[dict]] = {}
        previous_doc_count = 0

        for round_number in range(1, effective_max_rounds + 1):
            queries = self._build_round_queries(plan, round_number, all_documents)
            round_warnings: list[str] = []
            round_results = self._run_search_round(queries, plan, round_warnings)
            search_results_by_round[round_number] = [result.model_dump(mode="json") for result in round_results]

            fetched_pages = 0
            new_documents = 0
            accepted_documents = 0

            for result in round_results:
                normalized_url = self._normalize_url(result.url)
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)

                fetched = self._fetcher.fetch(result.url)
                if not hasattr(fetched, "html"):
                    round_warnings.append(f"{result.url}: {fetched.error_type}")
                    continue
                fetched_pages += 1

                document = self._normalizer.normalize(fetched, plan, result)
                if document.id in seen_doc_ids:
                    continue
                seen_doc_ids.add(document.id)
                all_documents.append(document)
                accepted_documents += 1
                new_documents += 1

            round_duplicates = self._detect_duplicates(all_documents)
            all_duplicates = round_duplicates
            coverage = self._build_coverage_summary(all_documents, all_rounds + [], round_number, plan)
            round_obj = RetrievalRound(
                round_number=round_number,
                queries=queries,
                provider=self._provider.name,
                discovered_results=len(round_results),
                fetched_pages=fetched_pages,
                accepted_documents=accepted_documents,
                new_documents=new_documents,
                warnings=round_warnings,
            )
            all_rounds.append(round_obj)
            warnings.extend(round_warnings)
            if self._should_stop(
                all_documents,
                coverage,
                new_documents,
                previous_doc_count,
                round_number,
                effective_max_rounds,
                plan,
            ):
                break
            previous_doc_count = len(all_documents)

        scored_documents = self._score_documents(all_documents, plan)
        all_documents = [doc for doc, _ in scored_documents]
        coverage = self._build_coverage_summary(all_documents, all_rounds, len(all_rounds), plan)
        confidence = self._coverage_confidence(coverage)
        categorized = self._categorize_documents(scored_documents, plan)

        result = RetrievalResult(
            investigation_id=investigation_id,
            plan_snapshot=plan,
            retrieved_document_ids=[doc.id for doc in all_documents],
            high_relevance_document_ids=categorized["high_relevance"],
            main_narrative_document_ids=categorized["main_narrative"],
            counter_narrative_candidate_ids=categorized["counter_candidates"],
            context_document_ids=categorized["context"],
            possible_duplicate_pairs=all_duplicates,
            search_rounds=all_rounds,
            warnings=warnings,
            coverage_summary=coverage,
            evidence_coverage_confidence=confidence,
        )
        self._repository.save_retrieval_result(result, all_documents)
        for round_number, search_results in search_results_by_round.items():
            self._repository.save_search_results(investigation_id, round_number, search_results)
        live_store.save_batch(all_documents)

        # Index newly retrieved documents in Redis for future semantic searches
        if self._vector_store and all_documents:
            try:
                indexed = self._vector_store.add_documents_batch(all_documents[:20])
                logger.info("Indexed %d documents in Redis vector store", indexed)
            except Exception as exc:
                logger.warning("Redis document indexing failed: %s", exc)

        return result

    def _retrieve_from_local_corpus(
        self,
        investigation_id: str,
        plan: InvestigationPlan,
    ) -> RetrievalResult:
        corpus = [
            document.model_copy(deep=True)
            for document in get_merged_documents(ALL_DOCUMENTS)
        ]
        scored_documents = self._score_documents(corpus, plan)

        # Augment scores with Redis semantic search when available
        semantic_scores: dict[str, float] = {}
        if self._vector_store:
            try:
                queries = [plan.query_text] + list(plan.semantic_queries[:2])
                for q in queries:
                    for result in self._vector_store.semantic_search(q, limit=10):
                        doc_id = result.id.replace("rq:doc:", "")
                        semantic_scores[doc_id] = max(semantic_scores.get(doc_id, 0.0), result.score)
                if semantic_scores:
                    scored_documents = [
                        (doc, score + semantic_scores.get(doc.id, 0.0) * 3.0)
                        for doc, score in scored_documents
                    ]
                    scored_documents.sort(key=lambda item: item[1], reverse=True)
                    logger.info("Redis semantic search boosted %d documents", len(semantic_scores))
            except Exception as exc:
                logger.warning("Redis semantic search unavailable, using keyword scoring: %s", exc)
        matched_documents = [
            (document, score) for document, score in scored_documents if score > 0
        ]

        if not matched_documents:
            matched_documents = scored_documents[:8]
            warnings = [
                "demo_mode_local_corpus:no strong lexical match found; using top local corpus documents",
            ]
        else:
            warnings = [
                "demo_mode_local_corpus:retrieval used the seeded/local document corpus",
            ]

        selected_pairs = matched_documents[:12]
        selected_documents = [document for document, _score in selected_pairs]
        duplicates = self._detect_duplicates(selected_documents)
        queries = self._build_round_queries(plan, 1, [])
        coverage = self._build_coverage_summary(selected_documents, [], 1, plan)
        confidence = self._coverage_confidence(coverage)
        categorized = self._categorize_documents(selected_pairs, plan)
        search_results = [
            SearchResult(
                query=queries[0] if queries else plan.query_text,
                title=document.title,
                url=document.url,
                snippet=document.snippet,
                rank=index,
                provider="local_demo",
                provider_score=score,
                metadata={"source_name": document.source_name},
            ).model_dump(mode="json")
            for index, (document, score) in enumerate(selected_pairs, start=1)
        ]
        round_obj = RetrievalRound(
            round_number=1,
            queries=queries,
            provider="local_demo",
            discovered_results=len(selected_pairs),
            fetched_pages=len(selected_pairs),
            accepted_documents=len(selected_pairs),
            new_documents=len(selected_pairs),
            warnings=warnings,
        )
        result = RetrievalResult(
            investigation_id=investigation_id,
            plan_snapshot=plan,
            retrieved_document_ids=[doc.id for doc in selected_documents],
            high_relevance_document_ids=categorized["high_relevance"],
            main_narrative_document_ids=categorized["main_narrative"],
            counter_narrative_candidate_ids=categorized["counter_candidates"],
            context_document_ids=categorized["context"],
            possible_duplicate_pairs=duplicates,
            search_rounds=[round_obj],
            warnings=warnings,
            coverage_summary=coverage,
            evidence_coverage_confidence=confidence,
        )
        self._repository.save_retrieval_result(result, selected_documents)
        self._repository.save_search_results(investigation_id, 1, search_results)
        live_store.save_batch(selected_documents)
        return result

    def _build_round_queries(
        self,
        plan: InvestigationPlan,
        round_number: int,
        documents: list[Document],
    ) -> list[str]:
        if round_number == 1:
            return plan.search_queries[: max(1, min(4, self._settings.RETRIEVER_MAX_RESULTS_PER_QUERY))]
        if round_number == 2:
            queries = list(plan.semantic_queries[:2])
            if plan.canonical_phrase and _COUNTER_OUTPUT in plan.requested_outputs:
                queries.append(f"{plan.canonical_phrase} counter narrative")
                queries.append(f"{plan.canonical_phrase} rebuttal response")
            if plan.canonical_phrase and _SOURCE_DIVERSITY_OUTPUT in plan.requested_outputs:
                queries.append(f"{plan.canonical_phrase} official statement")
                queries.append(f"{plan.canonical_phrase} community response")
            if plan.entities:
                queries.append(" ".join(plan.entities[:4]))
            return _dedupe(queries)

        queries = []
        if plan.canonical_phrase and _COUNTER_OUTPUT in plan.requested_outputs:
            queries.append(f"{plan.canonical_phrase} criticism rebuttal")
        if plan.canonical_phrase and _TIMELINE_OUTPUT in plan.requested_outputs:
            queries.append(f"{plan.canonical_phrase} earliest mention")
        if documents:
            oldest = min((doc.published_at for doc in documents if doc.published_at), default=None)
            if oldest:
                queries.append(f"{plan.topic} before {oldest.date().isoformat()}")
            if _SOURCE_DIVERSITY_OUTPUT in plan.requested_outputs:
                scarce_type = self._find_scarce_requested_source_type(documents, plan.target_source_types)
                if scarce_type:
                    queries.append(f"{plan.topic} {scarce_type.replace('_', ' ')}")
        if plan.semantic_queries:
            queries.append(plan.semantic_queries[-1])
        return _dedupe(queries)

    def _run_search_round(
        self,
        queries: list[str],
        plan: InvestigationPlan,
        warnings: list[str],
    ) -> list[SearchResult]:
        if self._provider is None:
            raise RuntimeError("No search provider configured for retrieval.")
        results: list[SearchResult] = []
        for query in queries:
            try:
                results.extend(
                    self._provider.search(
                        query=query,
                        time_window=plan.time_window,
                        source_types=plan.target_source_types,
                        limit=self._settings.RETRIEVER_MAX_RESULTS_PER_QUERY,
                    )
                )
            except Exception as exc:
                logger.warning("Search provider failed for query '%s': %s", query, exc)
                warnings.append(f"search_failed:{query}")
        deduped: list[SearchResult] = []
        seen_urls: set[str] = set()
        for result in sorted(results, key=lambda item: (item.rank, -(item.provider_score or 0.0))):
            normalized = self._normalize_url(result.url)
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)
            deduped.append(result)
        return deduped

    def _score_documents(self, documents: list[Document], plan: InvestigationPlan) -> list[tuple[Document, float]]:
        source_counts = Counter(doc.source_name for doc in documents)
        source_type_counts = Counter(doc.source_type for doc in documents)
        scored: list[tuple[Document, float]] = []
        plan_terms = {term.lower() for term in plan.entities}
        phrase = (plan.canonical_phrase or "").lower()
        target_source_types = {source_type.lower() for source_type in plan.target_source_types}
        for doc in documents:
            score = 0.0
            haystack = " ".join(filter(None, [doc.title, doc.snippet or "", doc.text])).lower()
            reason_tags: list[str] = []
            if phrase and phrase in haystack:
                score += 5.0
                reason_tags.append("exact_phrase")
            overlap = sum(1 for term in plan_terms if term in haystack)
            if overlap:
                score += min(overlap * 1.2, 4.0)
                reason_tags.append("query_overlap")
            if any(signal in haystack for signal in _COUNTER_SIGNAL_TERMS):
                score += 1.5
                reason_tags.append("counter_signal")
            if doc.published_at is not None:
                score += 0.5
                reason_tags.append("dated")
                if plan.intent in {"origin", "spread"} or _TIMELINE_OUTPUT in plan.requested_outputs:
                    score += 0.4
                    reason_tags.append("timeline_priority")
            if source_counts[doc.source_name] == 1:
                score += 0.8
                reason_tags.append("source_diversity")
            if doc.source_type in _TIMELINE_SOURCE_TYPES:
                score += 0.5
                reason_tags.append("timeline_useful")
            if doc.source_type.lower() in target_source_types:
                score += 0.8
                reason_tags.append("requested_source_type")
                if (
                    _SOURCE_DIVERSITY_OUTPUT in plan.requested_outputs
                    and source_type_counts[doc.source_type] <= 1
                ):
                    score += 0.6
                    reason_tags.append("scarce_source_type")
            if _RECEIPTS_OUTPUT in plan.requested_outputs and doc.snippet:
                score += 0.4
                reason_tags.append("receipt_snippet")
            if _GRAPH_OUTPUT in plan.requested_outputs and len(doc.entities) >= 2:
                score += 0.4
                reason_tags.append("graph_entities")
            if doc.duplicate_of_doc_id:
                score -= 2.0
                reason_tags.append("duplicate_penalty")
            metadata = dict(doc.metadata or {})
            metadata["retrieval_score"] = round(score, 3)
            metadata["retrieval_reason_tags"] = reason_tags
            doc.metadata = metadata
            scored.append((doc, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def _categorize_documents(
        self,
        scored_documents: list[tuple[Document, float]],
        plan: InvestigationPlan,
    ) -> dict[str, list[str]]:
        top_score = scored_documents[0][1] if scored_documents else 0.0
        high_cutoff = max(4.5, top_score * 0.65) if top_score else 4.5
        high_relevance: list[str] = []
        main_narrative: list[str] = []
        counter_candidates: list[str] = []
        context: list[str] = []
        phrase = (plan.canonical_phrase or "").lower()
        for doc, score in scored_documents:
            haystack = " ".join(filter(None, [doc.title, doc.snippet or "", doc.text])).lower()
            if score >= high_cutoff:
                high_relevance.append(doc.id)
            if phrase and phrase in haystack:
                main_narrative.append(doc.id)
            elif _COUNTER_OUTPUT in plan.requested_outputs and any(signal in haystack for signal in _COUNTER_SIGNAL_TERMS):
                counter_candidates.append(doc.id)
            else:
                context.append(doc.id)
        return {
            "high_relevance": high_relevance,
            "main_narrative": main_narrative,
            "counter_candidates": counter_candidates,
            "context": context,
        }

    def _build_coverage_summary(
        self,
        documents: list[Document],
        rounds: list[RetrievalRound],
        round_number: int,
        plan: InvestigationPlan,
    ) -> CoverageSummary:
        source_types = Counter(doc.source_type for doc in documents)
        phrase = (plan.canonical_phrase or "").lower()
        exact_phrase_hits = 0
        counter_hits = 0
        timeline_hits = 0
        for doc in documents:
            haystack = " ".join(filter(None, [doc.title, doc.snippet or "", doc.text])).lower()
            if phrase and phrase in haystack:
                exact_phrase_hits += 1
            if any(signal in haystack for signal in _COUNTER_SIGNAL_TERMS):
                counter_hits += 1
            if doc.published_at is not None:
                timeline_hits += 1
        return CoverageSummary(
            total_documents=len(documents),
            unique_sources=len({doc.source_name for doc in documents}),
            source_type_distribution=dict(source_types),
            has_counter_narrative_candidates=counter_hits > 0,
            has_timeline_coverage=timeline_hits >= max(2, len(documents) // 2) if documents else False,
            exact_phrase_hits=exact_phrase_hits,
            search_rounds_completed=round_number if documents or rounds else 0,
        )

    def _coverage_confidence(self, coverage: CoverageSummary) -> str:
        if (
            coverage.total_documents >= 8
            and coverage.unique_sources >= 5
            and coverage.exact_phrase_hits >= 2
            and coverage.has_timeline_coverage
        ):
            return "high"
        if coverage.total_documents >= 4 and coverage.unique_sources >= 3:
            return "medium"
        return "low"

    def _should_stop(
        self,
        documents: list[Document],
        coverage: CoverageSummary,
        new_documents: int,
        previous_doc_count: int,
        round_number: int,
        max_rounds: int,
        plan: InvestigationPlan,
    ) -> bool:
        if round_number >= max_rounds:
            return True
        enough_counter = (
            coverage.has_counter_narrative_candidates
            if _COUNTER_OUTPUT in plan.requested_outputs
            else True
        )
        enough_timeline = coverage.has_timeline_coverage if _TIMELINE_OUTPUT in plan.requested_outputs else True
        enough_diversity = (
            len(coverage.source_type_distribution) >= min(3, len(plan.target_source_types))
            if _SOURCE_DIVERSITY_OUTPUT in plan.requested_outputs
            else True
        )
        if coverage.total_documents >= 8 and coverage.unique_sources >= 5 and enough_timeline and enough_counter and enough_diversity:
            return True
        if new_documents == 0:
            return True
        if previous_doc_count and len(documents) - previous_doc_count <= 1:
            return True
        return False

    def _find_scarce_requested_source_type(
        self,
        documents: list[Document],
        target_source_types: list[str],
    ) -> str | None:
        if not target_source_types:
            return None
        current_counts = Counter(doc.source_type for doc in documents)
        for source_type in target_source_types:
            if current_counts[source_type] == 0:
                return source_type
        return None

    def _detect_duplicates(self, documents: list[Document]) -> list[DuplicateCandidate]:
        duplicates: list[DuplicateCandidate] = []
        for left_index, left in enumerate(documents):
            for right in documents[left_index + 1 :]:
                similarity = self._doc_similarity(left, right)
                if similarity < 0.92:
                    continue
                reason = "same_url" if self._normalize_url(left.url) == self._normalize_url(right.url) else "similar_title_text"
                duplicates.append(
                    DuplicateCandidate(
                        left_doc_id=left.id,
                        right_doc_id=right.id,
                        similarity_score=round(similarity, 3),
                        reason=reason,
                    )
                )
                if similarity >= 0.98:
                    right.duplicate_of_doc_id = left.id
        return duplicates

    def _doc_similarity(self, left: Document, right: Document) -> float:
        if self._normalize_url(left.url) == self._normalize_url(right.url):
            return 1.0
        left_text = f"{left.title} {left.snippet or ''} {left.text[:800]}"
        right_text = f"{right.title} {right.snippet or ''} {right.text[:800]}"
        return SequenceMatcher(None, left_text.lower(), right_text.lower()).ratio()

    def _normalize_url(self, url: str) -> str:
        return re.sub(r"/+$", "", url.strip().lower())


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        output.append(normalized)
    return output
