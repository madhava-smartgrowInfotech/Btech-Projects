"""Feature building for the zone classifier - shared by training (ml/) and live inference (app/).

Input: one row per reading with columns
    device_key  any hashable id of the device / trace (rolling windows never cross devices)
    ts          timestamp (datetime64)
    family      "2g" | "3g" | "lte_nr"
    level       RSRP (LTE/NR), RSCP (3G) or RSSI (2G) in dBm
    quality     RSRQ (LTE/NR) or Ec/No (3G) in dB
    sinr        SINR / RSSNR in dB
    rssi        received signal strength indicator in dBm
    cqi         channel quality indicator 0-15
Missing metrics are NaN. Rolling statistics look back over the device's last 30 seconds, which
keeps them comparable between 1 Hz drive-test traces and a phone sampling every few seconds.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .signal_ranges import FAMILIES, RANGES

BASE_METRICS = ["level", "quality", "sinr", "rssi", "cqi"]
RANGE_METRICS = ["level", "quality", "sinr"]
WINDOW = "30s"
ROLLING = [("level", "median"), ("level", "min"), ("level", "std"), ("quality", "median"),
           ("sinr", "median"), ("rssi", "median")]

FEATURES = (
    [f"fam_{f}" for f in FAMILIES]
    + BASE_METRICS
    + [f"has_{m}" for m in BASE_METRICS]
    + [f"{col}_{stat}30" for col, stat in ROLLING]
    + ["level_dev"]
    + [f"band_{m}" for m in RANGE_METRICS] + ["band_worst"]
)

# Device profiles: which metrics a device reports. Used to train with realistic missingness and to
# score the model per profile. "full" keeps whatever was recorded.
PROFILES: dict[str, list[str]] = {
    "full": [],
    "no_sinr_cqi": ["sinr", "cqi"],
    "level_only": ["quality", "sinr", "rssi", "cqi"],
    "rssi_only": ["level", "quality", "sinr", "cqi"],
}
PROFILE_REQUIRES = {"level_only": "level", "rssi_only": "rssi"}


def apply_profile(df: pd.DataFrame, profile: str) -> pd.DataFrame:
    """Blank out the metrics a device of this profile would not report; drop rows left without their key metric."""
    out = df.copy()
    for metric in PROFILES[profile]:
        out[metric] = np.nan
    need = PROFILE_REQUIRES.get(profile)
    if need:
        out = out[out[need].notna()]
    return out


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a float DataFrame with columns FEATURES, index aligned to df."""
    n = len(df)
    feats: dict[str, np.ndarray] = {}
    fam = df["family"].to_numpy(dtype=object)
    for f in FAMILIES:
        feats[f"fam_{f}"] = (fam == f).astype(float)

    values = {m: pd.to_numeric(df[m], errors="coerce").to_numpy(dtype=float) for m in BASE_METRICS}
    for m in BASE_METRICS:
        feats[m] = values[m]
        feats[f"has_{m}"] = (~np.isnan(values[m])).astype(float)

    rolled = {f"{c}_{s}30": np.full(n, np.nan) for c, s in ROLLING}
    ts = pd.to_datetime(df["ts"]).to_numpy()
    groups = pd.Series(np.arange(n)).groupby(df["device_key"].to_numpy(), sort=False).indices
    for idx in groups.values():
        idx = idx[np.argsort(ts[idx], kind="stable")]
        index = pd.DatetimeIndex(ts[idx])
        for col, stat in ROLLING:
            window = pd.Series(values[col][idx], index=index).rolling(WINDOW, min_periods=1)
            res = window.std(ddof=0) if stat == "std" else getattr(window, stat)()
            rolled[f"{col}_{stat}30"][idx] = res.to_numpy()
    feats.update(rolled)
    feats["level_dev"] = values["level"] - rolled["level_median30"]

    # Domain knowledge as features: the documented band (0 Strong / 1 Weak / 2 Dead) of each reported metric.
    worst = np.full(n, np.nan)
    for m in RANGE_METRICS:
        band = np.full(n, np.nan)
        for f, bands in RANGES.items():
            if m not in bands:
                continue
            weak_below, dead_below = bands[m]
            mask = (fam == f) & ~np.isnan(values[m])
            v = values[m][mask]
            cls = np.where(v >= weak_below, 0.0, 1.0)
            if dead_below is not None:
                cls = np.where(v < dead_below, 2.0, cls)
            band[mask] = cls
        feats[f"band_{m}"] = band
        worst = np.fmax(worst, band)
    feats["band_worst"] = worst
    return pd.DataFrame(feats, index=df.index)[FEATURES]
