"""Request and response shapes for the Nuvara API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ORM = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------- catalogue


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    product_count: int


class ProductOut(BaseModel):
    model_config = ORM

    id: int
    slug: str
    name: str
    category: str
    subcategory: str
    price: float
    compare_at_price: float | None = None
    currency: str
    description: str
    short_description: str
    image_seed: str
    colorway: str
    rating: float
    review_count: int
    stock: int
    tags: list[str]
    attributes: dict[str, Any]
    created_at: datetime


class ProductDetailOut(ProductOut):
    related_ids: list[int] = Field(default_factory=list)


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class ReviewOut(BaseModel):
    model_config = ORM

    id: int
    user_name: str
    rating: int
    title: str
    body: str
    created_at: datetime
    helpful_count: int


class ReviewListOut(BaseModel):
    items: list[ReviewOut]
    total: int
    page: int = 1
    page_size: int = 10


# --------------------------------------------------------------------- people


class PersonaOut(BaseModel):
    id: str
    name: str
    segment: str
    avatar_seed: str
    blurb: str


# --------------------------------------------------------------------- events


class EventIn(BaseModel):
    session_id: str
    user_id: str | None = None
    product_id: int | None = None
    type: Literal["view", "click", "search", "add_to_cart", "purchase", "rating", "review"]
    query: str | None = None
    value: float | None = None
    rec_id: str | None = None
    source_agent: str | None = None


class EventOut(BaseModel):
    ok: bool
    event_id: int


# ------------------------------------------------------------ recommendations


class Weights(BaseModel):
    collaborative: float
    content: float
    trending: float
    diversity: float


class Strategy(BaseModel):
    name: str
    weights: Weights


class AgentScores(BaseModel):
    collaborative: float
    content: float
    trending: float
    diversity_bonus: float


class RecommendationItem(BaseModel):
    product: ProductOut
    rec_id: str
    score: float
    reason: str
    agents: AgentScores
    confidence: float
    base_score: float | None = None


class RecommendationsOut(BaseModel):
    strategy: Strategy
    items: list[RecommendationItem]


class AgentBreakdown(BaseModel):
    agent: Literal["collaborative", "content", "trending"]
    weight: float
    raw_score: float
    contribution: float
    narrative: str


class SimilarBecause(BaseModel):
    product: ProductOut
    similarity: float
    shared_signal: str


class AudienceFit(BaseModel):
    segment: str
    percentile: float
    segment_affinity: float | None = None
    population_affinity: float | None = None


class ExplainOut(BaseModel):
    rec_id: str
    product: ProductOut
    headline: str
    agent_breakdown: list[AgentBreakdown]
    similar_because: list[SimilarBecause]
    audience_fit: AudienceFit
    diversity_bonus: float | None = None
    confidence: float | None = None
    context: str | None = None


# ------------------------------------------------------------------- feedback


class FeedbackIn(BaseModel):
    session_id: str
    user_id: str | None = None
    rec_id: str
    action: Literal["click", "add_to_cart", "purchase", "dismiss", "ignore"]


class FeedbackOut(BaseModel):
    ok: bool
    updated_weights: Weights
    learning_step: int
    applied: bool | None = None
    reward: float | None = None
    agent_credit: dict[str, float] | None = None
    delta: dict[str, float] | None = None


class WeightHistoryOut(BaseModel):
    step: int
    timestamp: datetime
    weights: Weights
    trigger_action: str


# ----------------------------------------------------------------- simulation


class SimulateIn(BaseModel):
    name: str = "Untitled strategy"
    weights: Weights
    population_size: int | None = Field(default=200, ge=10, le=2000)
    rounds: int | None = Field(default=5, ge=1, le=30)


class SimMetrics(BaseModel):
    ctr: float
    conversion_rate: float
    avg_order_value: float
    catalog_coverage: float
    diversity_index: float
    impressions: int | None = None
    clicks: int | None = None
    purchases: int | None = None
    revenue: float | None = None


class Lift(BaseModel):
    ctr_pct: float
    conversion_pct: float
    revenue_pct: float


class TimelinePoint(BaseModel):
    round: int
    baseline_ctr: float
    candidate_ctr: float


class SegmentRow(BaseModel):
    segment: str
    baseline_ctr: float
    candidate_ctr: float
    ctr_lift_pct: float | None = None
    impressions: int | None = None


class SimulateOut(BaseModel):
    run_id: str
    name: str
    weights: Weights
    baseline_weights: Weights | None = None
    baseline: SimMetrics
    candidate: SimMetrics
    lift: Lift
    timeline: list[TimelinePoint]
    segment_breakdown: list[SegmentRow]
    verdict: Literal["deploy", "hold", "reject"]
    narrative: str
    population_size: int | None = None
    distinct_profiles: int | None = None
    rounds: int | None = None
    created_at: str | None = None


class SimulationHistoryRow(BaseModel):
    run_id: str
    name: str
    weights: Weights
    verdict: str
    lift: Lift
    created_at: datetime


class DeployOut(BaseModel):
    ok: bool
    live_weights: Weights


# -------------------------------------------------------------------- traffic


class TrafficSnapshot(BaseModel):
    rps: float
    p50_latency_ms: float
    p99_latency_ms: float
    queue_length: int
    cache_hit_rate: float
    active_workers: int
    autoscale_target: int
    status: Literal["nominal", "elevated", "critical"]
    updated_at: str
    active_test: dict[str, Any] | None = None


class LoadTestIn(BaseModel):
    profile: Literal["steady", "flash_sale", "spike"]
    duration_s: float = Field(default=60, ge=5, le=900)


class LoadTestOut(BaseModel):
    ok: bool
    test_id: str
    profile: str
    duration_s: float
