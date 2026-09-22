"""Model performance: training metrics and plots from experiments/, and live validation on field readings."""
from __future__ import annotations

import json
import math
import re
from collections import Counter

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db
from ..core.security import get_current_user
from ..ml.gp import GPParams, aggregate, fit_predict, project
from ..ml.registry import get_models
from ..ml.signal_ranges import CLASSES, classify_by_ranges, family_of
from ..models import Reading, User

router = APIRouter(prefix="/api/ml", tags=["models"])
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _load(name: str) -> tuple[dict, dict]:
    summary_path = settings.models_dir / f"{name}.json"
    if not summary_path.exists():
        return {}, {}
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    metrics_path = settings.root / summary.get("experiment", "") / "metrics.json"
    return summary, (json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {})


def _plots(run: str) -> list[str]:
    folder = settings.experiments_dir / run
    return sorted(p.name for p in folder.glob("*.png")) if folder.exists() else []


@router.get("/models", summary="Every trained model with its evaluation (from experiments/)")
def models(user: User = Depends(get_current_user)) -> dict:
    out = {}
    zs, zm = _load("zone_classifier")
    if zm:
        out["zone_classifier"] = {
            "title": "Zone classifier", "summary": zs, "run": zm["run"], "created_at": zm["created_at"], "chosen": zm["chosen"],
            "chosen_by": zm.get("chosen_by"), "task": zm["task"], "dataset": {k: zm["dataset"][k] for k in ("name", "date_range", "split_method", "splits")},
            "labels": zm["labels"], "profiles": list(zm["profiles"]), "cross_validation": zm["cross_validation"], "test": zm["test"],
            "test_overall": zm["test_overall_chosen"], "calibration": {k: zm["calibration"][k] for k in ("ece_before", "ece_after")},
            "temperature": zm["temperature"], "feature_importance": zm["feature_importance"][:10],
            "consistency_check": {k: zm["consistency_check_patna"][k] for k in ("accuracy", "macro_f1", "note", "by_network_type")},
            "timings_s": zm["timings_s"], "plots": _plots(zm["run"]),
        }
    rs, rm = _load("radio_estimate")
    if rm:
        out["radio_estimate"] = {
            "title": "Radio-condition estimate (phone speed tests)", "summary": rs, "run": rm["run"], "created_at": rm["created_at"], "task": rm["task"],
            "dataset": {k: rm["dataset"][k] for k in ("name", "split_method", "splits", "speed_test_simulation")},
            "test_per_speed_test": {k: rm["test_per_speed_test"][k] for k in ("accuracy", "macro_f1", "per_class", "confusion")},
            "test_per_zone": rm["test_per_zone"], "baselines": {k: {"accuracy": v["accuracy"], "macro_f1": v["macro_f1"]} for k, v in rm["baselines"].items()},
            "calibration": {"ece": rm["calibration"]["ece"]}, "interpretation": rm["interpretation"], "plots": _plots(rm["run"]),
        }
    gs, gm = _load("gp_signal")
    if gm:
        out["gp_signal"] = {
            "title": "Better-signal predictor (Gaussian Process)", "summary": gs, "run": gm["run"], "created_at": gm["created_at"], "task": gm["task"],
            "kernel": gm["kernel"], "dataset": gm["dataset"],
            "targets": {t: {"label": r["spec"]["label"], "unit": r["spec"]["unit"], "params": r["params"], "block_cv": r["block_cv_summary"],
                            "coverage": r["gp_interval_coverage"], "random_holdout_rmse": r["random_holdout_gp_rmse"], "areas": len(r["areas"])}
                        for t, r in gm["targets"].items()},
            "plots": _plots(gm["run"]),
        }
    return {"models": out, "loaded": get_models().status()}


@router.get("/models/{run}/artifacts/{filename}", summary="A plot or file from a training run")
def artifact(run: str, filename: str, user: User = Depends(get_current_user)) -> FileResponse:
    if not SAFE.match(run) or not SAFE.match(filename) or not filename.endswith((".png", ".json", ".log")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid artifact")
    path = settings.experiments_dir / run / filename
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/field-validation", summary="How the models behave on readings collected with this installation")
def field_validation(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    out: dict = {}
    # 1. Radio readings from field devices (not the replayed sample): model vs documented ranges on the metrics present.
    radio = db.execute(select(Reading.network_type, Reading.rsrp, Reading.rsrq, Reading.sinr, Reading.zone_label, Reading.zone_confidence)
                       .where(Reading.source.in_(("phone", "esp32", "simulator")), Reading.rsrp.is_not(None), Reading.label_method == "model")).all()
    if radio:
        agree = 0
        for r in radio:
            v = classify_by_ranges(family_of(r.network_type) or "lte_nr", r.rsrp, r.rsrq, r.sinr)
            agree += int(v.label is not None and CLASSES[v.label] == r.zone_label)
        out["radio"] = {"readings": len(radio), "agreement_with_ranges": round(agree / len(radio), 3),
                        "mean_confidence": round(float(np.mean([r.zone_confidence or 0 for r in radio])), 3)}
    else:
        out["radio"] = {"readings": 0, "note": "No field readings with radio metrics yet (phone-browser probes measure service quality, not radio)."}

    # 2. Phone probe: measured class vs the speed-based radio estimate (agreement, not accuracy - different targets).
    probe = db.execute(select(Reading.zone_label, Reading.radio_estimate).where(Reading.source == "phone", Reading.radio_estimate.is_not(None),
                                                                                 Reading.link != "wifi")).all()
    counts = Counter(zip((p.zone_label for p in probe), (p.radio_estimate for p in probe)))
    total_probe = db.query(func.count(Reading.id)).filter(Reading.source == "phone", Reading.link != "wifi").scalar() or 0
    out["probe"] = {"readings": total_probe, "with_speed_test": len(probe),
                    "agreement": round(sum(v for (a, b), v in counts.items() if a == b) / len(probe), 3) if probe else None,
                    "matrix": [[counts.get((a, b), 0) for b in CLASSES] for a in CLASSES],
                    "measured_classes": dict(Counter(r[0] for r in db.execute(select(Reading.zone_label).where(Reading.source == "phone", Reading.link != "wifi")).all()))}

    # 3. Gaussian Process on this installation's own phone speed tests: hold out 20% of measured cells, predict them.
    gp = get_models().gp
    rows = db.execute(select(Reading.lat, Reading.lon, Reading.dl_mbps, Reading.operator).where(Reading.source == "phone", Reading.dl_mbps.is_not(None),
                                                                                               Reading.link != "wifi")).all()
    need = 30
    if gp and rows:
        op = Counter(r.operator for r in rows).most_common(1)[0][0]
        pts = [(r.lat, r.lon, math.log10(max(r.dl_mbps, 0.05))) for r in rows if r.operator == op]
        cells = aggregate([p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts], 10.0)
        if len(cells) >= need:
            rng = np.random.default_rng(7)
            idx = rng.permutation(len(cells))
            k = max(5, len(cells) // 5)
            test, train = idx[:k], idx[k:]
            xy = project(cells.lat, cells.lon, float(cells.lat.mean()), float(cells.lon.mean()))
            y = cells.value.to_numpy()
            t = gp["targets"]["log_dl"]
            params = GPParams.from_dict(t.get("params_by_operator", {}).get(op) or t["params"])
            mu, _ = fit_predict(xy[train], y[train], xy[test], params, latent=False)
            rmse = float(np.sqrt(np.mean((mu - y[test]) ** 2)))
            base = float(np.sqrt(np.mean((y[train].mean() - y[test]) ** 2)))
            out["gp"] = {"operator": op, "cells": len(cells), "held_out": int(k), "rmse_log10_mbps": round(rmse, 3), "mean_baseline_rmse": round(base, 3),
                         "improvement": round(1 - rmse / base, 3) if base else None}
        else:
            out["gp"] = {"cells": len(cells), "needed": need, "note": f"Collect speed tests in at least {need} different 10 m cells to validate the predictor on your own data."}
    else:
        out["gp"] = {"cells": 0, "needed": need, "note": "No phone speed tests yet."}
    return out
