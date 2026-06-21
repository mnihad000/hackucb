import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import get_settings
from models.investigation import (
    AgentDebateResult,
    InvestigationPlan,
    InvestigationPlanTimeWindow,
)
from services.band_room import BandRoomSync


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        query_text="Trace the hidden energy tax story.",
        topic="hidden energy tax",
        canonical_phrase="hidden energy tax",
        intent="spread",
        entities=["energy", "tax"],
        search_queries=["hidden energy tax"],
        semantic_queries=["trace hidden energy tax spread"],
        target_source_types=["local_news", "national_news"],
        requested_outputs=["receipts", "agent_debate"],
        time_window=InvestigationPlanTimeWindow(label="all_time"),
        retrieval_mode="broad",
        risk_notes=[],
        uncertainty_requirements=[],
    )


def _debate() -> AgentDebateResult:
    return AgentDebateResult(
        investigation_id="inv_band",
        plan_snapshot=_plan(),
        analyst_position="The analyst finds a visible spread pattern.",
        skeptic_response="The skeptic says the evidence does not prove coordination.",
        receipts_check="Receipts support two claims and soften one.",
        counter_narrative_note="A corrective counter-frame is present.",
        safety_grounding_decision="Use cautious language for contested claims.",
        final_language_decision="Use first-observed-in-dataset wording.",
        rejected_claims=[],
        softened_claims=[],
        limitations=[],
        confidence_score=0.7,
        confidence_label="medium",
    )


def test_band_sync_reports_not_configured(monkeypatch):
    # Override with empty strings so pydantic-settings ignores the .env file values
    monkeypatch.setenv("BAND_API_KEY", "")
    monkeypatch.setenv("BAND_AGENT_ID", "")
    get_settings.cache_clear()

    sync = BandRoomSync()
    result = sync.sync_debate(_debate())

    assert result.status == "not_configured"
    assert result.message_count == 0


def test_band_sync_posts_agent_events_with_fake_rest_client(monkeypatch):
    monkeypatch.setenv("BAND_API_KEY", "test-key")
    monkeypatch.setenv("BAND_AGENT_ID", "agent_rhetoriq")
    monkeypatch.delenv("BAND_ROOM_ID", raising=False)
    get_settings.cache_clear()

    events = []

    class _Chats:
        async def create_agent_chat(self, *, chat, request_options=None):
            return SimpleNamespace(data=SimpleNamespace(id="chat_inv_band"))

    class _Events:
        async def create_agent_chat_event(self, chat_id, *, event, request_options=None):
            events.append(
                {
                    "chat_id": chat_id,
                    "content": event.content,
                    "metadata": event.metadata,
                }
            )
            return SimpleNamespace(data=SimpleNamespace(id=f"event_{len(events)}"))

    class _Rest:
        agent_api_chats = _Chats()
        agent_api_events = _Events()

    class _Link:
        rest = _Rest()

    def _fake_link_factory(**kwargs):
        assert kwargs["agent_id"] == "agent_rhetoriq"
        assert kwargs["api_key"] == "test-key"
        return _Link()

    sync = BandRoomSync(link_factory=_fake_link_factory)
    result = sync.sync_debate(_debate())
    updated = sync.apply_sync_result(_debate(), result)

    assert result.status == "synced"
    assert result.chat_id == "chat_inv_band"
    assert result.message_count == 6
    assert updated.band_sync_status == "synced"
    assert updated.band_chat_id == "chat_inv_band"
    assert [event["metadata"]["agent_role"] for event in events] == [
        "Analyst Agent",
        "Skeptic Agent",
        "Receipts Agent",
        "Counter-Narrative Agent",
        "Safety Agent",
        "Final Language Agent",
    ]


def test_band_stage_events_reuse_investigation_chat_with_fake_rest_client(monkeypatch):
    monkeypatch.setenv("BAND_API_KEY", "test-key")
    monkeypatch.setenv("BAND_AGENT_ID", "agent_rhetoriq")
    monkeypatch.delenv("BAND_ROOM_ID", raising=False)
    get_settings.cache_clear()

    chats = []
    events = []

    class _Chats:
        async def create_agent_chat(self, *, chat, request_options=None):
            chats.append(chat)
            return SimpleNamespace(data=SimpleNamespace(id=f"chat_{len(chats)}"))

    class _Events:
        async def create_agent_chat_event(self, chat_id, *, event, request_options=None):
            events.append(
                {
                    "chat_id": chat_id,
                    "content": event.content,
                    "metadata": event.metadata,
                }
            )
            return SimpleNamespace(data=SimpleNamespace(id=f"event_{len(events)}"))

    class _Rest:
        agent_api_chats = _Chats()
        agent_api_events = _Events()

    class _Link:
        rest = _Rest()

    sync = BandRoomSync(link_factory=lambda **kwargs: _Link())

    first = sync.sync_stage_event(
        investigation_id="inv_band",
        stage="retrieval",
        role="Retriever Agent",
        content="Retrieved 8 documents across 5 sources.",
        metadata={"confidence_label": "medium"},
    )
    second = sync.sync_stage_event(
        investigation_id="inv_band",
        stage="timeline",
        role="Timeline Agent",
        content="Built a timeline with 6 events.",
        metadata={"confidence_label": "high"},
    )

    assert first.status == "synced"
    assert second.status == "synced"
    assert first.chat_id == "chat_1"
    assert second.chat_id == "chat_1"
    assert len(chats) == 1
    assert [event["metadata"]["stage"] for event in events] == ["retrieval", "timeline"]
    assert all(event["metadata"]["event_type"] == "stage_update" for event in events)
