"""
Loads prompt templates from agents/prompts/{name}.md.

Prompts are loaded once and cached in-process. The cache is keyed by name so
hot-reloading is possible in tests by calling _cache.clear().
"""

import os

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
_cache: dict[str, str] = {}


def load_prompt(name: str) -> str:
    """
    Load and return the markdown prompt file for `name`.
    Raises FileNotFoundError if the file does not exist.
    """
    if name in _cache:
        return _cache[name]

    path = os.path.join(_PROMPTS_DIR, f"{name}.md")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with open(path, encoding="utf-8") as fh:
        text = fh.read().strip()

    _cache[name] = text
    return text
