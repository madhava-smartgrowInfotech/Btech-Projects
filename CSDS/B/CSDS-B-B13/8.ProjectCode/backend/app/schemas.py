"""Pydantic request/response models."""
from pydantic import BaseModel, Field


class Credentials(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)


class TokenOut(BaseModel):
    token: str
    email: str


class ManualTarget(BaseModel):
    name: str
    base_url: str
    endpoints: list[dict] = []
    auth: dict = {}
    known_vulns: list[dict] = []


class ImportSpec(BaseModel):
    name: str
    spec_text: str
    base_url: str | None = None
    auth: dict = {}
    known_vulns: list[dict] = []


class ScanCreate(BaseModel):
    target_id: int
    authorized: bool = False
