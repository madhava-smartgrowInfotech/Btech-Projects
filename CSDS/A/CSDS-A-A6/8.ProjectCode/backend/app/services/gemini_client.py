"""Thin wrapper around google-generativeai for text generation and embeddings."""
import json
import re
import time

import google.generativeai as genai

from ..config import GEMINI_API_KEY, GEMINI_TEXT_MODEL, GEMINI_EMBEDDING_MODEL, gemini_configured

_configured = False


def _ensure_configured():
    global _configured
    if not gemini_configured():
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to .env (see .env.example) and restart the backend."
        )
    if not _configured:
        genai.configure(api_key=GEMINI_API_KEY)
        _configured = True


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    _ensure_configured()
    text = text[:8000]
    result = genai.embed_content(model=GEMINI_EMBEDDING_MODEL, content=text, task_type=task_type)
    return result["embedding"]


def embed_batch(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    return [embed_text(t, task_type=task_type) for t in texts]


def _call_model(prompt: str, retries: int = 3) -> str:
    _ensure_configured()
    model = genai.GenerativeModel(GEMINI_TEXT_MODEL)
    last_err = None
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text or ""
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Gemini generate_content failed after {retries} attempts: {last_err}")


def _extract_json(raw: str):
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    match = re.search(r"[\{\[].*[\}\]]", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


def generate_json(prompt: str, retries: int = 3):
    raw = _call_model(prompt, retries=retries)
    return _extract_json(raw)


def generate_text(prompt: str, retries: int = 3) -> str:
    return _call_model(prompt, retries=retries).strip()
