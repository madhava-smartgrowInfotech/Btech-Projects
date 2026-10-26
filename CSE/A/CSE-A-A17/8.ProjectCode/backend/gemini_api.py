"""
gemini_api.py
--------------
Optional AI Insights for the API. src/gemini_helper.py reads the key from
`st.secrets`, which does not exist outside Streamlit, so this module sends the
same aggregated context and the same prompt to Gemini using the key and model
from `.env`. Raw data is never sent, only metrics / feature importance / a forecast summary.
"""

from __future__ import annotations

import requests

from src import gemini_helper

from .state import env

NOT_CONFIGURED = (
    "AI Insights is not configured. Add a GEMINI_API_KEY to .env to enable this optional feature. "
    "The rest of the app works fully without it."
)


def configured() -> bool:
    return bool(env("GEMINI_API_KEY"))


def model_name() -> str:
    return env("GEMINI_MODEL", "gemini-flash-latest")


def build_context(**kwargs) -> str:
    return gemini_helper.build_context_summary(**kwargs)


def ask(question: str, context_summary: str) -> str:
    if not configured():
        raise RuntimeError(NOT_CONFIGURED)

    prompt = f"""You are helping explain a fashion demand forecasting ML project
to a student and their project examiner. Base your explanation ONLY on
the data below -- do not invent numbers or facts not present here.

DATA SUMMARY:
{context_summary}

QUESTION:
{question}

Answer in clear, simple, plain language suitable for a project demo."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name()}:generateContent"
    resp = requests.post(
        url,
        headers={"x-goog-api-key": env("GEMINI_API_KEY"), "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
        except ValueError:
            detail = resp.text[:200]
        raise RuntimeError(f"Gemini returned {resp.status_code}: {detail}")
    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError):
        raise RuntimeError("Gemini returned no text for this question. Try rephrasing it.")
