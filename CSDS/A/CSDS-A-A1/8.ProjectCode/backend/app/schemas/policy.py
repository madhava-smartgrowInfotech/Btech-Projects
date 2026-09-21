from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    size_bytes: int
    page_count: int
    insurer: str | None
    product_name: str | None
    uin: str | None
    status: str
    status_detail: str | None
    progress: int
    error: str | None
    extraction_error: str | None
    is_sample: bool
    processed_at: datetime | None


class PolicyOut(BaseModel):
    id: int
    display_name: str
    is_sample: bool
    created_at: datetime
    document: DocumentOut
    has_card: bool = False
    clause_count: int = 0
    risk_counts: dict[str, int] = Field(default_factory=dict)
    highlights: dict[str, str] = Field(default_factory=dict)


class PolicyStatusOut(BaseModel):
    id: int
    status: str
    status_detail: str | None
    progress: int
    error: str | None
    extraction_error: str | None
    has_card: bool


class PolicyRename(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)


class ClauseOut(BaseModel):
    id: int
    ordinal: int
    clause_ref: str | None
    heading: str | None
    section_path: str | None
    text: str
    page_start: int
    page_end: int
    bboxes: list[dict[str, float]]
    label: str


class PageInfo(BaseModel):
    number: int
    width: float
    height: float


class CardOut(BaseModel):
    policy_id: int
    document_id: int
    language: str
    model: str
    prompt_version: str
    created_at: datetime
    verified_ratio: float
    translated: bool = False
    data: dict[str, Any]
    summary: dict[str, Any] | None
    labels: dict[str, Any]


class RiskOut(BaseModel):
    id: int
    title: str
    category: str
    severity: str
    explanation: str
    clause_ordinal: int | None
    clause_label: str | None = None
    page: int | None
    quote: str | None
    source: str


class SearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    mode: Literal["bm25", "dense", "hybrid", "hybrid_rerank"] = "hybrid_rerank"
    k: int = Field(default=8, ge=1, le=20)
