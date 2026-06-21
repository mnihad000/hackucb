import logging

from agents.model_client import _is_credit_or_quota_error, _log_model_call_error


class _ProviderError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


def test_credit_or_quota_errors_include_http_402_and_429():
    assert _is_credit_or_quota_error(_ProviderError("payment required", 402))
    assert _is_credit_or_quota_error(_ProviderError("rate limited", 429))


def test_credit_or_quota_errors_match_provider_messages():
    assert _is_credit_or_quota_error(
        _ProviderError("RESOURCE_EXHAUSTED: exceeded your current quota")
    )
    assert _is_credit_or_quota_error(
        _ProviderError("Your account has insufficient credits. Update billing.")
    )


def test_model_credit_failure_logs_as_error(caplog):
    caplog.set_level(logging.INFO, logger="agents.model_client")

    _log_model_call_error(
        provider="groq",
        model="test-model",
        schema_name="planner",
        exc=_ProviderError("insufficient_quota", 429),
    )

    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert "provider=groq" in caplog.text
    assert "agent_schema=planner" in caplog.text
    assert "quota/credit failure" in caplog.text


def test_non_quota_model_failure_logs_as_warning(caplog):
    caplog.set_level(logging.INFO, logger="agents.model_client")

    _log_model_call_error(
        provider="gemini",
        model="test-model",
        schema_name="narrative_family",
        exc=_ProviderError("temporary upstream error", 503),
    )

    assert any(record.levelno == logging.WARNING for record in caplog.records)
    assert "provider=gemini" in caplog.text
    assert "agent_schema=narrative_family" in caplog.text
