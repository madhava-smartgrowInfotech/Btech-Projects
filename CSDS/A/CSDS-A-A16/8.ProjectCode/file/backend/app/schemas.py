from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class EmotionScore(BaseModel):
    key: str
    label: str
    confidence: float


class DominantEmotion(EmotionScore):
    kind: str  # "basic" | "compound"


class AnalysisResponse(BaseModel):
    id: Optional[str]
    created_at: datetime
    face_detected: bool
    basic_emotions: list[EmotionScore]
    compound_emotions: list[EmotionScore]
    dominant: Optional[DominantEmotion]
    thumbnail_url: Optional[str] = None


class HistoryListResponse(BaseModel):
    items: list[AnalysisResponse]
    total: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
