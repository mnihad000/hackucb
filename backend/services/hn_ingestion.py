"""
Hacker News ingestion via Algolia HN Search API.

No API key. No signup. Free public access.
Returns stories matching a query filtered by date range.

HN is the forum layer of the source type pyramid, same position as Reddit.
Stories with url=None are Ask HN / Show HN self-posts — we use the
HN item URL as the canonical source link.

Points are stored as entities["hn_points"] proxy for engagement signal.
Swap-in notes:
- Add ?page=1, ?page=2 iteration for deeper history.
- Add tags=comment to also pull comment-level phrase signals.
"""

import hashlib
from datetime import datetime, timezone

import httpx

from config import get_settings
from models.document import Document

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


def _doc_id(object_id: str) -> str:
    return f"hn_{object_id}"


def _hn_url(object_id: str) -> str:
    return f"https://news.ycombinator.com/item?id={object_id}"


def _extract_phrases(title: str, query: str) -> list[str]:
    title_lower = title.lower()
    phrases: list[str] = []
    query_terms = [t.strip() for t in query.split() if len(t) > 3]
    words = title_lower.split()
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i + 1]}"
        if any(term in bigram for term in query_terms):
            phrases.append(bigram)
    if len(title) < 80:
        phrases.append(title_lower)
    return list(dict.fromkeys(phrases))[:4]


def _parse_published_at(hit: dict) -> datetime:
    ts = hit.get("created_at_i")
    if ts:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    raw = hit.get("created_at", "")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


class HNIngestion:
    def __init__(self) -> None:
        self._settings = get_settings()

    def fetch_stories(
        self,
        query: str,
        start_dt: datetime,
        end_dt: datetime | None = None,
        num_results: int = 50,
    ) -> list[Document]:
        start_ts = int(start_dt.timestamp())
        numeric_filters = f"created_at_i>{start_ts}"
        if end_dt:
            numeric_filters += f",created_at_i<{int(end_dt.timestamp())}"

        params = {
            "query": query,
            "tags": "story",
            "numericFilters": numeric_filters,
            "hitsPerPage": min(num_results, 100),
        }

        with httpx.Client(timeout=30) as client:
            response = client.get(HN_SEARCH_URL, params=params)
            response.raise_for_status()

        hits = response.json().get("hits") or []
        return [self._map_hit(hit, query) for hit in hits]

    def _map_hit(self, hit: dict, query: str) -> Document:
        object_id = str(hit.get("objectID", ""))
        url = hit.get("url") or _hn_url(object_id)
        title = hit.get("title") or "Untitled"
        author = hit.get("author") or "unknown"
        points = hit.get("points") or 0
        num_comments = hit.get("num_comments") or 0

        return Document(
            id=_doc_id(object_id),
            source_name="Hacker News",
            source_type="forum",
            url=url,
            title=title,
            published_at=_parse_published_at(hit),
            text=title,
            entities=[author, f"hn_points:{points}", f"hn_comments:{num_comments}"],
            phrases=_extract_phrases(title, query),
        )
