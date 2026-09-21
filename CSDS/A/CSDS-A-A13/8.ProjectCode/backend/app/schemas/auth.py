from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_email(value: str) -> str:
    value = value.strip().lower()
    if not _EMAIL.match(value):
        raise ValueError("enter a valid email address")
    return value


class LoginIn(BaseModel):
    email: str
    password: str = Field(min_length=1)

    _email = field_validator("email")(_clean_email)


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=72)

    _email = field_validator("email")(_clean_email)

    @field_validator("full_name")
    @classmethod
    def _name(cls, value: str) -> str:
        return " ".join(value.split())


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Literal["admin", "invigilator"]
    status: Literal["active", "pending", "disabled"]
    created_at: datetime
    last_login_at: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserOut


class UserCreateIn(RegisterIn):
    role: Literal["admin", "invigilator"] = "invigilator"


class UserUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role: Literal["admin", "invigilator"] | None = None
    status: Literal["active", "pending", "disabled"] | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
