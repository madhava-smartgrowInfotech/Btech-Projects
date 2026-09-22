"""Phone-probe readings: measured service-quality bands and speed-test features for the radio estimate.

A browser cannot read radio metrics, so a probe reading is classified from what it measures directly:

    Dead    no connectivity - the browser is offline or at least 2 of 3 latency probes fail
    Weak    median round-trip above 400 ms (ITU-T G.114 limit for interactive voice), download below
            2 Mbps (India's broadband minimum since 2024), or 1 of 3 probes lost
    Strong  otherwise

The radio-condition estimate (a model trained on drive-test traces) uses only speed-test features,
built by the same functions here during training and at inference.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .signal_ranges import DEAD, STRONG, WEAK

DEFAULT_WEAK_RTT_MS = 400.0
DEFAULT_WEAK_DL_MBPS = 2.0

# Speed-test features: the current test plus the two previous tests of the same device (about a minute apart).
SPEED_FEATURES = ["dl_mbps", "ul_mbps", "dl_prev1", "dl_prev2", "dl_med3", "dl_min3", "ul_med3", "dl_log", "dl_zero"]


@dataclass
class QualityVerdict:
    label: int
    confidence: float
    reasons: list[str]


def classify_probe(connected: bool, probes_sent: int, probes_ok: int, rtt_ms: float | None,
                   dl_mbps: float | None, weak_rtt_ms: float = DEFAULT_WEAK_RTT_MS,
                   weak_dl_mbps: float = DEFAULT_WEAK_DL_MBPS) -> QualityVerdict:
    """Measured class of one probe reading, with a confidence from probe agreement and distance to the band edges."""
    probes_sent = max(int(probes_sent or 0), 0)
    probes_ok = max(min(int(probes_ok or 0), probes_sent), 0)
    lost = probes_sent - probes_ok
    if not connected or (probes_sent and lost >= 2) or (probes_sent and probes_ok == 0):
        reason = "Phone reported no connection" if not connected else f"{lost} of {probes_sent} latency probes failed"
        conf = 1.0 if not connected else (0.8 + 0.2 * lost / max(probes_sent, 1))
        return QualityVerdict(DEAD, round(min(conf, 1.0), 3), [reason])

    reasons, margins = [], []
    weak = False
    if lost == 1:
        weak = True
        reasons.append(f"1 of {probes_sent} latency probes lost")
        margins.append(0.6)
    if rtt_ms is not None:
        if rtt_ms > weak_rtt_ms:
            weak = True
            reasons.append(f"Round-trip {rtt_ms:.0f} ms is above {weak_rtt_ms:.0f} ms")
        margins.append(min(abs(np.log(max(rtt_ms, 1) / weak_rtt_ms)) / np.log(2), 1.0))
    if dl_mbps is not None:
        if dl_mbps < weak_dl_mbps:
            weak = True
            reasons.append(f"Download {dl_mbps:.2f} Mbps is below {weak_dl_mbps:g} Mbps")
        margins.append(min(abs(np.log(max(dl_mbps, 0.01) / weak_dl_mbps)) / np.log(4), 1.0))
    if not margins:
        return QualityVerdict(WEAK if weak else STRONG, 0.5, reasons or ["Connected, but no latency or speed measured"])
    if not weak:
        reasons.append("Latency and speed within the Strong band")
    # Evidence far from the band edges -> high confidence; values sitting on an edge -> about 0.55.
    margin = float(np.mean(margins)) if not weak else float(np.max(margins))
    return QualityVerdict(WEAK if weak else STRONG, round(0.55 + 0.45 * margin, 3), reasons)


def speed_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features from a device's consecutive speed tests. df needs device_key, ts, dl_mbps, ul_mbps."""
    d = df[["device_key", "ts", "dl_mbps", "ul_mbps"]].copy()
    d["_order"] = np.arange(len(d))
    d = d.sort_values(["device_key", "ts", "_order"], kind="stable")
    g = d.groupby("device_key", sort=False)["dl_mbps"]
    d["dl_prev1"] = g.shift(1)
    d["dl_prev2"] = g.shift(2)
    last3 = pd.concat([d.dl_mbps, d.dl_prev1, d.dl_prev2], axis=1)
    d["dl_med3"] = last3.median(axis=1, skipna=True)
    d["dl_min3"] = last3.min(axis=1, skipna=True)
    ul = d.groupby("device_key", sort=False)["ul_mbps"]
    d["ul_med3"] = pd.concat([d.ul_mbps, ul.shift(1), ul.shift(2)], axis=1).median(axis=1, skipna=True)
    d["dl_log"] = np.log10(d.dl_mbps.clip(lower=0.01))
    d["dl_zero"] = (d.dl_mbps < 0.05).astype(float)
    d = d.sort_values("_order")
    d.index = df.index
    return d[SPEED_FEATURES].astype(float)
