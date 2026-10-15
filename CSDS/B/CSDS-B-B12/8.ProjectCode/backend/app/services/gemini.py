"""Gemini REST client with model fallback (quota-limited keys fall through to the next model)."""
import json

import requests

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiError(RuntimeError):
    pass


def generate(prompt: str, system: str = "", history=None, json_mode: bool = False):
    """Return (text, model_used). history: list of (role, text) with role user|assistant."""
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY is not set in .env")
    contents = [{"role": "model" if r == "assistant" else "user", "parts": [{"text": t}]} for r, t in (history or [])]
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    body = {"contents": contents, "generationConfig": {"temperature": 0.3}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    errors = []
    for model in [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]:
        try:
            r = requests.post(URL.format(model=model), headers={"x-goog-api-key": GEMINI_API_KEY}, json=body, timeout=90)
        except requests.RequestException as e:
            errors.append(f"{model}: {e.__class__.__name__}")
            continue
        if r.status_code == 200:
            try:
                parts = r.json()["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts).strip()
            except (KeyError, IndexError, ValueError):
                errors.append(f"{model}: empty response")
                continue
            if text:
                return text, model
            errors.append(f"{model}: empty response")
            continue
        errors.append(f"{model}: HTTP {r.status_code}")
        if r.status_code in (400, 401, 403):
            break  # key problem - other models will fail the same way
    raise GeminiError("AI assistant unavailable (" + "; ".join(errors) + ")")


def generate_json(prompt: str, system: str = ""):
    text, model = generate(prompt, system, json_mode=True)
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text), model
    except json.JSONDecodeError:
        raise GeminiError("AI response was not valid JSON")
