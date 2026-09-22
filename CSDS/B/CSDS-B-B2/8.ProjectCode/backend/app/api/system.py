from __future__ import annotations

import json
import socket

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..core.config import APP_NAME, APP_VERSION, settings
from ..core.db import get_db, utcnow
from ..core.security import get_current_user
from ..ml.registry import get_models
from ..models import Complaint, Reading, User, ZoneState
from ..schemas.common import _iso_utc

router = APIRouter(prefix="/api", tags=["system"])

MODEL_FILES = ("zone_classifier", "radio_estimate", "gp_signal")


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception as exc:  # reported, not raised: health must always answer
        database = f"error: {exc.__class__.__name__}"
    status = get_models().status()
    return {
        "status": "ok" if database == "ok" else "degraded",
        "app": APP_NAME, "version": APP_VERSION, "time": _iso_utc(utcnow()), "database": database,
        "models": {name: status[name]["loaded"] for name in MODEL_FILES},
        "model_versions": {name: status[name]["version"] for name in MODEL_FILES},
    }


def _model_summary(name: str) -> dict:
    path = settings.models_dir / f"{name}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


@router.get("/public/stats", summary="Headline numbers for the landing page (aggregates only, no sign-in)")
def public_stats(db: Session = Depends(get_db)) -> dict:
    zc, gp = _model_summary("zone_classifier"), _model_summary("gp_signal")
    rmse = (gp.get("targets", {}).get("rsrp") or {}).get("block_cv_rmse") or {}
    gp_gain = 1 - rmse["Gaussian Process"] / rmse["Inverse distance"] if rmse.get("Gaussian Process") and rmse.get("Inverse distance") else None
    return {
        "readings": db.query(func.count(Reading.id)).filter(Reading.zone_label.is_not(None)).scalar() or 0,
        "zones": db.query(func.count()).select_from(ZoneState).scalar() or 0,
        "complaints_registered": db.query(func.count(Complaint.id)).filter(Complaint.registered_at.is_not(None)).scalar() or 0,
        "classifier_accuracy": round((zc.get("test_overall") or {}).get("accuracy", 0), 3) or None,
        "classifier_model": zc.get("model"),
        "predictor_gain_vs_idw": round(gp_gain, 3) if gp_gain is not None else None,
    }


def lan_addresses() -> list[str]:
    """The address of the network interface that carries normal traffic (skips virtual adapters)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))   # no packet is sent; this only selects the outgoing interface
            return [s.getsockname()[0]]
    except OSError:
        pass
    try:
        ips = {str(info[4][0]) for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)}
        return sorted(ip for ip in ips if not ip.startswith(("127.", "169.254.")))
    except OSError:
        return []


def tunnel_info() -> dict | None:
    path = settings.runtime_dir / "tunnel.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@router.get("/system/connect")
def connect_info(_: User = Depends(get_current_user)) -> dict:
    """Where phones and nodes can reach this installation (the phone probe needs the HTTPS link)."""
    tunnel = tunnel_info()
    tunnel_url = tunnel.get("url") if tunnel else None
    ips = lan_addresses()
    return {
        "tunnel_url": tunnel_url,
        "tunnel_started_at": tunnel.get("started_at") if tunnel else None,
        "probe_url": f"{tunnel_url}/probe" if tunnel_url else None,
        "tunnel_enabled": settings.tunnel_enabled,
        "lan_api_urls": [f"http://{ip}:{settings.backend_port}" for ip in ips],
        "lan_dashboard_urls": [f"http://{ip}:{settings.frontend_port}" for ip in ips],
        "backend_port": settings.backend_port,
        "frontend_port": settings.frontend_port,
    }
