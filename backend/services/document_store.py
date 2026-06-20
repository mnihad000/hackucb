"""
In-memory live document store.

Shape mirrors a Redis hash: {doc_id: Document}.
Swap-in: replace _LIVE_STORE writes with redis.hset / reads with redis.hget.
"""

from models.document import Document

_LIVE_STORE: dict[str, Document] = {}


class DocumentStore:
    def save(self, doc: Document) -> None:
        _LIVE_STORE[doc.id] = doc

    def save_batch(self, docs: list[Document]) -> None:
        for doc in docs:
            _LIVE_STORE[doc.id] = doc

    def get(self, doc_id: str) -> Document | None:
        return _LIVE_STORE.get(doc_id)

    def get_all(self) -> list[Document]:
        return list(_LIVE_STORE.values())

    def count(self) -> int:
        return len(_LIVE_STORE)

    def clear(self) -> None:
        _LIVE_STORE.clear()

    def ids(self) -> list[str]:
        return list(_LIVE_STORE.keys())


# Module-level singleton — shared across the app process
live_store = DocumentStore()
