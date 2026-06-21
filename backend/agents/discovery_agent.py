from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from urllib.parse import urlparse

from models.investigation import InvestigationPlan, InvestigationPlanTimeWindow, RawPage, SearchResult
from models.trending import DiscoveryQuery, DiscoveryRunStats
from services.document_normalizer import DocumentNormalizer
from services.page_fetcher import HttpPageFetcher
from services.search_provider import MultiSearchProvider


DISCOVERY_HEADLINES = [
    "breaking news today",
    "latest politics",
    "world news today",
    "business news today",
    "technology news today",
    "major policy announcement",
]
ENRICHMENT_HEADLINES = [
    "official statement today",
    "public reaction today",
    "fact check latest news",
]

_DEFAULT_SOURCE_TYPES = [
    "blog",
    "local_news",
    "national_news",
    "commentary",
    "official_statement",
    "community_post",
]


@dataclass
class DiscoveryCandidate:
    search_result: SearchResult
    raw_page: RawPage
    document_plan: InvestigationPlan


@dataclass
class DiscoveryBatchResult:
    queries: list[DiscoveryQuery]
    candidates: list[DiscoveryCandidate]
    warnings: list[str]
    stats: DiscoveryRunStats


class DiscoveryAgent:
    def __init__(
        self,
        *,
        search_provider: MultiSearchProvider | None = None,
        page_fetcher: HttpPageFetcher | None = None,
        normalizer: DocumentNormalizer | None = None,
    ) -> None:
        self._provider = search_provider or MultiSearchProvider()
        self._fetcher = page_fetcher or HttpPageFetcher()
        self._normalizer = normalizer or DocumentNormalizer()

    def build_queries(
        self,
        *,
        prior_topics: list[str],
        is_reseed: bool,
    ) -> list[DiscoveryQuery]:
        normalized: list[DiscoveryQuery] = []
        seen: set[str] = set()
        for query in DISCOVERY_HEADLINES:
            value = query.strip()
            lowered = value.lower()
            if not value or lowered in seen:
                continue
            seen.add(lowered)
            normalized.append(DiscoveryQuery(query=value, provider_role="discovery", topic_seed=value))

        for query in ENRICHMENT_HEADLINES:
            value = query.strip()
            lowered = value.lower()
            if not value or lowered in seen:
                continue
            seen.add(lowered)
            normalized.append(
                DiscoveryQuery(
                    query=value,
                    provider_role="enrichment",
                    topic_seed=value,
                )
            )

        prior_limit = 6 if is_reseed else 4
        for topic in prior_topics[:prior_limit]:
            value = topic.strip()
            lowered = value.lower()
            if not value:
                continue
            exact = f"\"{value}\""
            if exact.lower() not in seen:
                seen.add(exact.lower())
                normalized.append(DiscoveryQuery(query=exact, provider_role="discovery", topic_seed=value))
            latest = f"{value} latest"
            if latest.lower() not in seen:
                seen.add(latest.lower())
                normalized.append(DiscoveryQuery(query=latest, provider_role="enrichment", topic_seed=value))
            official = f"{value} official statement"
            if official.lower() not in seen:
                seen.add(official.lower())
                normalized.append(DiscoveryQuery(query=official, provider_role="enrichment", topic_seed=value))
        return normalized

    def discover(
        self,
        *,
        prior_topics: list[str],
        is_reseed: bool,
        max_results_per_query: int = 6,
    ) -> DiscoveryBatchResult:
        queries = self.build_queries(prior_topics=prior_topics, is_reseed=is_reseed)
        stats = DiscoveryRunStats(query_count=len(queries))
        warnings: list[str] = []
        candidates: list[DiscoveryCandidate] = []
        seen_urls: set[str] = set()

        time_window = InvestigationPlanTimeWindow(label="recent")
        for query in queries:
            try:
                if query.provider_role == "discovery":
                    results = self._provider.search_discovery(
                        query.query,
                        time_window,
                        _DEFAULT_SOURCE_TYPES,
                        max_results_per_query,
                    )
                else:
                    results = self._provider.search_enrichment(
                        query.query,
                        time_window,
                        _DEFAULT_SOURCE_TYPES,
                        max_results_per_query,
                    )
            except Exception as exc:
                warnings.append(f"search_failed:{query.provider_role}:{query.query}:{exc}")
                continue

            stats.result_count += len(results)
            for result in results:
                normalized_url = self._normalize_url(result.url)
                if normalized_url in seen_urls:
                    stats.duplicate_documents += 1
                    continue
                fetched = self._fetcher.fetch(result.url)
                if not hasattr(fetched, "html"):
                    warnings.append(f"fetch_failed:{result.url}")
                    continue
                seen_urls.add(normalized_url)
                stats.fetched_pages += 1
                candidates.append(
                    DiscoveryCandidate(
                        search_result=result,
                        raw_page=fetched,
                        document_plan=self._build_plan(query.topic_seed, result),
                    )
                )
                stats.accepted_documents += 1

        return DiscoveryBatchResult(
            queries=queries,
            candidates=candidates,
            warnings=warnings,
            stats=stats,
        )

    def normalize_candidate(self, candidate: DiscoveryCandidate):
        return self._normalizer.normalize(
            candidate.raw_page,
            candidate.document_plan,
            candidate.search_result,
        )

    def _build_plan(self, topic_seed: str, result: SearchResult) -> InvestigationPlan:
        phrase = self._canonical_phrase(topic_seed, result)
        entities = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", phrase)]
        return InvestigationPlan(
            query_text=topic_seed,
            topic=topic_seed,
            canonical_phrase=phrase,
            intent="general investigation",
            entities=list(dict.fromkeys(entities))[:8],
            search_queries=[topic_seed, result.query],
            semantic_queries=[f"Track the civic narrative around {phrase}"],
            target_source_types=_DEFAULT_SOURCE_TYPES,
            requested_outputs=["timeline", "source_diversity"],
            time_window=InvestigationPlanTimeWindow(label="recent"),
            retrieval_mode="broad",
            risk_notes=["Discovery pass for trending candidates; ranking remains deterministic."],
            uncertainty_requirements=["Do not treat search ranking as trend evidence without stored history."],
        )

    def _canonical_phrase(self, topic_seed: str, result: SearchResult) -> str:
        title = result.title.lower()
        title_tokens = re.findall(r"[a-z0-9][a-z0-9\-]{2,}", title)
        seed_tokens = re.findall(r"[a-z0-9][a-z0-9\-]{2,}", topic_seed.lower())
        if seed_tokens:
            for index in range(len(title_tokens) - len(seed_tokens) + 1):
                if title_tokens[index : index + len(seed_tokens)] != seed_tokens:
                    continue
                phrase_tokens = title_tokens[index : min(len(title_tokens), index + max(3, len(seed_tokens) + 2))]
                if len(set(phrase_tokens)) > 1:
                    return " ".join(phrase_tokens)
        if len(title_tokens) >= 3:
            return " ".join(title_tokens[: min(4, len(title_tokens))])
        if topic_seed.lower() in title:
            return topic_seed.lower()
        return " ".join(title_tokens) if title_tokens else topic_seed.lower()

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url.strip())
        path = re.sub(r"/+$", "", parsed.path or "")
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"

