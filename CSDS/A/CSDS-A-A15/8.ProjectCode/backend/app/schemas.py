import datetime as dt

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ClassProbability(BaseModel):
    label: str
    display_name: str
    probability: float


class InspectionOut(BaseModel):
    id: int
    asset_name: str
    original_filename: str
    image_url: str
    heatmap_url: str
    defect_type: str
    display_name: str
    confidence: float
    severity: str
    class_probabilities: list[ClassProbability]
    description: str
    root_cause_text: str
    corrective_actions: list[str]
    created_at: dt.datetime

    class Config:
        from_attributes = True


class InspectionSummary(BaseModel):
    id: int
    asset_name: str
    defect_type: str
    display_name: str
    confidence: float
    severity: str
    created_at: dt.datetime
    image_url: str


class AnalyticsSummary(BaseModel):
    total_inspections: int
    average_confidence: float
    defect_distribution: dict[str, int]
    severity_distribution: dict[str, int]
    inspections_over_time: list[dict]
    model_metrics: dict
