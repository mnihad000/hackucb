from __future__ import annotations

from abc import ABC, abstractmethod

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


def build_search_provider() -> SearchProvider:
    settings = get_settings()
    provider = settings.SEARCH_PROVIDER.lower()
    if provider == "tavily":
        return TavilySearchProvider()
    raise RuntimeError(f"Unsupported search provider: {settings.SEARCH_PROVIDER}")
