"""Evidence bundle for a complaint: what was measured in the zone, when, by how many devices, and what it means."""
from __future__ import annotations

from collections import Counter
from datetime import datetime

import h3
import numpy as np
from sqlalchemy.orm import Session

from ..models import Reading
from .suggest_service import suggest_for


def _stat(values: list[float], fn) -> float | None:
    vals = [v for v in values if v is not None]
    return round(float(fn(vals)), 2) if vals else None


def _iso(d: datetime | None) -> str | None:
    return d.isoformat() + "Z" if d else None


def build_evidence(db: Session, readings: list[Reading], cell: str, operator: str, with_suggestion: bool = True) -> dict:
    readings = sorted(readings, key=lambda r: r.ts)
    n = len(readings)
    labels = Counter(r.zone_label for r in readings)
    lat, lon = h3.cell_to_latlng(cell)
    probe = [r for r in readings if r.source == "phone"]
    radio = [r for r in readings if r.rsrp is not None or r.rssi is not None and r.wifi_rssi is None]
    wifi = [r for r in readings if r.wifi_rssi is not None or r.source in ("esp32", "simulator")]
    ev: dict = {
        "zone": {"h3_cell": cell, "resolution": h3.get_resolution(cell), "center": [lat, lon],
                 "area_km2": round(h3.cell_area(cell, unit="km^2"), 3), "operator": operator},
        "window": {"first": _iso(readings[0].ts) if n else None, "last": _iso(readings[-1].ts) if n else None,
                   "minutes": round((readings[-1].ts - readings[0].ts).total_seconds() / 60, 1) if n > 1 else 0},
        "readings": n,
        "classes": {k: labels.get(k, 0) for k in ("Strong", "Weak", "Dead")},
        "bad_share": round((labels.get("Weak", 0) + labels.get("Dead", 0)) / max(n, 1), 3),
        "dead_share": round(labels.get("Dead", 0) / max(n, 1), 3),
        "devices": len({r.device_id for r in readings}),
        "sources": dict(Counter(r.source for r in readings)),
        "methods": dict(Counter(r.label_method for r in readings if r.label_method)),
        "model_versions": sorted({r.model_version for r in readings if r.model_version}),
        "mean_confidence": _stat([r.zone_confidence for r in readings], np.mean),
    }
    if probe:
        ev["service"] = {
            "readings": len(probe),
            "no_connectivity_share": round(sum(1 for r in probe if not r.connected or (r.probes_sent and not r.probes_ok)) / len(probe), 3),
            "latency_median_ms": _stat([r.latency_ms for r in probe], np.median),
            "latency_p90_ms": _stat([r.latency_ms for r in probe], lambda v: np.percentile(v, 90)),
            "jitter_median_ms": _stat([r.jitter_ms for r in probe], np.median),
            "packet_loss_mean": _stat([r.packet_loss for r in probe], np.mean),
            "download_median_mbps": _stat([r.dl_mbps for r in probe], np.median),
            "upload_median_mbps": _stat([r.ul_mbps for r in probe], np.median),
            "asns": sorted({r.asn for r in probe if r.asn}),
            "radio_estimate": dict(Counter(r.radio_estimate for r in probe if r.radio_estimate)),
        }
    if radio:
        ev["radio"] = {
            "readings": len(radio),
            "rsrp_median_dbm": _stat([r.rsrp for r in radio], np.median), "rsrp_min_dbm": _stat([r.rsrp for r in radio], np.min),
            "rsrq_median_db": _stat([r.rsrq for r in radio], np.median), "sinr_median_db": _stat([r.sinr for r in radio], np.median),
            "rssi_median_dbm": _stat([r.rssi for r in radio], np.median),
            "cell_ids": sorted({r.cell_id for r in radio if r.cell_id})[:20], "pcis": sorted({r.pci for r in radio if r.pci})[:20],
            "earfcns": sorted({r.earfcn for r in radio if r.earfcn})[:10],
            "network_types": dict(Counter(r.network_type for r in radio if r.network_type)),
        }
    if wifi:
        ev["wifi"] = {"readings": len(wifi), "rssi_median_dbm": _stat([r.wifi_rssi for r in wifi], np.median),
                      "latency_median_ms": _stat([r.latency_ms for r in wifi], np.median),
                      "offline_share": round(sum(1 for r in wifi if not r.connected) / len(wifi), 3)}
    reasons = Counter(x for r in readings if r.zone_label in ("Weak", "Dead") for x in (r.reasons or [])[:1])
    ev["top_reasons"] = [{"reason": k, "count": v} for k, v in reasons.most_common(4)]
    step = max(1, n // 120)
    ev["series"] = [{"ts": _iso(r.ts), "label": r.zone_label, "rsrp": r.rsrp, "latency_ms": r.latency_ms, "dl_mbps": r.dl_mbps,
                     "wifi_rssi": r.wifi_rssi} for r in readings[::step]]
    ev["samples"] = [{"ts": _iso(r.ts), "lat": round(r.lat, 6), "lon": round(r.lon, 6), "label": r.zone_label, "confidence": r.zone_confidence,
                      "rsrp": r.rsrp, "rsrq": r.rsrq, "sinr": r.sinr, "latency_ms": r.latency_ms, "dl_mbps": r.dl_mbps, "wifi_rssi": r.wifi_rssi,
                      "cell_id": r.cell_id, "source": r.source} for r in readings[-50:]]
    if with_suggestion:
        try:
            s = suggest_for(db, lat, lon, operator)
            ev["nearest_strong_spot"] = {k: s.get(k) for k in ("found", "status", "message", "lat", "lon", "distance_m", "direction",
                                                                "predicted", "predicted_mbps", "probability", "target")}
        except Exception:
            ev["nearest_strong_spot"] = None
    return ev


def summary_text(ev: dict, operator: str, ref: str | None = None) -> str:
    """Plain-language complaint text written from the evidence (deterministic)."""
    c = ev["classes"]
    parts = [f"{'Complaint ' + ref + ': ' if ref else ''}poor {operator} coverage in zone {ev['zone']['h3_cell']} "
             f"(around {ev['zone']['center'][0]:.5f}, {ev['zone']['center'][1]:.5f})."]
    parts.append(f"{ev['readings']} readings from {ev['devices']} device(s) between {(ev['window']['first'] or '')[:16].replace('T', ' ')} and "
                 f"{(ev['window']['last'] or '')[:16].replace('T', ' ')} UTC: {c['Dead']} Dead, {c['Weak']} Weak, {c['Strong']} Strong "
                 f"({ev['bad_share']:.0%} Weak or Dead).")
    s = ev.get("service")
    if s:
        bits = []
        if s["no_connectivity_share"]:
            bits.append(f"no connection in {s['no_connectivity_share']:.0%} of phone readings")
        if s["latency_median_ms"] is not None:
            bits.append(f"median latency {s['latency_median_ms']:.0f} ms")
        if s["download_median_mbps"] is not None:
            bits.append(f"median download {s['download_median_mbps']:.1f} Mbps")
        if bits:
            parts.append("Measured service: " + ", ".join(bits) + ".")
    r = ev.get("radio")
    if r and r["rsrp_median_dbm"] is not None:
        parts.append(f"Radio: median RSRP {r['rsrp_median_dbm']:.0f} dBm (minimum {r['rsrp_min_dbm']:.0f} dBm)"
                     + (f", median SINR {r['sinr_median_db']:.0f} dB" if r["sinr_median_db"] is not None else "")
                     + (f", serving cells {', '.join(map(str, r['cell_ids'][:5]))}" if r["cell_ids"] else "") + ".")
    w = ev.get("wifi")
    if w and w["rssi_median_dbm"] is not None:
        parts.append(f"Wi-Fi link: median RSSI {w['rssi_median_dbm']:.0f} dBm, offline {w['offline_share']:.0%} of the time.")
    spot = ev.get("nearest_strong_spot") or {}
    if spot.get("found") and spot.get("status") == "found":
        parts.append(f"Nearest predicted strong signal: about {spot['distance_m']:.0f} m {spot.get('direction') or ''}.")
    return " ".join(parts)
