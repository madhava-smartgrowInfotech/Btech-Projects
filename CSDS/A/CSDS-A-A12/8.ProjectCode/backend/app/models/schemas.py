"""Pydantic response/request schemas for the API."""
import datetime as dt

from pydantic import BaseModel


class KeyFactor(BaseModel):
    factor: str
    impact: str
    weight: float
    detail: str


class Explanation(BaseModel):
    summary: str
    key_factors: list[KeyFactor]
    recommendations: list[str]


class MorphologicalFeatures(BaseModel):
    area: float
    perimeter: float
    aspect_ratio: float
    circularity: float
    mean_color_rgb: list[float]
    color_std: float
    segmented: bool


class EmbeddingSummary(BaseModel):
    encoder: str
    embedding_dim: int
    top_activations: list[float]


class PredictionResponse(BaseModel):
    id: str
    prediction: str
    confidence: float
    probability_germinate: float
    risk_level: str
    morphological_features: MorphologicalFeatures
    embedding_summary: EmbeddingSummary
    explanation: Explanation
    seed_type: str
    soil_moisture: float
    temperature: float
    humidity: float
    rainfall: float
    soil_ph: float
    created_at: dt.datetime
    thumbnail_data_url: str | None = None

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    id: str
    prediction: str
    confidence: float
    probability_germinate: float
    risk_level: str
    seed_type: str
    created_at: dt.datetime
    thumbnail_data_url: str | None = None

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_predictions: int
    germination_rate: float
    avg_confidence: float
    seed_type_breakdown: dict
    trend: list[dict]
    model_metrics: dict


class HealthResponse(BaseModel):
    status: str
    model_version: str
    encoder_version: str


class ModelInfoResponse(BaseModel):
    architecture: dict
    global_feature_importance: list[dict]
    metrics: dict
