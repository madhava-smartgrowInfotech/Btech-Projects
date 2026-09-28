"""Thin Gemini wrapper: JSON generation from text or an image, with model fallback."""
import json
import re

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL


class GeminiUnavailable(Exception):
    pass


_client = None


def client():
    global _client
    if not GEMINI_API_KEY:
        raise GeminiUnavailable("Gemini is not configured. Add GEMINI_API_KEY to the .env file and restart the backend.")
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _parse_json(text: str):
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def generate_json(prompt: str, image: bytes | None = None, mime_type: str = "image/jpeg", temperature: float = 0.4):
    from google.genai import types
    c = client()
    contents = []
    if image is not None:
        contents.append(types.Part.from_bytes(data=image, mime_type=mime_type))
    contents.append(prompt)
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=temperature)
    last_err = None
    for model in [GEMINI_MODEL] + [m for m in GEMINI_FALLBACK_MODELS if m != GEMINI_MODEL]:
        try:
            resp = c.models.generate_content(model=model, contents=contents, config=config)
            return _parse_json(resp.text), model
        except Exception as e:  # model missing, quota, transient error -> try the next model
            last_err = e
            continue
    raise GeminiUnavailable(f"Gemini request failed: {str(last_err)[:300]}")
