"""ParkSure Pydantic schemas with strict input validation."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LocationIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    address: str = Field(default="", max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    capacity: int = Field(ge=1, le=5000)
    price_per_hour: float = Field(ge=0.5, le=100)
    buffer_size: int = Field(default=1, ge=0, le=20)


class ReservationIn(BaseModel):
    location_id: int = Field(ge=1)
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be after start_time")
        return v
