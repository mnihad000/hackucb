from datetime import datetime, timezone
from types import SimpleNamespace

from models.document import Document
from services.source_verification_builder import build_source_verification, verification_map_from_result


def _docs() -> list[Document]:
    return [
        Document(
            id="doc_1",
            source_id="domain:example.com",
            source_name="Example News",
            source_type="local_news",
            url="https://example.com/story",
            title="Original story",
            published_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            collected_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
            text="A claim appears in an original story.",
            snippet="A claim appears in an original story.",
            language="en",
            content_type="article",
            geographic_scope="local",
            entities=[],
            phrases=[],
            metadata={},
        ),
        Document(
            id="doc_2",
            source_id="domain:example.org",
            source_name="Example Wire",
            source_type="national_news",
            url="https://example.org/wire",
            title="Wire follow-up",
            published_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
            collected_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
            text="A follow-up story repeats the claim.",
            snippet="A follow-up story repeats the claim.",
            language="en",
            content_type="article",
            geographic_scope="national",
            entities=[],
            phrases=[],
            metadata={},
        ),
    ]


class _FakeAgent:
    def verify_documents(self, documents: list[Document]):
        receipts = [
            SimpleNamespace(
                source_id=documents[0].id,
                url=documents[0].url,
                verified_status="verified",
                backend="browserbase",
                live_title="Original story",
                stored_title=documents[0].title,
                evidence_snippet=documents[0].snippet,
                support_reason="Live page title and snippet matched the retrieved document.",
                checked_at="2026-06-21T10:00:00+00:00",
                error=None,
            )
        ]
        if len(documents) > 1:
            receipts.append(
                {
                    "source_id": documents[1].id,
                    "url": documents[1].url,
                    "verified_status": "source_updated",
                    "backend": "httpx_fallback",
                    "live_title": "Updated wire follow-up",
                    "stored_title": documents[1].title,
                    "evidence_snippet": documents[1].snippet,
                    "support_reason": "Title changed after retrieval.",
                    "checked_at": "2026-06-21T10:00:01+00:00",
                    "error": None,
                }
            )
        return receipts


def test_build_source_verification_checks_cited_docs_and_counts_backends():
    result = build_source_verification(
        "inv_browserbase",
        _docs(),
        cited_document_ids=["doc_1", "doc_2", "missing_doc"],
        agent=_FakeAgent(),
    )

    assert [receipt.document_id for receipt in result.receipts] == ["doc_1", "doc_2"]
    assert result.verified_count == 1
    assert result.metadata_mismatch_count == 1
    assert result.browserbase_verified_count == 1
    assert result.fallback_checked_count == 1
    assert result.backend_counts == {"browserbase": 1, "httpx_fallback": 1}
    assert "missing_doc" not in verification_map_from_result(result)
    assert verification_map_from_result(result) == {
        "doc_1": "verified",
        "doc_2": "metadata_mismatch",
    }
    assert any("not present" in limitation for limitation in result.limitations)
    assert any("HTTP fallback" in limitation for limitation in result.limitations)


def test_build_source_verification_can_limit_uncited_document_set():
    result = build_source_verification(
        "inv_browserbase",
        _docs(),
        max_documents=1,
        agent=_FakeAgent(),
    )

    assert [receipt.document_id for receipt in result.receipts] == ["doc_1"]
    assert result.status_counts == {"verified": 1}
