from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import urlparse

import httpx

from config import get_settings
from models.investigation import InvestigationPlanTimeWindow, SearchResult


class SearchProvider(ABC):
    name: str

    @abstractmethod
    def search(
        self,
        query: str,
        time_window: InvestigationPlanTimeWindow,
        source_types: list[str],
        limit: int,
    ) -> list[SearchResult]:
        raise NotImplementedError


class TavilySearchProvider(SearchProvider):
    name = "tavily"
    _url = "https://api.tavily.com/search"

    def __init__(self) -> None:
        self._settings = get_settings()
        if not self._settings.TAVILY_API_KEY:
            raise RuntimeError("TavilySearchProvider requires TAVILY_API_KEY.")

    def search(
        self,
        query: str,
        time_window: InvestigationPlanTimeWindow,
        source_types: list[str],
        limit: int,
    ) -> list[SearchResult]:
        payload = {
            "api_key": self._settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": limit,
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False,
            "topic": "general",
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self._url, json=payload)
            response.raise_for_status()

        data = response.json()
        raw_results = data.get("results") or []
        normalized: list[SearchResult] = []
        for index, item in enumerate(raw_results, start=1):
            url = item.get("url")
            title = item.get("title")
            if not url or not title:
                continue
            normalized.append(
                SearchResult(
                    query=query,
                    title=title,
                    url=url,
                    snippet=item.get("content"),
                    rank=index,
                    provider=self.name,
                    provider_score=item.get("score"),
                    metadata={
                        "time_window_label": time_window.label,
                        "target_source_types": source_types,
                    },
                )
            )
        return normalized


class SerpApiSearchProvider(SearchProvider):
    name = "serpapi"
    _url = "https://serpapi.com/search.json"

    def __init__(self) -> None:
        self._settings = get_settings()
        if not self._settings.SERPAPI_API_KEY:
            raise RuntimeError("SerpApiSearchProvider requires SERPAPI_API_KEY.")

    def search(
        self,
        query: str,
        time_window: InvestigationPlanTimeWindow,
        source_types: list[str],
        limit: int,
    ) -> list[SearchResult]:
        params = {
            "api_key": self._settings.SERPAPI_API_KEY,
            "engine": "google_news",
            "q": query,
            "num": max(10, min(limit, 100)),
            "hl": "en",
            "gl": "us",
        }
        if time_window.label == "today":
            params["tbs"] = "qdr:d"
        elif time_window.label in {"recent", "this_week"}:
            params["tbs"] = "qdr:w"
        elif time_window.label == "this_month":
            params["tbs"] = "qdr:m"

        with httpx.Client(timeout=30) as client:
            response = client.get(self._url, params=params)
            response.raise_for_status()

        data = response.json()
        raw_results = data.get("news_results") or data.get("organic_results") or []
        normalized: list[SearchResult] = []
        for index, item in enumerate(raw_results[:limit], start=1):
            url = item.get("link") or item.get("url")
            title = item.get("title")
            if not url or not title:
                continue
            source_name = None
            source = item.get("source")
            if isinstance(source, dict):
                source_name = source.get("name")
            elif isinstance(source, str):
                source_name = source
            normalized.append(
                SearchResult(
                    query=query,
                    title=title,
                    url=url,
                    snippet=item.get("snippet"),
                    rank=index,
                    provider=self.name,
                    provider_score=round(max(0.0, 1.0 - ((index - 1) * 0.06)), 3),
                    metadata={
                        "time_window_label": time_window.label,
                        "target_source_types": source_types,
                        "source_name_hint": source_name,
                    },
                )
            )
        return normalized


class MultiSearchProvider:
    def __init__(
        self,
        discovery_provider: SearchProvider | None = None,
        enrichment_provider: SearchProvider | None = None,
    ) -> None:
        self.discovery_provider = discovery_provider or SerpApiSearchProvider()
        self.enrichment_provider = enrichment_provider or TavilySearchProvider()

    def search_discovery(
        self,
        query: str,
        time_window: InvestigationPlanTimeWindow,
        source_types: list[str],
        limit: int,
    ) -> list[SearchResult]:
        return self.discovery_provider.search(query, time_window, source_types, limit)

    def search_enrichment(
        self,
        query: str,
        time_window: InvestigationPlanTimeWindow,
        source_types: list[str],
        limit: int,
    ) -> list[SearchResult]:
        return self.enrichment_provider.search(query, time_window, source_types, limit)

    @property
    def provider_mix(self) -> dict[str, str]:
        return {
            "discovery": self.discovery_provider.name,
            "enrichment": self.enrichment_provider.name,
        }


def build_search_provider() -> SearchProvider:
    settings = get_settings()
    provider = settings.SEARCH_PROVIDER.lower()
    if provider == "tavily":
        return TavilySearchProvider()
    if provider == "serpapi":
        return SerpApiSearchProvider()
    raise RuntimeError(f"Unsupported search provider: {settings.SEARCH_PROVIDER}")


def source_name_from_url(url: str) -> str:
    return urlparse(url).netloc.lower()

