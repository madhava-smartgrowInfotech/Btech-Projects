"""Gather nearby readings and run the Gaussian Process for better-signal suggestions and predicted coverage."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ml.registry import get_models
from ..ml.suggest import MIN_CELLS, Suggestion, predicted_surface, suggest
from ..models import Reading

FLOOR_MBPS = 0.05          # a probe reading with no connection enters the speed surface at this floor


@dataclass
class Points:
    target: str             # rsrp / log_dl
    operator: str | None
    lat: np.ndarray
    lon: np.ndarray
    value: np.ndarray


def _bbox(lat: float, lon: float, radius_m: float) -> tuple[float, float, float, float]:
    dlat = radius_m / 111_320
    dlon = radius_m / (111_320 * max(math.cos(math.radians(lat)), 0.01))
    return lat - dlat, lat + dlat, lon - dlon, lon + dlon


def nearby_operator(db: Session, lat: float, lon: float, radius_m: float = 1600) -> str | None:
    a, b, c, d = _bbox(lat, lon, radius_m)
    row = db.execute(select(Reading.operator, func.count()).where(Reading.lat.between(a, b), Reading.lon.between(c, d),
                                                                  Reading.link != "wifi", Reading.zone_label.is_not(None))
                     .group_by(Reading.operator).order_by(func.count().desc()).limit(1)).first()
    return row[0] if row else None


def gather(db: Session, lat: float, lon: float, operator: str | None, radius_m: float = 1600) -> Points | None:
    operator = operator or nearby_operator(db, lat, lon, radius_m)
    if not operator:
        return None
    a, b, c, d = _bbox(lat, lon, radius_m)
    rows = db.execute(select(Reading.lat, Reading.lon, Reading.rsrp, Reading.dl_mbps, Reading.connected, Reading.source)
                      .where(Reading.lat.between(a, b), Reading.lon.between(c, d), Reading.operator == operator,
                             Reading.link != "wifi", Reading.zone_label.is_not(None))
                      .order_by(Reading.ts.desc()).limit(20000)).all()
    probe = [(r.lat, r.lon, math.log10(max(r.dl_mbps, FLOOR_MBPS)) if r.dl_mbps is not None else math.log10(FLOOR_MBPS))
             for r in rows if r.source == "phone" and (r.dl_mbps is not None or not r.connected)]
    radio = [(r.lat, r.lon, r.rsrp) for r in rows if r.rsrp is not None]
    # Prefer what phones measured (speed) when there is enough of it; otherwise the radio level.
    if len(probe) >= MIN_CELLS and len(probe) >= 0.2 * len(radio):
        pts, target = probe, "log_dl"
    elif radio:
        pts, target = radio, "rsrp"
    elif probe:
        pts, target = probe, "log_dl"
    else:
        return None
    arr = np.asarray(pts, float)
    return Points(target, operator, arr[:, 0], arr[:, 1], arr[:, 2])


def suggest_for(db: Session, lat: float, lon: float, operator: str | None) -> dict:
    gp = get_models().gp
    if gp is None:
        return {"found": False, "status": "unavailable", "message": "The better-signal model is not trained yet (python ml/train_all.py)."}
    pts = gather(db, lat, lon, operator)
    if pts is None:
        return Suggestion(False, "not_enough_data", "No readings near you yet. Collect a few while walking and try again.",
                          "log_dl", "gaussian-process").to_dict() | {"operator": operator}
    s = suggest(gp, pts.target, lat, lon, pts.lat, pts.lon, pts.value, operator=pts.operator)
    out = s.to_dict() | {"operator": pts.operator, "model_version": gp.get("version")}
    if s.target == "log_dl":
        for k in ("predicted", "here_predicted"):
            if out.get(k) is not None:
                out[k + "_mbps"] = round(10 ** out[k], 2)
    return out


def surface_for(db: Session, lat: float, lon: float, operator: str | None, radius_m: float = 1200, step_m: float = 40) -> dict:
    gp = get_models().gp
    pts = gather(db, lat, lon, operator, radius_m + 400) if gp else None
    if not gp or pts is None:
        return {"cells": [], "target": None, "operator": operator}
    cells = predicted_surface(gp, pts.target, lat, lon, pts.lat, pts.lon, pts.value, operator=pts.operator, radius_m=radius_m, step_m=step_m)
    threshold = gp["targets"][pts.target]["strong_threshold"]
    return {"cells": cells, "target": pts.target, "operator": pts.operator, "strong_threshold": threshold, "step_m": step_m,
            "unit": "dBm" if pts.target == "rsrp" else "log10 Mbps"}


def strong_spot_pack(db: Session, lat: float, lon: float, operator: str | None, radius_m: float = 2500) -> dict:
    """Predicted strong spots around a point - downloaded by the phone for offline use."""
    surf = surface_for(db, lat, lon, operator, radius_m=radius_m, step_m=60)
    spots = [{"lat": c["lat"], "lon": c["lon"], "value": c["value"], "p_strong": c["p_strong"], "target": surf["target"]}
             for c in surf["cells"] if c["p_strong"] >= 0.8]
    return {"center": [lat, lon], "operator": surf["operator"], "target": surf["target"], "spots": spots[:1500]}
