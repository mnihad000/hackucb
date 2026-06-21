"""
Model adapter layer for the investigation planner.

All clients implement BaseModelClient.generate_json(system_prompt, user_prompt, schema_name) -> dict.

Priority order when building a client for production:
  GeminiModelClient  (primary — fast, structured output support)
  GroqModelClient    (backup — llama-3.1-8b-instant, very low latency)
  OllamaModelClient  (local fallback — requires Ollama running locally)
  CachedModelClient  (last resort — returns pre-generated fixture JSON)
  MockModelClient    (deterministic — for tests and demo mode)
"""

import json
import os
from typing import Any


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class BaseModelClient:
    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mock — deterministic, no network calls, safe for tests
# ---------------------------------------------------------------------------

_MOCK_OUTPUTS: dict[str, dict] = {
    "planner": {
        "query_text": "Where did the 'hidden energy tax' narrative come from?",
        "topic": "hidden energy tax",
        "canonical_phrase": "hidden energy tax",
        "intent": "origin",
        "entities": ["hidden", "energy", "tax"],
        "search_queries": [
            "\"hidden energy tax\"",
            "Where did the 'hidden energy tax' narrative come from?",
            "\"hidden energy tax\" hidden energy tax",
        ],
        "semantic_queries": [
            "Investigate the narrative around hidden energy tax",
            "Find evidence about origin and spread of hidden energy tax",
            "Find counter-narratives and source diversity around hidden energy tax",
        ],
        "target_source_types": [
            "forum",
            "blog",
            "local_news",
            "national_news",
            "commentary",
            "speech_transcript",
        ],
        "requested_outputs": ["timeline", "counter_narratives", "source_diversity"],
        "time_window": {"start": None, "end": None, "label": "all_time"},
        "retrieval_mode": "broad",
        "risk_notes": [
            "Use 'first observed in our dataset' instead of claiming a definitive origin.",
            "Do not infer coordination or intent from timing alone.",
            "Return an evidence-seeking plan, not a user-facing answer.",
        ],
        "uncertainty_requirements": [
            "State clearly when earlier sources may exist outside the dataset.",
            "Preserve uncertainty when the query is broad or underspecified.",
        ],
    },
}


class MockModelClient(BaseModelClient):
    """
    Returns deterministic, schema-valid dicts keyed by schema_name.
    Used in DEMO_MODE and as the last-resort fallback in LLM functions.
    Never makes network calls.
    """

    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        if schema_name not in _MOCK_OUTPUTS:
            raise ValueError(f"MockModelClient has no output for schema_name={schema_name!r}")
        return dict(_MOCK_OUTPUTS[schema_name])


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

class GeminiModelClient(BaseModelClient):
    """
    Calls Google Gemini API (google-genai SDK).
    Requires GEMINI_API_KEY. Model defaults to GEMINI_MODEL env var or 'gemini-2.5-flash'.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        if not self._api_key:
            raise RuntimeError(
                "GeminiModelClient requires GEMINI_API_KEY. "
                "Set it in your .env file or environment."
            )

    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        try:
            from google import genai  # type: ignore[import]
            from google.genai import types as genai_types  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is not installed. Run: pip install google-genai"
            ) from exc

        client = genai.Client(api_key=self._api_key)
        response = client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        from agents.json_utils import safe_json_loads
        return safe_json_loads(response.text)


# ---------------------------------------------------------------------------
# Groq
# ---------------------------------------------------------------------------

class GroqModelClient(BaseModelClient):
    """
    Calls Groq API with JSON mode enabled.
    Requires GROQ_API_KEY. Model defaults to GROQ_MODEL env var or 'llama-3.1-8b-instant'.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self._model = model or os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

        if not self._api_key:
            raise RuntimeError(
                "GroqModelClient requires GROQ_API_KEY. "
                "Set it in your .env file or environment."
            )

    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        try:
            from groq import Groq  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "groq is not installed. Run: pip install groq"
            ) from exc

        client = Groq(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4096,
        )
        from agents.json_utils import safe_json_loads
        return safe_json_loads(response.choices[0].message.content or "{}")


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------

class OllamaModelClient(BaseModelClient):
    """
    Calls a local Ollama instance via its HTTP API.
    Base URL defaults to OLLAMA_BASE_URL or 'http://localhost:11434'.
    Model defaults to OLLAMA_MODEL or 'qwen3:8b'.
    No API key required.
    """

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self._base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        import httpx

        full_prompt = (
            f"{system_prompt}\n\n"
            "Return ONLY a valid JSON object. No markdown. No explanation.\n\n"
            f"{user_prompt}"
        )
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": full_prompt, "stream": False, "format": "json"},
            timeout=120,
        )
        response.raise_for_status()
        text = response.json().get("response", "")
        from agents.json_utils import safe_json_loads
        return safe_json_loads(text)


# ---------------------------------------------------------------------------
# Cached — loads pre-generated fixture JSON
# ---------------------------------------------------------------------------

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class CachedModelClient(BaseModelClient):
    """
    Loads pre-generated JSON from agents/fixtures/{schema_name}.json.
    Used as a last-resort fallback when all live model calls fail.
    Falls back to MockModelClient if a fixture file does not exist.
    """

    def __init__(self) -> None:
        self._mock = MockModelClient()

    def generate_json(self, system_prompt: str, user_prompt: str, schema_name: str) -> dict:
        path = os.path.join(_FIXTURES_DIR, f"{schema_name}.json")
        if not os.path.exists(path):
            return self._mock.generate_json(system_prompt, user_prompt, schema_name)
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_model_client(prefer: str = "gemini") -> BaseModelClient:
    """
    Build the best available model client in priority order.

    prefer = "gemini" | "groq" | "ollama" | "mock"

    Falls through to the next client if the preferred one is unavailable.
    Always returns a working client (MockModelClient at minimum).
    """
    chain: list[str] = _build_chain(prefer)

    for name in chain:
        try:
            if name == "gemini":
                return GeminiModelClient()
            elif name == "groq":
                return GroqModelClient()
            elif name == "ollama":
                client = OllamaModelClient()
                # Quick connectivity check
                import httpx
                httpx.get(f"{client._base_url}/api/tags", timeout=3).raise_for_status()
                return client
            elif name == "cached":
                return CachedModelClient()
        except Exception:
            continue

    return MockModelClient()


def _build_chain(prefer: str) -> list[str]:
    order = ["gemini", "groq", "ollama", "cached", "mock"]
    if prefer in order:
        order = [prefer] + [x for x in order if x != prefer]
    return order
