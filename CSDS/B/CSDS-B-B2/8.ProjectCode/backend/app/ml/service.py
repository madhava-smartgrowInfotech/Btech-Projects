"""Model service: loads the trained models once and classifies readings for the API.

Three kinds of readings, three methods (each verdict records which one was used):
    radio   readings with RSRP/RSRQ/SINR/RSSI (datasets, cellular modems): trained zone classifier
    probe   phone-browser readings (connectivity, latency, speed): measured service-quality bands,
            plus the speed-based radio-condition estimate as supporting evidence
    wifi    ESP32 Wi-Fi/BLE link readings: documented Wi-Fi ranges
If a model file is missing the documented ranges are used and the verdict says so.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .features import build_features
from .service_quality import DEFAULT_WEAK_DL_MBPS, DEFAULT_WEAK_RTT_MS, SPEED_FEATURES, classify_probe, speed_features
from .signal_ranges import CLASSES, DEAD, classify_by_ranges, classify_wifi, family_of

log = logging.getLogger("signalscout.models")


@dataclass
class Verdict:
    label: str | None                    # Strong / Weak / Dead, or None when nothing can be judged
    confidence: float | None
    method: str                          # model / service-bands / wifi-ranges / ranges / no-service
    reasons: list[str] = field(default_factory=list)
    model_version: str | None = None
    radio_estimate: str | None = None
    radio_estimate_conf: float | None = None


class ModelService:
    def __init__(self, models_dir: Path):
        self.models_dir = Path(models_dir)
        self.zone = self._load("zone_classifier")
        self.radio_estimate = self._load("radio_estimate")
        self.gp = self._load("gp_signal")

    def _load(self, name: str) -> dict | None:
        path = self.models_dir / f"{name}.joblib"
        if not path.exists():
            log.warning("model not found - using documented ranges instead", extra={"fields": {"model": name}})
            return None
        try:
            bundle = joblib.load(path)
        except Exception:
            log.exception("model could not be loaded", extra={"fields": {"model": name}})
            return None
        meta = self.models_dir / f"{name}.json"
        bundle["summary"] = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
        log.info("model loaded", extra={"fields": {"model": name, "version": bundle.get("version")}})
        return bundle

    # ------------------------------------------------------------ info
    def status(self) -> dict:
        def info(b: dict | None) -> dict:
            return {"loaded": b is not None, "version": b.get("version") if b else None, "name": b.get("name") if b else None}
        return {"zone_classifier": info(self.zone), "radio_estimate": info(self.radio_estimate), "gp_signal": info(self.gp)}

    # ------------------------------------------------------------ radio readings
    def classify_radio(self, frame: pd.DataFrame, target: np.ndarray | None = None) -> list[Verdict]:
        """frame: device_key, ts, network_type, rsrp (or level), rsrq, sinr, rssi, cqi, in_service.
        Rows outside `target` are only history for the 30-second rolling features."""
        df = frame.copy()
        df["family"] = [family_of(t) or ("lte_nr" if pd.notna(r) else None) for t, r in zip(df.get("network_type"), df.get("rsrp"))]
        df["level"] = df["rsrp"].where(df["family"] != "2g", df["rssi"]) if "level" not in df else df["level"]
        df["quality"] = df.get("rsrq")
        for col in ("sinr", "rssi", "cqi"):
            if col not in df:
                df[col] = np.nan
        target = np.ones(len(df), bool) if target is None else np.asarray(target, bool)
        in_service = df.get("in_service", pd.Series(True, index=df.index)).fillna(True).astype(bool).to_numpy()
        has_metric = df[["level", "quality", "sinr", "rssi", "cqi"]].notna().any(axis=1).to_numpy()
        has_family = df["family"].notna().to_numpy()

        proba = None
        usable = target & in_service & has_metric & has_family
        if self.zone is not None and usable.any():
            feats = build_features(df.assign(family=df["family"].fillna("lte_nr")))
            proba = np.full((len(df), 3), np.nan)
            proba[usable] = self.zone["model"].predict_proba(feats.to_numpy()[usable])

        out: list[Verdict] = []
        for i in np.flatnonzero(target):
            row = df.iloc[i]
            if not in_service[i]:
                out.append(Verdict("Dead", 1.0, "no-service", ["No mobile service at this point"]))
                continue
            ranges = classify_by_ranges(row["family"], _num(row["level"]), _num(row["quality"]), _num(row["sinr"]))
            if proba is not None and usable[i]:
                k = int(np.argmax(proba[i]))
                reasons = list(ranges.reasons)
                if ranges.label is not None and ranges.label != k:
                    reasons.append(f"The model expects {CLASSES[k]} conditions from the metrics this device reports")
                out.append(Verdict(CLASSES[k], round(float(proba[i][k]), 3), "model", reasons, self.zone.get("version")))
            elif ranges.label is not None:
                out.append(Verdict(CLASSES[ranges.label], None, "ranges", ranges.reasons))
            else:
                out.append(Verdict(None, None, "unclassified", ["Not enough signal metrics to judge this reading"]))
        return out

    # ------------------------------------------------------------ phone-probe readings
    def classify_probes(self, frame: pd.DataFrame, target: np.ndarray | None = None,
                        weak_rtt_ms: float = DEFAULT_WEAK_RTT_MS, weak_dl_mbps: float = DEFAULT_WEAK_DL_MBPS) -> list[Verdict]:
        """frame: device_key, ts, connected, probes_sent, probes_ok, latency_ms, dl_mbps, ul_mbps (history rows allowed)."""
        df = frame.reset_index(drop=True)
        target = np.ones(len(df), bool) if target is None else np.asarray(target, bool)

        est_proba = None
        tests = df[df["dl_mbps"].notna()] if "dl_mbps" in df else df.iloc[0:0]
        if self.radio_estimate is not None and len(tests):
            feats = speed_features(tests.assign(ul_mbps=tests.get("ul_mbps")))
            est = self.radio_estimate["model"].predict_proba(feats[SPEED_FEATURES].to_numpy())
            est_proba = pd.DataFrame(est, index=tests.index)

        out: list[Verdict] = []
        for i in np.flatnonzero(target):
            row = df.iloc[i]
            q = classify_probe(bool(row.get("connected", True)), _int(row.get("probes_sent")), _int(row.get("probes_ok")),
                               _num(row.get("latency_ms")), _num(row.get("dl_mbps")), weak_rtt_ms, weak_dl_mbps)
            v = Verdict(CLASSES[q.label], q.confidence, "service-bands", q.reasons)
            if est_proba is not None and i in est_proba.index and q.label != DEAD:
                p = est_proba.loc[i].to_numpy()
                k = int(np.argmax(p))
                v.radio_estimate, v.radio_estimate_conf = CLASSES[k], round(float(p[k]), 3)
                v.model_version = self.radio_estimate.get("version")
            out.append(v)
        return out

    # ------------------------------------------------------------ ESP32 Wi-Fi/BLE readings
    @staticmethod
    def classify_wifi(rssi: float | None, latency_ms: float | None, packet_loss: float | None, connected: bool = True) -> Verdict:
        r = classify_wifi(rssi, latency_ms, packet_loss, connected)
        return Verdict(CLASSES[r.label] if r.label is not None else None, None, "wifi-ranges", r.reasons)


def _num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(f) else f


def _int(v) -> int:
    f = _num(v)
    return int(f) if f is not None else 0
