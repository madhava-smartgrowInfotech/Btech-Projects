"""Optional plain-language complaint summary with Google Gemini. Without GEMINI_API_KEY the deterministic
template summary (services/evidence.summary_text) is used unchanged."""
from __future__ import annotations

import json
import logging

from ..core.config import settings

log = logging.getLogger("signalscout.llm")

PROMPT = (
    "You write complaint letters to a mobile network operator's complaint desk. Rewrite the draft below as a short, "
    "polite, factual complaint (at most 120 words). Keep every number, reference code and location exactly as given; "
    "do not invent facts. Plain text, no greeting line, no signature.\n\nDraft:\n{draft}\n\nKey evidence (JSON):\n{evidence}"
)


def rewrite_summary(draft: str, evidence: dict) -> str:
    if not settings.gemini_api_key or not draft:
        return draft
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        key = {k: evidence.get(k) for k in ("readings", "classes", "bad_share", "service", "radio", "wifi", "window")}
        resp = client.models.generate_content(model=settings.gemini_model, contents=PROMPT.format(draft=draft, evidence=json.dumps(key, default=str)[:4000]))
        text = (resp.text or "").strip()
        return text if 40 <= len(text) <= 2000 else draft
    except Exception as exc:   # the template text is always a valid fallback
        log.warning("summary rewrite skipped", extra={"fields": {"error": str(exc)[:160]}})
        return draft
