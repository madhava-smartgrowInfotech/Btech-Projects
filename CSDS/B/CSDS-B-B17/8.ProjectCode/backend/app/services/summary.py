"""Call summaries with Gemini: reason for the call, resolution and action items."""
import json
import re

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL

_client = None
RETRYABLE = ("429", "500", "503", "404", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "NOT_FOUND", "INTERNAL", "overloaded",
             "high demand", "timed out", "timeout")


class SummaryError(Exception):
    pass


def configured():
    return bool(GEMINI_API_KEY)


def _get_client():
    global _client
    if not GEMINI_API_KEY:
        raise SummaryError("Summaries need GEMINI_API_KEY in .env (https://aistudio.google.com/apikey)")
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _parse_json(text):
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    return json.loads(m.group(1) if m else text)


def generate_json(prompt, temperature=0.2):
    """Gemini in JSON mode; on busy / quota / retired-model errors fall through the fallback models."""
    from google.genai import types
    client = _get_client()
    models = [GEMINI_MODEL] + [m for m in GEMINI_FALLBACK_MODELS if m != GEMINI_MODEL]
    errors = []
    for model in models:
        for _ in range(2):  # one retry for malformed JSON
            try:
                resp = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=temperature))
                return _parse_json(resp.text), model
            except (ValueError, json.JSONDecodeError) as e:
                errors.append(f"{model}: malformed JSON ({e})")
            except Exception as e:  # network / quota / auth errors from the API
                msg = str(e)
                errors.append(f"{model}: {msg[:160]}")
                if not any(k in msg for k in RETRYABLE):
                    raise SummaryError(f"Gemini request failed: {msg[:300]}")
                break
    raise SummaryError("Gemini is unavailable right now (all models busy or over quota) - retry shortly. "
                       + " | ".join(errors[-3:]))


def _fmt(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def summarise(segments, intent=None):
    lines = "\n".join(f"[{_fmt(s['start'])}] {s['speaker'].upper()}: {s['text']}" for s in segments)
    hint = f"\nThe intent classifier labelled this call as: {intent}." if intent else ""
    prompt = f"""You are a contact-centre quality analyst. Read this customer-support call transcript
(speakers were separated automatically, so there may be small errors).{hint}

TRANSCRIPT
{lines}

Return JSON only:
{{"summary": "2-3 sentence neutral summary of the call",
  "reason": "why the customer called, one sentence",
  "resolution": "what the agent did and the outcome, one sentence",
  "status": "resolved" | "partially_resolved" | "unresolved",
  "action_items": [{{"owner": "agent" | "customer" | "team", "item": "concrete follow-up"}}],
  "customer_mood": "short phrase describing how the customer felt at the start and at the end"}}
Use only facts stated in the transcript. If there are no follow-ups, return an empty action_items list."""
    data, model = generate_json(prompt)
    status = str(data.get("status", "")).lower()
    return {
        "summary": str(data.get("summary", "")).strip(),
        "reason": str(data.get("reason", "")).strip(),
        "resolution": str(data.get("resolution", "")).strip(),
        "status": status if status in ("resolved", "partially_resolved", "unresolved") else "unresolved",
        "action_items": [{"owner": str(a.get("owner", "agent")), "item": str(a.get("item", "")).strip()}
                         for a in (data.get("action_items") or []) if isinstance(a, dict) and a.get("item")][:8],
        "customer_mood": str(data.get("customer_mood", "")).strip(),
        "model": model,
    }
