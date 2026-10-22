from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class ChatRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)

class EvidenceItem(BaseModel):
    record_id: str
    disease: str
    symptoms: str
    description: str
    guidance: str
    severity: str
    red_flags: str
    relevance: float

class ChatResponse(BaseModel):
    answer: str
    top_condition: str
    evidence: list[EvidenceItem]
    safety_flag: str
    safety_message: Optional[str] = None
    relevance_label: str
    consultation_id: int
    created_at: str
    generated_by: str
