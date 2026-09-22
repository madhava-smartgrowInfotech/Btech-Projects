"""Gemini: structured detail extraction (schema-validated) and draft citizen replies."""
from typing import Optional

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from ..config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_MODEL


class Extraction(BaseModel):
    place: Optional[str] = Field(None, description="Locality, street, landmark or ward named in the complaint, as written. null if none.")
    issue: str = Field(description="The civic problem as a short English phrase, e.g. 'deep pothole on main road'.")
    affected_people: Optional[str] = Field(None, description="Who or how many people are affected, if stated or clearly implied. null if unknown.")
    hazards: list[str] = Field(default_factory=list, description="Safety or health hazards mentioned, in English. Empty if none.")
    duration: Optional[str] = Field(None, description="How long the problem has lasted, if stated, in English.")
    summary_en: str = Field(description="One-sentence English summary for the officer.")


class GeminiUnavailable(Exception):
    pass


_client = None


def _get_client():
    global _client
    if not GEMINI_API_KEY:
        raise GeminiUnavailable("GEMINI_API_KEY is not set in .env")
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _generate(prompt, schema=None, temperature=0.3):
    client = _get_client()
    last = None
    for model in dict.fromkeys([GEMINI_MODEL, GEMINI_FALLBACK_MODEL]):
        cfg = types.GenerateContentConfig(
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="application/json" if schema else "text/plain",
            response_schema=schema,
        )
        for _ in range(2):
            try:
                r = client.models.generate_content(model=model, contents=prompt, config=cfg)
                if r.text:
                    return r.text, model
                last = GeminiUnavailable("empty response")
            except errors.APIError as e:
                last = e
                if e.code not in (429, 500, 502, 503, 504):
                    raise GeminiUnavailable(f"Gemini error {e.code}: {e.message}") from e
    raise GeminiUnavailable(f"Gemini is busy right now ({last}). Try again in a minute.")


def extract_details(text: str) -> dict:
    prompt = (
        "You extract structured facts from a citizen complaint sent to a city grievance office in India. "
        "The complaint may be in English, Hindi or Hinglish (Hindi in Roman script). "
        "Only use facts stated in the complaint; use null when something is not mentioned. "
        "Write every field in English (translate if needed); for 'place' give the English/Roman spelling "
        "of the place name.\n\n"
        f"Complaint:\n{text}"
    )
    raw, model = _generate(prompt, schema=Extraction, temperature=0.1)
    data = Extraction.model_validate_json(raw)  # schema validation
    return {**data.model_dump(), "model": model}


def draft_reply(*, text, language, tracking_id, status, department, expected_days, officer_note=""):
    lang_rule = {
        "Hindi": "Write the reply in Hindi (Devanagari script).",
        "Hinglish": "Write the reply in Hinglish: Hindi words in Roman script, the way the citizen wrote.",
    }.get(language, "Write the reply in simple English.")
    prompt = (
        "You draft a short status reply from a city grievance office to the citizen who filed a complaint. "
        f"{lang_rule} Keep it polite, specific and under 110 words. Mention the tracking ID, the current "
        "status, the department handling it and the expected time to resolve. Do not promise anything that "
        "is not given below. Do not use placeholders such as [Name]; address the citizen generically. "
        "Sign off as 'Grievance Cell'. Return only the reply text.\n\n"
        f"Tracking ID: {tracking_id}\nStatus: {status}\nDepartment: {department}\n"
        f"Expected time to resolve: about {expected_days} days\n"
        f"Officer note (include if relevant): {officer_note or 'none'}\n\n"
        f"Citizen's complaint:\n{text}"
    )
    reply, model = _generate(prompt, temperature=0.4)
    return {"draft": reply.strip(), "model": model}
