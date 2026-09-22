from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base, utcnow

SOURCES = ("phone", "esp32", "simulator", "sample_dataset")


class Reading(Base):
    """One observation. Radio metrics are filled when the device reports them (datasets, modems);
    service metrics come from the phone probe; Wi-Fi/BLE from ESP32 nodes."""
    __tablename__ = "readings"
    __table_args__ = (
        Index("ix_readings_cell_op_ts", "h3_cell", "operator", "ts"),
        Index("ix_readings_device_ts", "device_id", "ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_uuid: Mapped[str] = mapped_column(String(64), unique=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(20), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # position
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    h3_cell: Mapped[str] = mapped_column(String(20))

    # network identity
    operator: Mapped[str] = mapped_column(String(80), default="Unknown")
    operator_source: Mapped[str | None] = mapped_column(String(20), nullable=True)   # asn / manual / reported
    asn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    link: Mapped[str] = mapped_column(String(16), default="unknown")                 # cellular / wifi / unknown
    network_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    in_service: Mapped[bool] = mapped_column(Boolean, default=True)
    connected: Mapped[bool] = mapped_column(Boolean, default=True)

    # radio metrics (when available)
    cell_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tac: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pci: Mapped[int | None] = mapped_column(Integer, nullable=True)
    earfcn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rssi: Mapped[float | None] = mapped_column(Float, nullable=True)
    rsrp: Mapped[float | None] = mapped_column(Float, nullable=True)
    rsrq: Mapped[float | None] = mapped_column(Float, nullable=True)
    sinr: Mapped[float | None] = mapped_column(Float, nullable=True)
    cqi: Mapped[float | None] = mapped_column(Float, nullable=True)

    # service metrics (phone probe)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    jitter_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    packet_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    probes_sent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    probes_ok: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dl_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    ul_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_type: Mapped[str | None] = mapped_column(String(12), nullable=True)
    downlink_est: Mapped[float | None] = mapped_column(Float, nullable=True)
    rtt_est: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ESP32 link metrics
    wifi_rssi: Mapped[float | None] = mapped_column(Float, nullable=True)
    ble_rssi: Mapped[float | None] = mapped_column(Float, nullable=True)

    # classification
    zone_label: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)   # Strong / Weak / Dead
    zone_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    label_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    radio_estimate: Mapped[str | None] = mapped_column(String(10), nullable=True)
    radio_estimate_conf: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(60), nullable=True)
    reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
