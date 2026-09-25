from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class GuardianIn(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_chat_id: Optional[str] = None


class GuardianOut(GuardianIn):
    id: int

    class Config:
        from_attributes = True


class RoutePlanIn(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float


class SosStartIn(BaseModel):
    lat: float
    lng: float
    trigger: str = "manual"  # manual | safephrase


class LocationUpdateIn(BaseModel):
    lat: float
    lng: float


class AiAskIn(BaseModel):
    question: str
    lat: Optional[float] = None
    lng: Optional[float] = None
