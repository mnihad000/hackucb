"""
GDELT Project v2 DOC API ingestion.

No API key required. Free public access.
Returns articles with title, URL, domain, timestamp, language, and sourcecountry.
Full text is not included in artlist mode, so title/snippet stand in as text.
"""

import hashlib
from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Literal

import httpx

from config import get_settings
from models.document import Document

SourceType = Literal[
    "forum", "blog", "local_news", "national_news", "commentary", "speech_transcript"
]

_BLOG_DOMAINS = {
    "substack.com", "medium.com", "wordpress.com", "blogspot.com",
    "tumblr.com", "ghost.io", "beehiiv.com",
}

_NATIONAL_DOMAINS = {
    "nytimes.com", "washingtonpost.com", "reuters.com", "apnews.com",
    "cnn.com", "foxnews.com", "nbcnews.com", "cbsnews.com", "abcnews.go.com",
    "bbc.com", "bbc.co.uk", "politico.com", "thehill.com", "axios.com",
    "theguardian.com", "bloomberg.com", "wsj.com", "ft.com",
    "npr.org", "pbs.org", "vox.com", "slate.com", "salon.com",
    "nationalreview.com", "theatlantic.com", "newyorker.com",
}

_LOCAL_KEYWORDS = {
    "gazette", "herald", "tribune", "daily", "observer", "register",
    "dispatch", "courier", "chronicle", "journal", "bulletin", "sentinel",
    "beacon", "pilot", "record", "times-", "-times", "patch.com",
}

_COMMENTARY_DOMAINS = {
    "reason.com", "thedispatch.com", "commondreams.org", "motherjones.com",
    "jacobin.com", "federalist.com", "breitbart.com", "dailykos.com",
}


def _classify_source(domain: str) -> SourceType:
    domain_lower = domain.lower()
    if any(b in domain_lower for b in _BLOG_DOMAINS):
        return "blog"
    if domain_lower in _COMMENTARY_DOMAINS:
        return "commentary"
    if domain_lower in _NATIONAL_DOMAINS:
        return "national_news"
    if any(kw in domain_lower for kw in _LOCAL_KEYWORDS):
        return "local_news"
    return "national_news"


def _parse_gdelt_date(raw: str) -> datetime:
    """Parse GDELT seendate like '20260601T120000Z' or '20260601120000'."""
    raw = raw.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S", "%Y%m%dT%H%M%S"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def _normalize_language(language: str | None) -> str | None:
    if not language:
        return None
    return language.strip().lower()


def _infer_content_type(source_type: SourceType) -> str:
    if source_type == "commentary":
        return "opinion"
    if source_type == "blog":
        return "analysis"
    return "article"


def _infer_geographic_scope(source_type: SourceType, source_country: str | None) -> str:
    if source_type == "local_news":
        return "local"
    if source_type in {"national_news", "commentary"}:
        return (
            "national"
            if (source_country or "").strip().lower() in {"united states", "us", "usa"}
            else "international"
        )
    return "unknown"


def _extract_phrases(title: str, query: str) -> list[str]:
    """Extract candidate phrases from title by checking query term overlap."""
    phrases: list[str] = []
    title_lower = title.lower()
    query_terms = [t.strip() for t in query.split() if len(t) > 3]

    words = title_lower.split()
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i + 1]}"
        if any(term in bigram for term in query_terms):
            phrases.append(bigram)

    if len(title) < 80:
        phrases.append(title.lower())

    return list(dict.fromkeys(phrases))[:4]


def _doc_id(url: str, index: int) -> str:
    return "gdelt_" + hashlib.md5(url.encode()).hexdigest()[:8] if url else f"gdelt_{index:04d}"


def build_timeline(documents: list[Document]) -> list[dict]:
    daily: dict[str, int] = defaultdict(int)
    for doc in documents:
        if doc.published_at is None:
            continue
        daily[doc.published_at.strftime("%Y-%m-%d")] += 1
    return [{"date": day, "count": daily[day]} for day in sorted(daily.keys())]


def build_first_observed_label(documents: list[Document]) -> dict | None:
    dated_documents = [doc for doc in documents if doc.published_at is not None]
    if not dated_documents:
        return None

    first_doc = min(dated_documents, key=lambda doc: doc.published_at)
    return {
        "label": "first observed in our dataset",
        "doc_id": first_doc.id,
        "title": first_doc.title,
        "source_name": first_doc.source_name,
        "source_type": first_doc.source_type,
        "published_at": first_doc.published_at,
        "url": first_doc.url,
        "note": "This is the earliest article returned in our retrieved dataset, not a claim about true origin.",
    }


class GDELTIngestion:
    def __init__(self) -> None:
        self._settings = get_settings()

    def fetch_articles(
        self,
        query: str,
        start_dt: datetime,
        end_dt: datetime,
        max_records: int | None = None,
    ) -> list[Document]:
        max_records = max_records or self._settings.GDELT_MAX_RECORDS
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_records,
            "sort": "datedesc",
            "startdatetime": start_dt.strftime("%Y%m%d%H%M%S"),
            "enddatetime": end_dt.strftime("%Y%m%d%H%M%S"),
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "RhetoriQ/0.1 (backend GDELT DOC 2.0 integration)",
        }

        with httpx.Client(timeout=30, headers=headers) as client:
            for attempt in range(2):
                response = client.get(self._settings.GDELT_BASE_URL, params=params)
                if response.status_code != 429:
                    response.raise_for_status()
                    break
                if attempt == 0:
                    time.sleep(2)
                    continue
                response.raise_for_status()

        data = response.json()
        articles = data.get("articles") or []
        documents = [self._map_article(article, query, index) for index, article in enumerate(articles)]
        return sorted(documents, key=lambda doc: doc.published_at or datetime.max.replace(tzinfo=timezone.utc))

    def _map_article(self, article: dict, query: str, index: int) -> Document:
        url = article.get("url", "")
        domain = article.get("domain", "")
        title = article.get("title", "Untitled")
        raw_date = article.get("seendate", "")
        language = _normalize_language(article.get("language"))
        source_country = article.get("sourcecountry")
        published_at = _parse_gdelt_date(raw_date) if raw_date else datetime.now(timezone.utc)
        source_type = _classify_source(domain)
        phrases = _extract_phrases(title, query)
        collected_at = datetime.now(timezone.utc)

        return Document(
            id=_doc_id(url, index),
            source_id=f"domain:{domain.lower()}" if domain else None,
            source_name=domain or "Unknown",
            source_type=source_type,
            url=url,
            title=title,
            published_at=published_at,
            collected_at=collected_at,
            text=title,
            snippet=title,
            language=language,
            content_type=_infer_content_type(source_type),
            geographic_scope=_infer_geographic_scope(source_type, source_country),
            entities=[],
            phrases=phrases,
            metadata={
                "dataset": "gdelt_doc_2",
                "gdelt_query": query,
                "gdelt_mode": "artlist",
                "gdelt_format": "json",
                "gdelt_seendate": raw_date or None,
                "domain": domain or None,
                "source_country": source_country,
            },
        )
