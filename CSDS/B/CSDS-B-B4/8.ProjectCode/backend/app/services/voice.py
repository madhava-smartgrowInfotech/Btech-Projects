"""F8 - spoken warnings and guidance in English, Hindi and Telugu (gTTS), with an MP3 cache.

gTTS calls Google's text-to-speech endpoint, so a phrase needs the internet the first time it
is spoken. Every phrase is cached by a hash of (language, text); the standard guides and
advice are pre-built into backend/app/assets/voice/ so they work offline too.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi import status

from app.core.config import ASSETS_DIR, get_settings
from app.core.deps import api_error
from app.core.logging import get_logger

log = get_logger("upi_guardian.voice")
PREBUILT = ASSETS_DIR / "voice"
GTTS_LANG = {"en": ("en", "co.in"), "hi": ("hi", "co.in"), "te": ("te", "co.in")}
MAX_CHARS = 900


def clean_for_speech(text: str) -> str:
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = text.replace("₹", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_CHARS]


def voice_key(lang: str, text: str) -> str:
    return hashlib.sha1(f"{lang}|{text}".encode("utf-8")).hexdigest()[:24]


def cache_dir() -> Path:
    d = get_settings().voice_cache_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def find_audio(key: str) -> Path | None:
    for base in (PREBUILT, cache_dir()):
        p = base / f"{key}.mp3"
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def synthesize(text: str, lang: str, target_dir: Path | None = None) -> tuple[str, bool]:
    """Returns (key, was_cached). Raises a 503 API error when speech cannot be generated."""
    if lang not in GTTS_LANG:
        raise api_error(status.HTTP_400_BAD_REQUEST, "voice_language", "Voice is available in English, Hindi and Telugu.")
    text = clean_for_speech(text)
    if not text:
        raise api_error(status.HTTP_400_BAD_REQUEST, "voice_empty", "Nothing to speak.")
    key = voice_key(lang, text)
    if target_dir is None and find_audio(key):
        return key, True
    if not get_settings().tts_enabled:
        raise api_error(status.HTTP_503_SERVICE_UNAVAILABLE, "voice_disabled", "Spoken warnings are turned off on this server (TTS_ENABLED=false).")
    out = (target_dir or cache_dir()) / f"{key}.mp3"
    try:
        from gtts import gTTS

        code, tld = GTTS_LANG[lang]
        tmp = out.with_suffix(".part")
        gTTS(text=text, lang=code, tld=tld, slow=False).save(str(tmp))
        tmp.replace(out)
    except Exception as exc:
        log.warning("speech synthesis failed", extra={"lang": lang, "error": str(exc)[:200]})
        raise api_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "voice_offline",
            "Could not create speech right now (no internet?). The warning is still shown on screen.",
        ) from exc
    return key, False
