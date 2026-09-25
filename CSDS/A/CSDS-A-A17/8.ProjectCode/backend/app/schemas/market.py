from pydantic import BaseModel


class PriceRequest(BaseModel):
    crop_type: str
    region: str
    grade: str = "B"
    listing_id: int | None = None


class PricePredictionOut(BaseModel):
    crop_type: str
    region: str
    grade: str
    current_price: float
    confidence_low: float
    confidence_high: float
    forecast: dict
    shap_explanation: dict
    best_sell_day: int

    class Config:
        from_attributes = True
