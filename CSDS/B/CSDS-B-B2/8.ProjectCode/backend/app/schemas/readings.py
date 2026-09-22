from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from .common import ORMModel, UTCDateTime


def _to_naive_utc(v: datetime) -> datetime:
    return v.astimezone(timezone.utc).replace(tzinfo=None) if v.tzinfo else v


class ReadingIn(BaseModel):
    """One observation from a phone probe, an ESP32 node or a replayed trace. Unknown metrics are omitted."""
    client_uuid: str = Field(min_length=8, max_length=64, description="Generated on the device; re-sending the same UUID is ignored")
    ts: datetime
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0, le=100000)

    operator: str | None = Field(default=None, max_length=80, description="Set when the user picked the operator manually")
    network_type: str | None = Field(default=None, max_length=20)
    connection_type: str | None = Field(default=None, max_length=20, description="Browser hint: cellular / wifi / ...")
    in_service: bool = True
    connected: bool = True

    cell_id: int | None = None
    tac: int | None = None
    pci: int | None = None
    earfcn: int | None = None
    rssi: float | None = None
    rsrp: float | None = None
    rsrq: float | None = None
    sinr: float | None = None
    cqi: float | None = None

    latency_ms: float | None = Field(default=None, ge=0, le=120000)
    jitter_ms: float | None = Field(default=None, ge=0, le=120000)
    packet_loss: float | None = Field(default=None, ge=0, le=1)
    probes_sent: int | None = Field(default=None, ge=0, le=20)
    probes_ok: int | None = Field(default=None, ge=0, le=20)
    dl_mbps: float | None = Field(default=None, ge=0, le=10000)
    ul_mbps: float | None = Field(default=None, ge=0, le=10000)
    effective_type: str | None = Field(default=None, max_length=12)
    downlink_est: float | None = Field(default=None, ge=0, le=10000)
    rtt_est: float | None = Field(default=None, ge=0, le=120000)

    wifi_rssi: float | None = Field(default=None, ge=-120, le=0)
    ble_rssi: float | None = Field(default=None, ge=-120, le=0)

    @field_validator("ts")
    @classmethod
    def utc(cls, v: datetime) -> datetime:
        return _to_naive_utc(v)


class IngestBatch(BaseModel):
    readings: list[ReadingIn] = Field(min_length=1, max_length=500)


class NodeReading(BaseModel):
    """Compact format sent by the ESP32 firmware (and the simulator)."""
    seq: int = Field(ge=0)
    ts: datetime | None = None                   # from NTP / GPS; missing -> time of receipt
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    wifi_rssi: float | None = Field(default=None, ge=-120, le=0)
    ble_rssi: float | None = Field(default=None, ge=-120, le=0)
    latency_ms: float | None = Field(default=None, ge=0, le=120000)
    packet_loss: float | None = Field(default=None, ge=0, le=1)
    connected: bool = True
    cell_rssi: float | None = Field(default=None, ge=-120, le=0, description="From an optional cellular modem (AT+CSQ)")
    cell_type: str | None = Field(default=None, max_length=20)

    @field_validator("ts")
    @classmethod
    def utc(cls, v: datetime | None) -> datetime | None:
        return _to_naive_utc(v) if v else v


class NodeBatch(BaseModel):
    firmware: str | None = Field(default=None, max_length=60)
    uptime_s: int | None = Field(default=None, ge=0)
    network_name: str | None = Field(default=None, max_length=80, description="The Wi-Fi network the node monitors")
    readings: list[NodeReading] = Field(min_length=1, max_length=500)


class ReadingResult(BaseModel):
    client_uuid: str
    status: str                                  # accepted / duplicate / rejected
    zone_label: str | None = None
    zone_confidence: float | None = None
    label_method: str | None = None
    radio_estimate: str | None = None
    radio_estimate_conf: float | None = None
    reasons: list[str] = []
    error: str | None = None


class IngestResult(BaseModel):
    received: int
    accepted: int
    duplicates: int
    rejected: int
    operator: str | None = None
    link: str | None = None
    results: list[ReadingResult]


class ReadingOut(ORMModel):
    id: int
    client_uuid: str
    device_id: int
    source: str
    ts: UTCDateTime
    lat: float
    lon: float
    accuracy_m: float | None
    h3_cell: str
    operator: str
    link: str
    network_type: str | None
    connected: bool
    in_service: bool
    rsrp: float | None
    rsrq: float | None
    sinr: float | None
    rssi: float | None
    latency_ms: float | None
    jitter_ms: float | None
    packet_loss: float | None
    dl_mbps: float | None
    ul_mbps: float | None
    wifi_rssi: float | None
    zone_label: str | None
    zone_confidence: float | None
    label_method: str | None
    radio_estimate: str | None
    radio_estimate_conf: float | None
    reasons: list | None
