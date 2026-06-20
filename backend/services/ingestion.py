"""
Ingestion coordinator.

Sources:
  GDELT  — news articles, national/local/blog classification, no key required
  HN     — forum layer (Hacker News), no key required

Both results are saved to the live DocumentStore and immediately available
to all narrative/investigate endpoints via get_merged_documents().
"""

from datetime import datetime

from models.document import Document
from services.document_store import live_store
from services.gdelt import GDELTIngestion
from services.hn_ingestion import HNIngestion


class IngestionCoordinator:
    def __init__(self) -> None:
        self._gdelt = GDELTIngestion()
        self._hn = HNIngestion()

    def ingest(
        self,
        query: str,
        start_dt: datetime,
        end_dt: datetime,
        include_hn: bool = True,
        hn_num_results: int = 50,
    ) -> dict:
        errors: list[str] = []

        gdelt_docs: list[Document] = []
        try:
            gdelt_docs = self._gdelt.fetch_articles(query, start_dt, end_dt)
            live_store.save_batch(gdelt_docs)
        except Exception as exc:
            errors.append(f"GDELT: {exc}")

        hn_docs: list[Document] = []
        if include_hn:
            try:
                hn_docs = self._hn.fetch_stories(
                    query, start_dt, end_dt, num_results=hn_num_results
                )
                live_store.save_batch(hn_docs)
            except Exception as exc:
                errors.append(f"HN: {exc}")

        return {
            "query": query,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "gdelt_ingested": len(gdelt_docs),
            "hn_ingested": len(hn_docs),
            "total_ingested": len(gdelt_docs) + len(hn_docs),
            "store_total": live_store.count(),
            "errors": errors,
        }


def get_merged_documents(demo_docs: list[Document]) -> list[Document]:
    """
    Returns live store documents merged with the demo corpus.
    Live documents take precedence (deduplicated by id).
    Demo corpus fills gaps when the store is empty.
    """
    live = live_store.get_all()
    if not live:
        return demo_docs
    live_ids = {d.id for d in live}
    return live + [d for d in demo_docs if d.id not in live_ids]
