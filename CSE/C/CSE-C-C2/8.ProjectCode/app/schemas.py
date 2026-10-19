"""StoryVox Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LanguageInfo(BaseModel):
    code: str
    name: str
    tts_checkpoint: str


class StoryGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    language_code: str = Field(min_length=2, max_length=8)
    style: str = "Adventure"
    length_option: str = "Short"
    synthesize: bool = True


class StoryResponse(BaseModel):
    id: int
    prompt: str
    title: str
    story_text: str
    language_code: str
    language_name: str
    style: str
    length_option: str
    word_count: int
    reading_time_minutes: float
    listening_time_minutes: float
    generation_time_seconds: float
    created_at: datetime
    audio: Optional["AudioResponse"] = None


class AudioResponse(BaseModel):
    id: int
    story_id: int
    file_path: str
    duration_seconds: float
    sample_rate: int
    tts_model: str
    synthesis_time_seconds: float
    rtf: float
    created_at: datetime


class StoryListItem(BaseModel):
    id: int
    title: str
    language_code: str
    language_name: str
    style: str
    word_count: int
    created_at: datetime
    has_audio: bool
    audio_id: Optional[int] = None


class EvaluationSummary(BaseModel):
    id: int
    evaluation_type: str
    language_code: str
    sample_count: int
    metrics_json: dict[str, Any]
    created_at: datetime


class EvaluationRunRequest(BaseModel):
    samples: int = Field(default=5, ge=1, le=30)
    language_code: Optional[str] = None
    skip_tts: bool = False
    skip_story: bool = False


StoryResponse.model_rebuild()
