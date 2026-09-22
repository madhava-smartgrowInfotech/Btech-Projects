"""Clean the public datasets into data/processed/ with one consistent schema.

    python ml/prepare_data.py

Outputs
    data/processed/lte_speed_clean.csv.gz          Cork drive-test traces (radio + throughput), labelled
    data/processed/cellular_analysis_clean.csv.gz  Patna measurements (signal level only), labelled
    data/processed/prep_report.json                row counts for every cleaning step and label shares
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from _common import PROCESSED, RAW, write_json
from app.ml.signal_ranges import CLASSES, VALID, family_of, label_arrays

MODE_ALIAS = {"HSPA+": "HSPA+", "HSUPA": "HSUPA", "HSDPA": "HSDPA", "UMTS": "UMTS", "EDGE": "EDGE", "GPRS": "GPRS", "LTE": "LTE"}


def clip_valid(values: pd.Series, family: pd.Series, metric: str) -> pd.Series:
    """Values outside the 3GPP reporting range for their family become NaN (e.g. the -200 dBm sentinel)."""
    out = pd.to_numeric(values, errors="coerce").astype(float)
    for fam, ranges in VALID.items():
        lo, hi = ranges[metric]
        mask = (family == fam) & ((out < lo) | (out > hi))
        out[mask] = np.nan
    return out


def prepare_lte(report: dict) -> pd.DataFrame:
    frames = []
    for path in sorted((RAW / "lte_speed").glob("*/*.csv")):
        df = pd.read_csv(path, na_values=["-", ""])
        df["device_key"] = f"{path.parent.name}/{path.stem}"
        df["mobility"] = path.parent.name
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    steps = {"raw_rows": len(df), "trace_files": df.device_key.nunique()}

    df["ts"] = pd.to_datetime(df["Timestamp"], format="%Y.%m.%d_%H.%M.%S", errors="coerce")
    df = df[df.ts.notna() & df.Latitude.between(-90, 90) & df.Longitude.between(-180, 180) & (df.Latitude != 0)]
    steps["after_valid_time_and_position"] = len(df)

    df = df[df.Operatorname.astype(str).isin(["A", "B"])].copy()
    steps["after_keep_operators_A_B"] = len(df)
    df["operator"] = "Operator " + df.Operatorname.astype(str)

    df["network_mode"] = df.NetworkMode.astype(str).map(MODE_ALIAS)
    df["family"] = df.network_mode.map(family_of)
    df = df[df.family.notna()].copy()

    fam = df["family"]
    df["level"] = clip_valid(df.RSRP, fam, "level")          # RSRP (LTE) / RSCP (3G) / RSSI (2G)
    df["quality"] = clip_valid(df.RSRQ, fam, "quality")      # RSRQ (LTE) / Ec/No (3G)
    df["sinr"] = clip_valid(df.SNR.where(fam == "lte_nr"), fam, "sinr")   # SNR/CQI are placeholders outside LTE
    df["cqi"] = clip_valid(df.CQI.where(fam == "lte_nr"), fam, "cqi")
    df["rssi"] = clip_valid(df.RSSI.where(fam == "lte_nr"), fam, "rssi")
    df.loc[fam == "2g", "rssi"] = df.loc[fam == "2g", "level"]
    steps["level_sentinels_removed"] = int(pd.to_numeric(df.RSRP, errors="coerce").notna().sum() - df.level.notna().sum())

    df["dl_kbps"] = pd.to_numeric(df.DL_bitrate, errors="coerce")
    df["ul_kbps"] = pd.to_numeric(df.UL_bitrate, errors="coerce")
    df["state"] = df.State.astype(str)
    df["cell_id"] = pd.to_numeric(df.CellID, errors="coerce").where(lambda s: s > 0)
    df["speed_kmh"] = pd.to_numeric(df.Speed, errors="coerce")

    df["label"] = label_arrays(df.family.to_numpy(), df.level.to_numpy(), df.quality.to_numpy(), df.sinr.to_numpy())
    df = df[df.label >= 0]
    steps["after_drop_unlabellable"] = len(df)

    cols = ["device_key", "mobility", "ts", "Latitude", "Longitude", "operator", "network_mode", "family", "cell_id",
            "level", "quality", "sinr", "rssi", "cqi", "dl_kbps", "ul_kbps", "state", "speed_kmh", "label"]
    df = df[cols].rename(columns={"Latitude": "lat", "Longitude": "lon"})
    df = df.drop_duplicates()
    steps["after_drop_exact_duplicates"] = len(df)
    df = df.sort_values(["device_key", "ts"], kind="stable").reset_index(drop=True)

    report["lte_speed"] = {
        "steps": steps,
        "label_share": {CLASSES[k]: round(v, 4) for k, v in df.label.value_counts(normalize=True).sort_index().items()},
        "family_share": df.family.value_counts(normalize=True).round(4).to_dict(),
        "operators": df.operator.value_counts().to_dict(),
        "mobility_traces": df.groupby("mobility").device_key.nunique().to_dict(),
        "date_range": [str(df.ts.min()), str(df.ts.max())],
    }
    return df


def prepare_patna(report: dict) -> pd.DataFrame:
    df = pd.read_csv(RAW / "cellular_network_analysis" / "signal_metrics.csv")
    steps = {"raw_rows": len(df)}
    df["ts"] = pd.to_datetime(df.Timestamp, errors="coerce")
    df["network_type"] = df["Network Type"].astype(str)
    df["family"] = df.network_type.map(family_of)
    df = df[df.ts.notna() & df.family.notna()].copy()
    df["level"] = clip_valid(df["Signal Strength (dBm)"], df.family, "level")
    df = df[df.level.notna()].copy()
    steps["after_valid"] = len(df)
    nan = np.full(len(df), np.nan)
    df["label"] = label_arrays(df.family.to_numpy(), df.level.to_numpy(), nan, nan)
    out = pd.DataFrame({
        "ts": df.ts, "locality": df.Locality, "lat": df.Latitude, "lon": df.Longitude,
        "network_type": df.network_type, "family": df.family, "level": df.level,
        "latency_ms": df["Latency (ms)"], "throughput_mbps": df["Data Throughput (Mbps)"], "label": df.label,
    }).sort_values("ts").reset_index(drop=True)
    report["cellular_analysis"] = {
        "steps": steps,
        "label_share": {CLASSES[k]: round(v, 4) for k, v in out.label.value_counts(normalize=True).sort_index().items()},
        "network_types": out.network_type.value_counts().to_dict(),
        "localities": int(out.locality.nunique()),
        "date_range": [str(out.ts.min()), str(out.ts.max())],
        "notes": "Signal Quality (%) is 0 for every row and the BB60C/srsRAN/BladeRF columns are 0 for 3G rows, so they are not used.",
    }
    return out


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    report: dict = {}
    lte = prepare_lte(report)
    lte.to_csv(PROCESSED / "lte_speed_clean.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    patna = prepare_patna(report)
    patna.to_csv(PROCESSED / "cellular_analysis_clean.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    write_json(PROCESSED / "prep_report.json", report)
    for name, info in report.items():
        print(f"{name}: {info['steps']}  labels {info['label_share']}")


if __name__ == "__main__":
    main()
