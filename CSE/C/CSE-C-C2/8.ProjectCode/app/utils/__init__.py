"""StoryVox small text/audio utility helpers."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

_WORD_RE = re.compile(r"[\w'\-]+", re.UNICODE)


def word_count(text: str) -> int:
    return len(_WORD_RE.findall(text or ""))


def reading_time_minutes(text: str, wpm: float = 200.0) -> float:
    return round(word_count(text) / wpm, 2) if text else 0.0


def listening_time_minutes(audio_duration_seconds: float, text: str = "") -> float:
    if audio_duration_seconds and audio_duration_seconds > 0:
        return round(audio_duration_seconds / 60.0, 2)
    return reading_time_minutes(text, wpm=150.0)


def chunk_text(text: str, max_chars: int = 380) -> list[str]:
    """Split text into synthesis-friendly chunks at sentence boundaries."""
    import re as _re

    clean = " ".join((text or "").split())
    if not clean:
        return []
    sentences = _re.split(r"(?<=[.!?\u0964\u3002])\s+", clean)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = (current + " " + sentence).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            while len(sentence) > max_chars:
                chunks.append(sentence[:max_chars])
                sentence = sentence[max_chars:]
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def sanitize_filename(name: str, max_len: int = 80) -> str:
    normalized = unicodedata.normalize("NFKD", name or "storyvox")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_only).strip("._-")
    return (cleaned[:max_len] or "storyvox").lower()


def normalize_text_for_metric(text: str) -> str:
    return " ".join((text or "").lower().split())


def unique_audio_filename(story_id: int, suffix: str = ".wav") -> str:
    import time
    import uuid

    stamp = int(time.time() * 1000)
    token = uuid.uuid4().hex[:8]
    return f"storyvox_story{story_id}_{stamp}_{token}{suffix}"


def ensure_within_directory(base: Path, target: Path) -> Path:
    resolved_base = base.resolve()
    resolved_target = target.resolve()
    if resolved_base not in resolved_target.parents and resolved_target != resolved_base:
        raise ValueError("Audio path escapes the StoryVox audio directory.")
    return resolved_target
