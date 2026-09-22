from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Language = Literal["en", "hi", "te"]


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    phone: str = Field(pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile number")
    email: EmailStr | None = None
    password: str = Field(min_length=8, max_length=72)
    pin: str = Field(pattern=r"^\d{4}$", description="4-digit sandbox UPI PIN")
    language: Language = "en"

    @field_validator("full_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Name is too short")
        return v


class LoginIn(BaseModel):
    identifier: str = Field(min_length=3, max_length=120, description="Mobile number or email")
    password: str = Field(min_length=1, max_length=72)


class MeOut(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str | None
    role: str
    is_sample: bool
    upi_id: str
    balance: float
    language: Language
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MeOut


class PinChangeIn(BaseModel):
    current_pin: str = Field(pattern=r"^\d{4}$")
    new_pin: str = Field(pattern=r"^\d{4}$")
