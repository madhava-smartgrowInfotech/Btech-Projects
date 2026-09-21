from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    policy_id: int
    title: str | None = Field(default=None, max_length=200)


class MessageIn(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    language: str | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    content_en: str | None
    language: str
    status: str | None
    citations: list[dict[str, Any]] | None
    faithfulness: float | None
    faithfulness_detail: dict[str, Any] | None
    retrieval: dict[str, Any] | None
    timings: dict[str, Any] | None
    total_ms: int | None
    model: str | None
    created_at: datetime


class ConversationOut(BaseModel):
    id: int
    policy_id: int
    policy_name: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class ExchangeOut(BaseModel):
    question: MessageOut
    answer: MessageOut
    follow_ups: list[str] = []
