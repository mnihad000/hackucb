"""
Arize observability layer for RhetoriQ.

Initialises an OpenTelemetry TracerProvider that exports spans to Arize
cloud via gRPC.  Every LLM call in the investigation pipeline is wrapped
in a span so judges (and the team) can see the full trace of each
investigation in the Arize UI.

Span attributes follow the OpenInference semantic conventions so Arize
can group them by model, agent, and schema automatically.

Usage:
    # Once at process start (called from main.py startup event):
    init_arize_tracing()

    # In agent code — use TracedModelClient wrapper (automatic) or
    # manually:
    with tracer_span("my_agent", schema="planner") as span:
        result = client.generate_json(...)
        span.set_attribute(OUTPUT_VALUE, str(result))
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)

_tracer: Any = None          # opentelemetry Tracer
_provider_ready = False      # True once init_arize_tracing() has succeeded
_init_attempted = False      # guard against repeated init attempts


def init_arize_tracing() -> bool:
    """
    Initialise the Arize/OTEL tracer provider.  Idempotent — safe to call
    multiple times; subsequent calls are no-ops.

    Returns True if tracing is now active, False if it couldn't be configured
    (missing keys, network error, etc.).
    """
    global _tracer, _provider_ready, _init_attempted
    if _init_attempted:
        return _provider_ready
    _init_attempted = True

    from config import get_settings
    settings = get_settings()

    api_key = settings.ARIZE_API_KEY
    space_id = settings.ARIZE_SPACE_ID

    if not api_key or not space_id:
        logger.warning(
            "Arize tracing disabled: ARIZE_API_KEY or ARIZE_SPACE_ID not set"
        )
        return False

    try:
        from arize.otel import register

        provider = register(
            space_id=space_id,
            api_key=api_key,
            project_name="RhetoriQ",
            batch=True,
            set_global_tracer_provider=True,
            verbose=False,
        )
        _tracer = provider.get_tracer("rhetoriq")
        _provider_ready = True
        logger.info("Arize tracing initialised (project=RhetoriQ, space=%s…)", space_id[:12])
        return True

    except Exception as exc:
        logger.warning("Arize tracing init failed: %s", exc)
        return False


def is_ready() -> bool:
    return _provider_ready


@contextmanager
def tracer_span(
    agent_name: str,
    schema: str = "",
    model: str = "",
    extra_attrs: dict[str, Any] | None = None,
) -> Generator[Any, None, None]:
    """
    Context manager that wraps a block of code in an Arize/OTEL LLM span.

    If tracing is not configured, yields a no-op sentinel so callers don't
    need to branch.
    """
    if not _provider_ready or _tracer is None:
        yield _NoOpSpan()
        return

    try:
        from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
    except ImportError:
        yield _NoOpSpan()
        return

    with _tracer.start_as_current_span(agent_name) as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.LLM.value)
        if model:
            span.set_attribute(SpanAttributes.LLM_MODEL_NAME, model)
        if schema:
            span.set_attribute("rhetoriq.agent.schema", schema)
        if extra_attrs:
            for k, v in extra_attrs.items():
                span.set_attribute(k, v)
        try:
            yield span
        except Exception as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc))
            raise


class _NoOpSpan:
    """Silent stand-in when tracing is not active."""
    def set_attribute(self, key: str, value: Any) -> None:
        pass
    def record_exception(self, exc: Exception) -> None:
        pass


def record_claim_grounding_eval(
    investigation_id: str,
    claim_receipts: list,
) -> None:
    """
    Emit a per-claim grounding span immediately after receipts are built.

    Each entry in claim_receipts must have .claim_id, .support_status, and
    .verification_state.  Records a breakdown of supported vs unsupported
    claims so Arize judges can see which specific claims lacked evidence
    before the final report drops them.
    """
    if not _provider_ready or _tracer is None:
        return

    try:
        from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

        supported = sum(1 for r in claim_receipts if getattr(r, "support_status", "") == "supported")
        unsupported = sum(1 for r in claim_receipts if getattr(r, "support_status", "") == "not_supported")
        total = len(claim_receipts)
        score = round(supported / max(1, total), 3)

        claim_detail = [
            {
                "claim_id": getattr(r, "claim_id", ""),
                "support_status": getattr(r, "support_status", ""),
                "verification_state": getattr(r, "verification_state", ""),
            }
            for r in claim_receipts
        ]

        with _tracer.start_as_current_span("claim_grounding_eval") as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.CHAIN.value,
            )
            span.set_attribute("rhetoriq.investigation_id", investigation_id)
            span.set_attribute("rhetoriq.claim_grounding.supported", supported)
            span.set_attribute("rhetoriq.claim_grounding.unsupported", unsupported)
            span.set_attribute("rhetoriq.claim_grounding.total", total)
            span.set_attribute("rhetoriq.claim_grounding.score", score)
            span.set_attribute(
                SpanAttributes.OUTPUT_VALUE,
                json.dumps({
                    "investigation_id": investigation_id,
                    "claim_grounding_score": score,
                    "supported": supported,
                    "unsupported": unsupported,
                    "total": total,
                    "claims": claim_detail,
                }),
            )
            logger.info(
                "Claim grounding eval: investigation=%s score=%.3f supported=%d/%d",
                investigation_id, score, supported, total,
            )
    except Exception as exc:
        logger.warning("Claim grounding eval span failed: %s", exc)


def record_grounding_eval(
    investigation_id: str,
    verified_count: int,
    pending_count: int,
    unavailable_count: int,
    total_claims: int,
) -> None:
    """
    Emit a single span summarising how well the final report is grounded.

    Arize shows this as a standalone eval span attached to the investigation.
    Judges can open the Arize UI and see the grounding score for every run.
    """
    if not _provider_ready or _tracer is None:
        return

    try:
        from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

        with _tracer.start_as_current_span("grounding_eval") as span:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.CHAIN.value,
            )
            span.set_attribute("rhetoriq.investigation_id", investigation_id)
            span.set_attribute("rhetoriq.grounding.verified", verified_count)
            span.set_attribute("rhetoriq.grounding.pending", pending_count)
            span.set_attribute("rhetoriq.grounding.unavailable", unavailable_count)
            span.set_attribute("rhetoriq.grounding.total_claims", total_claims)
            score = round(verified_count / max(1, total_claims), 3)
            span.set_attribute("rhetoriq.grounding.score", score)
            span.set_attribute(
                SpanAttributes.OUTPUT_VALUE,
                json.dumps({
                    "investigation_id": investigation_id,
                    "grounding_score": score,
                    "verified": verified_count,
                    "pending": pending_count,
                    "unavailable": unavailable_count,
                    "total_claims": total_claims,
                }),
            )
            logger.info(
                "Grounding eval: investigation=%s score=%.3f verified=%d/%d",
                investigation_id, score, verified_count, total_claims,
            )
    except Exception as exc:
        logger.warning("Grounding eval span failed: %s", exc)
