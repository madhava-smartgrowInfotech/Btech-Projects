from datetime import datetime

from pydantic import BaseModel


class QualityGradeOut(BaseModel):
    grade: str
    confidence: float
    probabilities: dict
    features: dict
    shap_explanation: dict

    class Config:
        from_attributes = True


class CropListingOut(BaseModel):
    id: int
    farmer_id: int
    crop_type: str
    region: str
    quantity_kg: float
    image_path: str
    status: str
    asking_price: float
    created_at: datetime
    quality_grade: QualityGradeOut | None = None

    class Config:
        from_attributes = True


class CropListingCreate(BaseModel):
    crop_type: str
    region: str
    quantity_kg: float
    asking_price: float = 0
