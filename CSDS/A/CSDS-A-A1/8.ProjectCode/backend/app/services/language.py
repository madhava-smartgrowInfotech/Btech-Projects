"""F8 - Multilingual support: script detection, question translation for retrieval, and cached
translation of generated content (Policy Card, risk highlights) into Hindi or Telugu.

Policy wordings are English, so retrieval always runs on an English query; answers are generated
directly in the chosen language, while clause quotes stay in the policy's original English.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.config import LANGUAGE_NAMES
from app.core.db import SessionLocal
from app.models import Translation
from app.services.gemini_client import generate_json

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_TELUGU = re.compile(r"[ఀ-౿]")


def detect_script(text: str) -> str:
    if _TELUGU.search(text or ""):
        return "te"
    if _DEVANAGARI.search(text or ""):
        return "hi"
    return "en"


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, "English")


class _EnglishQuery(BaseModel):
    english: str = Field(description="The question in clear English, keeping medical and insurance terms.")


def to_english_query(text: str, user_id: int | None = None) -> str | None:
    """Translate a Hindi/Telugu question to English for keyword + semantic search. None for English input."""
    if detect_script(text) == "en":
        return None
    result, _ = generate_json(
        prompt=f"Translate this health-insurance question into English. Return only the translation.\n\n{text}",
        schema=_EnglishQuery, purpose="query_translation", user_id=user_id, prefer_lite=True, cache=True,
        temperature=0.0,
    )
    return result.english.strip() or None


class _Item(BaseModel):
    id: int
    text: str


class _Translated(BaseModel):
    items: list[_Item]


def translate_strings(strings: list[str], lang: str, purpose: str, user_id: int | None = None) -> list[str]:
    """Translate a batch of short UI strings, cached in the ``translations`` table."""
    if lang == "en" or not strings:
        return strings
    payload = json.dumps(strings, ensure_ascii=False)
    key = hashlib.sha256(f"{lang}|{payload}".encode()).hexdigest()[:40]
    with SessionLocal() as db:
        cached = db.scalar(select(Translation).where(Translation.source_type == purpose,
                                                     Translation.source_key == key, Translation.language == lang))
        if cached and len(cached.content.get("strings", [])) == len(strings):
            return cached.content["strings"]

    items = [{"id": i, "text": s} for i, s in enumerate(strings)]
    prompt = (
        f"Translate each item's text from English into {language_name(lang)} for an Indian health-insurance "
        f"customer. Keep numbers, currency amounts, percentages, clause numbers and product names unchanged. "
        f"Use simple everyday {language_name(lang)}; common insurance terms (sum insured, co-payment, claim) may "
        f"stay in English in brackets. Return every id exactly once.\n\n{json.dumps(items, ensure_ascii=False)}"
    )
    result, meta = generate_json(prompt=prompt, schema=_Translated, purpose=purpose, user_id=user_id,
                                 temperature=0.1, cache=True)
    by_id = {item.id: item.text for item in result.items}
    out = [by_id.get(i, s) for i, s in enumerate(strings)]
    with SessionLocal() as db:
        existing = db.scalar(select(Translation).where(Translation.source_type == purpose,
                                                       Translation.source_key == key, Translation.language == lang))
        if existing is None:
            db.add(Translation(source_type=purpose, source_key=key, language=lang, content={"strings": out},
                               model=meta.model))
            db.commit()
    return out


def _collect_card_strings(card: dict[str, Any], summary: dict[str, Any] | None) -> list[tuple[tuple, str]]:
    refs: list[tuple[tuple, str]] = []

    def visit(obj: Any, path: tuple) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("value", "name") and isinstance(v, str) and v:
                    refs.append(((*path, k), v))
                elif isinstance(v, (dict, list)):
                    visit(v, (*path, k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if isinstance(v, str) and path and path[-1] == "specific_disease_examples":
                    refs.append(((*path, i), v))
                else:
                    visit(v, (*path, i))

    visit(card, ("card",))
    for key in ("overview",):
        if summary and summary.get(key):
            refs.append((("summary", key), summary[key]))
    for key in ("best_for", "watch_outs", "next_actions"):
        for i, text in enumerate((summary or {}).get(key) or []):
            refs.append((("summary", key, i), text))
    return refs


def _assign(root: dict[str, Any], path: tuple, value: str) -> None:
    target: Any = root
    for step in path[:-1]:
        target = target[step]
    target[path[-1]] = value


def translate_card(card: dict[str, Any], summary: dict[str, Any] | None, lang: str,
                   user_id: int | None = None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if lang == "en":
        return card, summary
    refs = _collect_card_strings(card, summary)
    translated = translate_strings([text for _, text in refs], lang, "card_translation", user_id)
    root = {"card": deepcopy(card), "summary": deepcopy(summary) if summary else {}}
    for (path, _), text in zip(refs, translated):
        _assign(root, path, text)
    return root["card"], root["summary"] or summary


def translate_risks(risks: list[dict[str, Any]], lang: str, user_id: int | None = None) -> list[dict[str, Any]]:
    if lang == "en" or not risks:
        return risks
    strings: list[str] = []
    for r in risks:
        strings.extend([r["title"], r["explanation"]])
    translated = translate_strings(strings, lang, "risk_translation", user_id)
    out = []
    for i, r in enumerate(risks):
        out.append(r | {"title": translated[2 * i], "explanation": translated[2 * i + 1]})
    return out
