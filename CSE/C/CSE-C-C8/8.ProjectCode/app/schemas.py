"""PeerScope Pydantic schemas for request/response validation."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ReviewerIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)
    affiliation: str = Field(default="", max_length=300)
    expertise_description: str = Field(default="", max_length=4000)
    research_topics: str = Field(default="", max_length=2000)
    methods: str = Field(default="", max_length=2000)
    keywords: str = Field(default="", max_length=2000)
    publication_titles: str = Field(default="", max_length=4000)
    current_load: int = Field(default=0, ge=0, le=100)
    maximum_load: int = Field(default=5, ge=1, le=100)
    is_active: bool = True
    conflict_terms: str = Field(default="", max_length=2000)


class ReviewerOut(ReviewerIn):
    id: int


class AnalysisSummary(BaseModel):
    id: int
    filename: str
    created_at: str
    overall_assessment: str
    concern_count: int
    recommendation_count: int
    top_reviewer: str
    status: str


class HealthOut(BaseModel):
    status: str
    product: str
    llm_status: str
    embedding_status: str
    model_loaded: bool
    reviewer_count: int
    literature_retrieval: str = "openalex"


class MetricsOut(BaseModel):
    data: dict[str, Any]


class AnalyzeFilters(BaseModel):
    active_only: bool = True
    min_score: float = 0.0
    topic: Optional[str] = None
    method: Optional[str] = None
