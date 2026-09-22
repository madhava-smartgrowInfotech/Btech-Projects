from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .common import ORMModel, UTCDateTime


class DeviceOut(ORMModel):
    id: int
    owner_id: int
    owner_name: str | None = None
    kind: str
    name: str
    api_key_prefix: str
    hardware: str | None
    firmware: str | None
    fixed_lat: float | None
    fixed_lon: float | None
    config: dict
    is_active: bool
    created_at: UTCDateTime
    last_seen_at: UTCDateTime | None
    last_sync_at: UTCDateTime | None
    readings_count: int
    online: bool = False


class DeviceCreate(BaseModel):
    kind: Literal["esp32", "simulator"] = "esp32"
    name: str = Field(min_length=2, max_length=120)
    fixed_lat: float | None = Field(default=None, ge=-90, le=90)
    fixed_lon: float | None = Field(default=None, ge=-180, le=180)
    network_name: str | None = Field(default=None, max_length=80)


class PhonePair(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    hardware: str | None = Field(default=None, max_length=255, description="Browser / phone description")


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    fixed_lat: float | None = Field(default=None, ge=-90, le=90)
    fixed_lon: float | None = Field(default=None, ge=-180, le=180)
    network_name: str | None = Field(default=None, max_length=80)
    is_active: bool | None = None


class DeviceWithKey(BaseModel):
    device: DeviceOut
    api_key: str = Field(description="Shown once - store it on the device")


class SyncBatchOut(ORMModel):
    id: int
    ts: UTCDateTime
    received: int
    accepted: int
    duplicates: int
    rejected: int
    oldest_reading: UTCDateTime | None
