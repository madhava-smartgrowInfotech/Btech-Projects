"""Optional LLM layer. The system is fully functional offline; if ANTHROPIC_API_KEY is set the reasoning
agents additionally ask Claude to write a plain-language explanation for the top findings."""
from __future__ import annotations

import os

MODEL = os.environ.get("AUTOSECAI_MODEL", "claude-sonnet-5-5")


def available(key: str | None = None) -> bool:
    return bool(key or os.environ.get("ANTHROPIC_API_KEY"))


def ask(prompt: str, system: str = "", key: str | None = None, max_tokens: int = 500, timeout: int = 40) -> str | None:
    key = key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import requests
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": MODEL, "max_tokens": max_tokens, "system": system,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=timeout)
        if r.status_code != 200:
            return None
        return "".join(b.get("text", "") for b in r.json().get("content", [])).strip() or None
    except Exception:
        return None
