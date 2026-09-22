"""Documented signal-quality ranges used to label readings Strong / Weak / Dead.

The bands follow the 3GPP measurement reporting ranges (TS 36.133 for LTE RSRP/RSRQ/SINR,
TS 38.133 for NR SS-RSRP/SS-RSRQ/SS-SINR, TS 25.133 for UMTS RSCP and Ec/No, TS 45.008 for
GSM RSSI) and the coverage bands operators commonly use for planning:

    LTE / NR   RSRP  >= -100 Strong | -115..-100 Weak | < -115 Dead
               RSRQ  >= -15  Strong | < -15 Weak
               SINR  >= 5    Strong | -3..5 Weak      | < -3 Dead
    UMTS/HSPA  RSCP  >= -95  Strong | -105..-95 Weak  | < -105 Dead
               Ec/No >= -14  Strong | < -14 Weak
    GSM/EDGE   RSSI  >= -85  Strong | -100..-85 Weak  | < -100 Dead

Each available metric is mapped to a class and the reading takes the worst class. A reading
taken while the phone has no service is always Dead. Wideband LTE RSSI and CQI are not
quality indicators on their own, so they are features for the model but do not set labels.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

STRONG, WEAK, DEAD = 0, 1, 2
CLASSES = ["Strong", "Weak", "Dead"]
FAMILIES = ["2g", "3g", "lte_nr"]

# metric -> (weak_below, dead_below). value >= weak_below is Strong, value < dead_below is Dead.
RANGES: dict[str, dict[str, tuple[float, float | None]]] = {
    "lte_nr": {"level": (-100.0, -115.0), "quality": (-15.0, None), "sinr": (5.0, -3.0)},
    "3g": {"level": (-95.0, -105.0), "quality": (-14.0, None)},
    "2g": {"level": (-85.0, -100.0)},
}

# Physically valid reporting ranges; anything outside is a sentinel / glitch and treated as missing.
VALID: dict[str, dict[str, tuple[float, float]]] = {
    "lte_nr": {"level": (-140, -44), "quality": (-34, 3), "sinr": (-30, 40), "rssi": (-120, -20), "cqi": (0, 15)},
    "3g": {"level": (-120, -25), "quality": (-24, 0), "sinr": (-30, 40), "rssi": (-120, -20), "cqi": (0, 15)},
    "2g": {"level": (-113, -51), "quality": (-40, 0), "sinr": (-30, 40), "rssi": (-113, -51), "cqi": (0, 15)},
}

METRIC_NAMES = {
    "lte_nr": {"level": "RSRP", "quality": "RSRQ", "sinr": "SINR"},
    "3g": {"level": "RSCP", "quality": "Ec/No", "sinr": "SINR"},
    "2g": {"level": "RSSI", "quality": "quality", "sinr": "SINR"},
}

# Wi-Fi / BLE link readings from ESP32 nodes (different scale from cellular - separate bands).
WIFI_RANGES = {"rssi": (-67.0, -80.0)}
WIFI_LATENCY_WEAK_MS = 300.0
WIFI_LOSS_WEAK = 0.2

# Map the network-type strings phones, ESP32 modems and datasets report to a technology family.
NETWORK_TYPE_FAMILY: dict[str, str] = {
    **{k: "2g" for k in ("GSM", "GPRS", "EDGE", "2G", "CDMA", "1XRTT", "IDEN")},
    **{k: "3g" for k in ("UMTS", "WCDMA", "HSPA", "HSPA+", "HSPAP", "HSDPA", "HSUPA", "TD_SCDMA", "TDSCDMA", "EVDO", "EVDO_0", "EVDO_A", "EVDO_B", "EHRPD", "3G")},
    **{k: "lte_nr" for k in ("LTE", "4G", "LTE_CA", "LTE+", "NR", "5G", "NR_NSA", "NR_SA", "5G_NSA", "5G_SA")},
}


def family_of(network_type: str | None) -> str | None:
    if not network_type:
        return None
    return NETWORK_TYPE_FAMILY.get(str(network_type).strip().upper())


def clean_metric(family: str, metric: str, value: float | None) -> float | None:
    """Return the value if it is inside the valid reporting range, else None."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(v):
        return None
    lo, hi = VALID.get(family, VALID["lte_nr"]).get(metric, (-np.inf, np.inf))
    return v if lo <= v <= hi else None


def _metric_class(values: np.ndarray, weak_below: float, dead_below: float | None) -> np.ndarray:
    cls = np.where(values >= weak_below, STRONG, WEAK)
    if dead_below is not None:
        cls = np.where(values < dead_below, DEAD, cls)
    return np.where(np.isnan(values), -1, cls)


def label_arrays(family: np.ndarray, level: np.ndarray, quality: np.ndarray, sinr: np.ndarray,
                 in_service: np.ndarray | None = None) -> np.ndarray:
    """Vectorised labelling. Returns 0/1/2, or -1 where no labelling metric is available."""
    family = np.asarray(family, dtype=object)
    metrics = {"level": np.asarray(level, float), "quality": np.asarray(quality, float), "sinr": np.asarray(sinr, float)}
    out = np.full(len(family), -1, dtype=int)
    for fam, bands in RANGES.items():
        mask = family == fam
        if not mask.any():
            continue
        worst = np.full(mask.sum(), -1, dtype=int)
        for metric, (weak_below, dead_below) in bands.items():
            worst = np.maximum(worst, _metric_class(metrics[metric][mask], weak_below, dead_below))
        out[mask] = worst
    if in_service is not None:
        out = np.where(np.asarray(in_service, bool), out, DEAD)
    return out


@dataclass
class RangeVerdict:
    label: int | None           # 0/1/2 or None when nothing can be judged
    reasons: list[str]          # human-readable, e.g. "RSRP -118 dBm is below -115 dBm (Dead)"


def classify_by_ranges(family: str | None, level: float | None = None, quality: float | None = None,
                       sinr: float | None = None, in_service: bool = True) -> RangeVerdict:
    """Scalar version with explanations - used for evidence text and provisional labels."""
    if not in_service:
        return RangeVerdict(DEAD, ["No mobile service at this point"])
    if family not in RANGES:
        return RangeVerdict(None, ["Unknown network technology"])
    names = METRIC_NAMES[family]
    worst, reasons = -1, []
    values = {"level": level, "quality": quality, "sinr": sinr}
    for metric, (weak_below, dead_below) in RANGES[family].items():
        v = clean_metric(family, metric, values[metric])
        if v is None:
            continue
        unit = "dBm" if metric == "level" else "dB"
        if dead_below is not None and v < dead_below:
            cls, text = DEAD, f"{names[metric]} {v:g} {unit} is below {dead_below:g} {unit}"
        elif v < weak_below:
            cls, text = WEAK, f"{names[metric]} {v:g} {unit} is below {weak_below:g} {unit}"
        else:
            cls, text = STRONG, f"{names[metric]} {v:g} {unit} is at or above {weak_below:g} {unit}"
        if cls > worst:
            worst, reasons = cls, [text]
        elif cls == worst:
            reasons.append(text)
    return RangeVerdict(None if worst < 0 else worst, reasons or ["No signal metric reported"])


def classify_wifi(rssi: float | None, latency_ms: float | None = None, packet_loss: float | None = None,
                  connected: bool = True) -> RangeVerdict:
    """Wi-Fi / BLE link quality for ESP32 node readings."""
    if not connected or rssi is None:
        return RangeVerdict(DEAD, ["Node is not connected to Wi-Fi"])
    weak_below, dead_below = WIFI_RANGES["rssi"]
    if rssi < dead_below:
        label, reasons = DEAD, [f"Wi-Fi RSSI {rssi:g} dBm is below {dead_below:g} dBm"]
    elif rssi < weak_below:
        label, reasons = WEAK, [f"Wi-Fi RSSI {rssi:g} dBm is below {weak_below:g} dBm"]
    else:
        label, reasons = STRONG, [f"Wi-Fi RSSI {rssi:g} dBm is at or above {weak_below:g} dBm"]
    if label == STRONG and latency_ms is not None and latency_ms > WIFI_LATENCY_WEAK_MS:
        label, reasons = WEAK, [f"Latency {latency_ms:.0f} ms is above {WIFI_LATENCY_WEAK_MS:.0f} ms"]
    if label == STRONG and packet_loss is not None and packet_loss > WIFI_LOSS_WEAK:
        label, reasons = WEAK, [f"Packet loss {packet_loss:.0%} is above {WIFI_LOSS_WEAK:.0%}"]
    return RangeVerdict(label, reasons)
