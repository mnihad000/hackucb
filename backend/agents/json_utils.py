"""
JSON extraction and safety validation for LLM outputs.

LLMs frequently wrap JSON in markdown fences, add preamble text, or include
trailing commentary. extract_json_object and safe_json_loads handle all of that.

validate_no_forbidden_language enforces RhetoriQ's cautious framing policy by
rejecting outputs that contain factual overclaims.
"""

import json
import re


# ---------------------------------------------------------------------------
# Forbidden phrases — language that asserts factual conclusions we can't make
# ---------------------------------------------------------------------------

_FORBIDDEN: list[tuple[str, str]] = [
    ("true origin", "Use 'first observed in our dataset' instead of 'true origin'."),
    ("proved coordination", "Do not claim proved coordination — use 'consistent with' or 'signals of'."),
    ("was coordinated", "Do not assert coordination — use 'may suggest' or 'is consistent with coordination signals'."),
    ("fake news", "Do not use 'fake news' — describe observed content neutrally."),
]

# "disinformation campaign" is allowed only when explicitly attributed to a source as a claim it made.
_DISINFORMATION_PATTERN = re.compile(
    r"\b(?:is|are|was|were|constitutes?|represents?)\s+(?:a\s+)?disinformation campaign",
    re.IGNORECASE,
)

_ALLOWED_QUALIFIERS = {
    "first observed in our dataset",
    "signals consistent with",
    "requires human review",
    "retrieved dataset",
    "consistent with",
    "may indicate",
    "is consistent with",
}


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json_object(text: str) -> dict:
    """
    Extracts the first JSON object from `text`, tolerating:
    - Markdown fences: ```json ... ``` or ``` ... ```
    - Preamble text before the opening brace
    - Trailing text after the closing brace
    - Single-quoted keys (converts to double-quoted)

    Raises ValueError if no valid JSON object is found.
    """
    # Strip markdown fences first
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Find the outermost { ... } block
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output.")

    depth = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(text[start:], start=start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Try fixing single-quoted keys
                    fixed = re.sub(r"'([^']+)':", r'"\1":', candidate)
                    return json.loads(fixed)

    raise ValueError("Unbalanced braces — could not extract JSON object.")


def safe_json_loads(text: str) -> dict:
    """
    Attempts to parse `text` as JSON using multiple strategies in order:
    1. Direct json.loads (cheapest — works when output is already clean JSON)
    2. extract_json_object (handles preamble/fence wrapping)

    Raises ValueError if all strategies fail.
    """
    text = text.strip()

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    return extract_json_object(text)


# ---------------------------------------------------------------------------
# Safety validation
# ---------------------------------------------------------------------------

def validate_no_forbidden_language(obj: dict) -> None:
    """
    Recursively walks `obj` and raises ValueError if any string value contains
    a forbidden factual phrase.

    The "disinformation campaign" phrase is only forbidden when used as a
    declarative assertion (e.g. "this is a disinformation campaign") rather
    than as a quote attributed to a source (e.g. "critics called it a disinformation campaign").
    """
    _check_value(obj)


def _check_value(value: object) -> None:
    if isinstance(value, str):
        lower = value.lower()
        for phrase, guidance in _FORBIDDEN:
            if phrase in lower:
                raise ValueError(
                    f"Forbidden language detected: '{phrase}'. {guidance}\n"
                    f"Offending text: {value[:200]!r}"
                )
        if "disinformation campaign" in lower and _DISINFORMATION_PATTERN.search(value):
            raise ValueError(
                "Forbidden language detected: asserting 'disinformation campaign' as fact. "
                "Only use this phrase when explicitly attributing it as a claim made by a source. "
                f"Offending text: {value[:200]!r}"
            )
    elif isinstance(value, dict):
        for v in value.values():
            _check_value(v)
    elif isinstance(value, list):
        for item in value:
            _check_value(item)
