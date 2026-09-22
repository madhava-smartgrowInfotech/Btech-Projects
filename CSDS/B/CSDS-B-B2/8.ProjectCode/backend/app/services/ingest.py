"""Ingestion: validate, de-duplicate, classify and store readings from any device, then notify listeners."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta

import h3
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import utcnow
from ..core.logging import log_event
from ..ml.registry import get_models
from ..ml.service import Verdict
from ..models import Device, Reading, SyncBatch
from ..schemas.readings import IngestResult, ReadingIn, ReadingResult
from . import events, settings_service
from .carrier import CarrierInfo

log = logging.getLogger("signalscout.ingest")

SOURCE_BY_KIND = {"phone": "phone", "esp32": "esp32", "simulator": "simulator", "replay": "sample_dataset"}
RADIO_FIELDS = ("rsrp", "rsrq", "sinr", "rssi", "cqi")
MAX_AGE = timedelta(days=90)
MAX_FUTURE = timedelta(minutes=10)

# Called after every successful ingest with the (h3_cell, operator) pairs that received readings.
after_ingest_hooks: list[Callable[[Session, set[tuple[str, str]]], None]] = []


@dataclass
class IngestOutcome:
    result: IngestResult
    affected: set[tuple[str, str]] = field(default_factory=set)
    stored: list[Reading] = field(default_factory=list)


def _category(device: Device, item: ReadingIn) -> str:
    if any(getattr(item, f) is not None for f in RADIO_FIELDS):
        return "radio"
    if device.kind == "phone":
        return "probe"
    if device.kind in ("esp32", "simulator"):
        return "wifi"
    return "radio"


def _operator(device: Device, item: ReadingIn, carrier: CarrierInfo | None) -> tuple[str, str | None, str]:
    """(operator, operator_source, link) for one reading."""
    if device.kind == "phone":
        link = carrier.link_for(item.connection_type) if carrier else ((item.connection_type or "unknown").lower() if item.connection_type in ("cellular", "wifi") else "unknown")
        if item.operator:
            return item.operator.strip(), "manual", link
        if carrier and carrier.operator:
            return carrier.operator, "asn", link
        if carrier and carrier.network_name and link == "wifi":
            return carrier.network_name.split(" ", 1)[-1][:80], "asn", link
        return "Unknown", None, link
    if device.kind in ("esp32", "simulator"):
        if any(getattr(item, f) is not None for f in RADIO_FIELDS):
            return (device.config or {}).get("modem_operator") or item.operator or "Unknown", "reported", "cellular"
        return (device.config or {}).get("network_name") or item.operator or "Wi-Fi link", "reported", "wifi"
    return item.operator or "Unknown", "reported", "cellular"


def _apply(reading: Reading, v: Verdict) -> None:
    reading.zone_label = v.label
    reading.zone_confidence = v.confidence
    reading.label_method = v.method
    reading.reasons = v.reasons[:4]
    reading.model_version = v.model_version
    reading.radio_estimate = v.radio_estimate
    reading.radio_estimate_conf = v.radio_estimate_conf


def _classify(db: Session, device: Device, rows: list[tuple[Reading, str]]) -> None:
    models = get_models()
    radio = [r for r, c in rows if c == "radio"]
    probe = [r for r, c in rows if c == "probe"]
    wifi = [r for r, c in rows if c == "wifi"]

    if radio:
        start = min(r.ts for r in radio) - timedelta(seconds=30)
        hist = db.execute(select(Reading.ts, Reading.network_type, Reading.rsrp, Reading.rsrq, Reading.sinr, Reading.rssi,
                                 Reading.cqi, Reading.in_service)
                          .where(Reading.device_id == device.id, Reading.ts >= start, Reading.rsrp.is_not(None) | Reading.rssi.is_not(None))
                          ).all()
        cols = ["ts", "network_type", "rsrp", "rsrq", "sinr", "rssi", "cqi", "in_service"]
        frame = pd.DataFrame([dict(zip(cols, h)) for h in hist] + [{c: getattr(r, c) for c in cols} for r in radio], columns=cols)
        frame["device_key"] = device.id
        frame[list(RADIO_FIELDS)] = frame[list(RADIO_FIELDS)].astype(float)
        target = np.r_[np.zeros(len(hist), bool), np.ones(len(radio), bool)]
        for r, v in zip(radio, models.classify_radio(frame, target)):
            _apply(r, v)

    if probe:
        cfg = settings_service.get_all(db)
        start = min(r.ts for r in probe) - timedelta(minutes=10)
        hist = db.execute(select(Reading.ts, Reading.dl_mbps, Reading.ul_mbps)
                          .where(Reading.device_id == device.id, Reading.ts >= start, Reading.dl_mbps.is_not(None))
                          .order_by(Reading.ts.desc()).limit(3)).all()
        cols = ["ts", "connected", "probes_sent", "probes_ok", "latency_ms", "dl_mbps", "ul_mbps"]
        hist_rows = [{"ts": h.ts, "connected": True, "probes_sent": 0, "probes_ok": 0, "latency_ms": None,
                      "dl_mbps": h.dl_mbps, "ul_mbps": h.ul_mbps} for h in reversed(hist)]
        frame = pd.DataFrame(hist_rows + [{c: getattr(r, c) for c in cols} for r in probe], columns=cols)
        frame["device_key"] = device.id
        for c in ("latency_ms", "dl_mbps", "ul_mbps"):
            frame[c] = frame[c].astype(float)
        target = np.r_[np.zeros(len(hist_rows), bool), np.ones(len(probe), bool)]
        for r, v in zip(probe, models.classify_probes(frame, target, cfg["probe_weak_rtt_ms"], cfg["probe_weak_dl_mbps"])):
            _apply(r, v)

    for r in wifi:
        _apply(r, models.classify_wifi(r.wifi_rssi, r.latency_ms, r.packet_loss, r.connected))


def ingest(db: Session, device: Device, items: list[ReadingIn], carrier: CarrierInfo | None = None,
           publish: bool = True) -> IngestOutcome:
    now = utcnow()
    uuids = [i.client_uuid for i in items]
    existing = set(db.scalars(select(Reading.client_uuid).where(Reading.client_uuid.in_(uuids))).all())
    results: list[ReadingResult] = []
    pending: list[tuple[Reading, str, ReadingResult]] = []
    seen: set[str] = set()
    duplicates = rejected = 0
    source = SOURCE_BY_KIND.get(device.kind, device.kind)
    link_seen = None

    for item in items:
        if item.client_uuid in existing or item.client_uuid in seen:
            duplicates += 1
            results.append(ReadingResult(client_uuid=item.client_uuid, status="duplicate"))
            continue
        seen.add(item.client_uuid)
        error = None
        if item.ts > now + MAX_FUTURE:
            error = "Timestamp is in the future - check the device clock"
        elif item.ts < now - MAX_AGE and device.kind != "replay":
            error = "Reading is older than 90 days"
        elif item.lat == 0 and item.lon == 0:
            error = "No GPS position"
        if error:
            rejected += 1
            results.append(ReadingResult(client_uuid=item.client_uuid, status="rejected", error=error))
            continue
        operator, op_source, link = _operator(device, item, carrier)
        link_seen = link
        reading = Reading(
            client_uuid=item.client_uuid, device_id=device.id, source=source, ts=item.ts, received_at=now,
            lat=item.lat, lon=item.lon, accuracy_m=item.accuracy_m, h3_cell=h3.latlng_to_cell(item.lat, item.lon, settings.h3_resolution),
            operator=operator, operator_source=op_source, asn=carrier.asn if carrier else None, link=link,
            network_type=item.network_type, in_service=item.in_service, connected=item.connected,
            cell_id=item.cell_id, tac=item.tac, pci=item.pci, earfcn=item.earfcn,
            rssi=item.rssi, rsrp=item.rsrp, rsrq=item.rsrq, sinr=item.sinr, cqi=item.cqi,
            latency_ms=item.latency_ms, jitter_ms=item.jitter_ms, packet_loss=item.packet_loss,
            probes_sent=item.probes_sent, probes_ok=item.probes_ok, dl_mbps=item.dl_mbps, ul_mbps=item.ul_mbps,
            effective_type=item.effective_type, downlink_est=item.downlink_est, rtt_est=item.rtt_est,
            wifi_rssi=item.wifi_rssi, ble_rssi=item.ble_rssi,
        )
        res = ReadingResult(client_uuid=item.client_uuid, status="accepted")
        pending.append((reading, _category(device, item), res))
        results.append(res)

    stored = [p[0] for p in pending]
    if pending:
        pending.sort(key=lambda p: p[0].ts)
        _classify(db, device, [(r, c) for r, c, _ in pending])
        for r, _, res in pending:
            res.zone_label, res.zone_confidence, res.label_method = r.zone_label, r.zone_confidence, r.label_method
            res.radio_estimate, res.radio_estimate_conf, res.reasons = r.radio_estimate, r.radio_estimate_conf, r.reasons or []
        db.add_all(stored)
        device.readings_count = (device.readings_count or 0) + len(stored)
    device.last_seen_at = now
    device.last_sync_at = now
    db.add(SyncBatch(device_id=device.id, ts=now, received=len(items), accepted=len(stored), duplicates=duplicates,
                     rejected=rejected, oldest_reading=min((r.ts for r in stored), default=None)))
    db.commit()

    affected = {(r.h3_cell, r.operator) for r in stored if r.zone_label and _counts_for_coverage(r)}
    for hook in after_ingest_hooks:
        try:
            hook(db, affected)
        except Exception:
            log.exception("after-ingest hook failed")
    if publish and stored:
        events.publish("readings", [live_view(r, device) for r in stored[-200:]])
    if stored or rejected:
        log_event(log, "ingest", device=device.id, kind=device.kind, accepted=len(stored), duplicates=duplicates, rejected=rejected)

    return IngestOutcome(IngestResult(received=len(items), accepted=len(stored), duplicates=duplicates, rejected=rejected,
                                      operator=stored[-1].operator if stored else None, link=link_seen, results=results),
                         affected, stored)


def _counts_for_coverage(r: Reading) -> bool:
    """Phone readings taken over Wi-Fi say nothing about the mobile network."""
    return not (r.source == "phone" and r.link == "wifi")


def live_view(r: Reading, device: Device | None = None) -> dict:
    return {"id": r.id, "ts": r.ts.isoformat() + "Z", "lat": r.lat, "lon": r.lon, "label": r.zone_label, "confidence": r.zone_confidence,
            "operator": r.operator, "source": r.source, "link": r.link, "device_id": r.device_id,
            "device": device.name if device else None, "rsrp": r.rsrp, "latency_ms": r.latency_ms, "dl_mbps": r.dl_mbps,
            "wifi_rssi": r.wifi_rssi, "connected": r.connected}
