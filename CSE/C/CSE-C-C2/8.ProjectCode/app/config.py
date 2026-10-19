"""StoryVox application configuration."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


class Settings:
    """Reads environment on every instantiation so tests can isolate via monkeypatch."""

    def __init__(self) -> None:
        self.app_name: str = "StoryVox"
        self.host: str = _env("HOST", "127.0.0.1")
        self.port: int = _env_int("PORT", 8000)
        self.story_model: str = _env("STORY_MODEL", "Qwen/Qwen3-0.6B")
        self.tts_model: str = _env("TTS_MODEL", "facebook/mms-tts-eng")
        self.asr_model: str = _env("ASR_MODEL", "openai/whisper-small")
        self.max_prompt_chars: int = _env_int("MAX_PROMPT_CHARS", 2000)
        self.max_audio_upload_mb: int = _env_int("MAX_AUDIO_UPLOAD_MB", 10)
        self.db_path: str = _env("STORYVOX_DB_PATH", "data/storyvox.db")
        self.audio_dir: str = _env("STORYVOX_AUDIO_DIR", "data/audio")
        self.eval_dir: str = _env("STORYVOX_EVAL_DIR", "data/evaluations")
        self.dataset_dir: str = _env("STORYVOX_DATASET_DIR", "data/datasets")
        self.story_max_tokens_short: int = _env_int("STORY_MAX_NEW_TOKENS_SHORT", 220)
        self.story_max_tokens_medium: int = _env_int("STORY_MAX_NEW_TOKENS_MEDIUM", 420)
        self.story_max_tokens_long: int = _env_int("STORY_MAX_NEW_TOKENS_LONG", 700)
        self.story_temperature: float = _env_float("STORY_TEMPERATURE", 0.8)
        self.story_top_p: float = _env_float("STORY_TOP_P", 0.9)

    @property
    def resolved_db_path(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def resolved_audio_dir(self) -> Path:
        p = Path(self.audio_dir)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def resolved_eval_dir(self) -> Path:
        p = Path(self.eval_dir)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def resolved_dataset_dir(self) -> Path:
        p = Path(self.dataset_dir)
        return p if p.is_absolute() else BASE_DIR / p


@lru_cache
def get_settings() -> Settings:
    return Settings()


SUPPORTED_STYLES = [
    "Adventure",
    "Fantasy",
    "Educational",
    "Bedtime",
    "Mystery",
    "Inspirational",
    "Funny",
    "Custom",
]

SUPPORTED_LENGTHS = ["Short", "Medium", "Long"]

# Languages supported by both the story workflow and the MMS TTS checkpoints.
# code: (display name, mms checkpoint suffix, tts HF checkpoint)
SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "tts_checkpoint": "facebook/mms-tts-eng"},
    {"code": "hi", "name": "Hindi", "tts_checkpoint": "facebook/mms-tts-hin"},
    {"code": "es", "name": "Spanish", "tts_checkpoint": "facebook/mms-tts-spa"},
    {"code": "fr", "name": "French", "tts_checkpoint": "facebook/mms-tts-fra"},
    {"code": "de", "name": "German", "tts_checkpoint": "facebook/mms-tts-deu"},
    {"code": "it", "name": "Italian", "tts_checkpoint": "facebook/mms-tts-ita"},
    {"code": "pt", "name": "Portuguese", "tts_checkpoint": "facebook/mms-tts-por"},
    {"code": "ru", "name": "Russian", "tts_checkpoint": "facebook/mms-tts-rus"},
    {"code": "ar", "name": "Arabic", "tts_checkpoint": "facebook/mms-tts-ara"},
    {"code": "tr", "name": "Turkish", "tts_checkpoint": "facebook/mms-tts-tur"},
    {"code": "nl", "name": "Dutch", "tts_checkpoint": "facebook/mms-tts-nld"},
    {"code": "pl", "name": "Polish", "tts_checkpoint": "facebook/mms-tts-pol"},
    {"code": "zh", "name": "Chinese (Mandarin)", "tts_checkpoint": "facebook/mms-tts-cmn"},
    {"code": "ja", "name": "Japanese", "tts_checkpoint": "facebook/mms-tts-jpn"},
    {"code": "ko", "name": "Korean", "tts_checkpoint": "facebook/mms-tts-kor"},
]

LANGUAGE_MAP = {lang["code"]: lang for lang in SUPPORTED_LANGUAGES}
