from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable

from config import get_settings
from models.investigation import AgentDebateResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BandSyncResult:
    chat_id: str | None
    status: str
    message_count: int = 0
    error: str | None = None


class BandRoomSync:
    """
    Pushes RhetoriQ's observable agent debate into a Band chat.

    The local debate artifact remains the source of truth. Band is a sponsor
    collaboration layer: Analyst, Skeptic, Receipts, Counter-Narrative, Safety,
    and Final Language outputs are posted as room events so judges can see the
    agents communicating in a shared investigation room.
    """

    def __init__(
        self,
        *,
        link_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._settings = get_settings()
        self._link_factory = link_factory

    def configured(self) -> bool:
        return bool(self._settings.BAND_API_KEY and self._settings.BAND_AGENT_ID)

    def sync_debate(self, debate: AgentDebateResult) -> BandSyncResult:
        if not self.configured():
            return BandSyncResult(
                chat_id=None,
                status="not_configured",
                error="BAND_API_KEY and BAND_AGENT_ID are required.",
            )

        try:
            asyncio.get_running_loop()
            return BandSyncResult(
                chat_id=None,
                status="failed",
                error="Band sync was called from an active event loop; use sync_debate_async instead.",
            )
        except RuntimeError:
            return asyncio.run(self.sync_debate_async(debate))

    async def sync_debate_async(self, debate: AgentDebateResult) -> BandSyncResult:
        if not self.configured():
            return BandSyncResult(
                chat_id=None,
                status="not_configured",
                error="BAND_API_KEY and BAND_AGENT_ID are required.",
            )

        try:
            link = self._build_link()
            rest = link.rest
            request_options = self._request_options()
            chat_id = self._settings.BAND_ROOM_ID or await self._create_chat(
                rest,
                debate.investigation_id,
                request_options,
            )

            messages = self._debate_messages(debate)
            sent = 0
            for role, content in messages:
                await self._create_event(
                    rest,
                    chat_id,
                    role,
                    content,
                    debate,
                    request_options,
                    order=sent + 1,
                )
                sent += 1

            logger.info(
                "Synced %d RhetoriQ agent debate messages to Band chat %s",
                sent,
                chat_id,
            )
            return BandSyncResult(chat_id=chat_id, status="synced", message_count=sent)
        except Exception as exc:
            logger.warning("Band debate sync failed: %s", exc)
            return BandSyncResult(chat_id=None, status="failed", error=str(exc))

    def apply_sync_result(
        self,
        debate: AgentDebateResult,
        result: BandSyncResult,
    ) -> AgentDebateResult:
        return debate.model_copy(
            update={
                "band_chat_id": result.chat_id,
                "band_sync_status": result.status,
                "band_message_count": result.message_count,
                "band_sync_error": result.error,
            }
        )

    def _build_link(self) -> Any:
        if self._link_factory is not None:
            return self._link_factory(
                agent_id=self._settings.BAND_AGENT_ID,
                api_key=self._settings.BAND_API_KEY,
                ws_url=self._settings.BAND_WS_URL,
                rest_url=self._settings.BAND_REST_URL,
            )

        from band import BandLink

        return BandLink(
            agent_id=self._settings.BAND_AGENT_ID,
            api_key=self._settings.BAND_API_KEY,
            ws_url=self._settings.BAND_WS_URL,
            rest_url=self._settings.BAND_REST_URL,
        )

    def _request_options(self) -> dict[str, Any] | None:
        try:
            from band.client.rest import DEFAULT_REQUEST_OPTIONS

            return DEFAULT_REQUEST_OPTIONS
        except Exception:
            return None

    async def _create_chat(
        self,
        rest: Any,
        investigation_id: str,
        request_options: dict[str, Any] | None,
    ) -> str:
        from band.client.rest import ChatRoomRequest

        import re
        _UUID_RE = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
        )
        task_id = investigation_id if _UUID_RE.match(investigation_id) else None
        response = await rest.agent_api_chats.create_agent_chat(
            chat=ChatRoomRequest(task_id=task_id),
            request_options=request_options,
        )
        chat_id = _response_id(response)
        if not chat_id:
            raise RuntimeError("Band chat creation returned no chat id.")
        return chat_id

    async def _create_event(
        self,
        rest: Any,
        chat_id: str,
        role: str,
        content: str,
        debate: AgentDebateResult,
        request_options: dict[str, Any] | None,
        *,
        order: int,
    ) -> None:
        from band.client.rest import ChatEventRequest

        await rest.agent_api_events.create_agent_chat_event(
            chat_id,
            event=ChatEventRequest(
                content=f"{role}: {_clip(content)}",
                message_type="thought",
                metadata={
                    "source": "rhetoriq",
                    "investigation_id": debate.investigation_id,
                    "agent_role": role,
                    "order": order,
                    "confidence_label": debate.confidence_label,
                },
            ),
            request_options=request_options,
        )

    def _debate_messages(self, debate: AgentDebateResult) -> list[tuple[str, str]]:
        messages = [
            ("Analyst Agent", debate.analyst_position),
            ("Skeptic Agent", debate.skeptic_response),
            ("Receipts Agent", debate.receipts_check),
            ("Counter-Narrative Agent", debate.counter_narrative_note),
            ("Safety Agent", debate.safety_grounding_decision),
            ("Final Language Agent", debate.final_language_decision),
        ]
        if debate.rejected_claims:
            messages.append(("Skeptic Agent", "Rejected claims: " + "; ".join(debate.rejected_claims)))
        if debate.softened_claims:
            softened = "; ".join(
                f"{item.original} -> {item.softened}" for item in debate.softened_claims[:4]
            )
            messages.append(("Safety Agent", "Softened claims: " + softened))
        return [(role, content) for role, content in messages if content]


def _response_id(response: Any) -> str | None:
    data = getattr(response, "data", response)
    if isinstance(data, dict):
        value = data.get("id")
        return str(value) if value else None
    value = getattr(data, "id", None)
    return str(value) if value else None


def _clip(value: str, limit: int = 1800) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


_sync: BandRoomSync | None = None


def get_band_room_sync() -> BandRoomSync:
    global _sync
    if _sync is None:
        _sync = BandRoomSync()
    return _sync
