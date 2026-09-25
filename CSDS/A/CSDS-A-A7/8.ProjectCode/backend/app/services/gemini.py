import httpx

from .. import config

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = (
    "You are the SHEGUARD safety assistant. Answer questions about personal safety, "
    "route planning, emergency preparedness and what to do if someone feels unsafe. "
    "Be concise, practical and calm. If the user describes an active emergency, your "
    "first line must tell them to use the app's SOS button or call local emergency "
    "services immediately. Keep answers under 150 words."
)


async def ask_gemini(question: str, lat: float | None = None, lng: float | None = None) -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set in .env - get a free key at "
            "https://aistudio.google.com/apikey"
        )

    location_note = f"\n(User's current approximate location: {lat}, {lng})" if lat and lng else ""
    prompt = f"{SYSTEM_PROMPT}\n\nUser question: {question}{location_note}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            GEMINI_URL,
            params={"key": config.GEMINI_API_KEY},
            json=payload,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise RuntimeError("Gemini API returned an unexpected response shape")
