"""Additive, read-only endpoints for the React frontend (plus the demo sign-in).

Nothing here changes an existing route: the Jinja pages and the original JSON
endpoints in app/main.py keep their contracts.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time

import numpy as np
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import APP_NAME, BASE_DIR, DEFAULT_K, MAX_DESC_LEN, RETRIEVAL_KS
from app.services.store import ensure_artifacts

log = logging.getLogger(APP_NAME)
router = APIRouter()

STATES = ["CA", "NY", "MA", "TX", "WA", "IL", "CO", "FL", "PA", "OR", "Other"]
INDUSTRIES = ["Software", "E-Commerce", "FinTech", "HealthTech", "EdTech",
              "CleanTech", "Media", "Mobile", "AI", "Biotech", "Other"]

# (min, max, step, default) for every numeric field of POST /predict
NUMERIC_FIELDS = {
    "funding_total_usd": (0, 1e10, 1000, 1000000),
    "funding_rounds": (0, 20, 1, 2),
    "relationships": (0, 200, 1, 4),
    "milestones": (0, 50, 1, 2),
    "avg_participants": (0, 50, 0.5, 3.0),
    "age_first_funding_year": (0, 30, 0.1, 1.5),
    "age_last_funding_year": (0, 30, 0.1, 2.5),
    "age_first_milestone_year": (0, 30, 0.1, 1.0),
    "age_last_milestone_year": (0, 30, 0.1, 2.0),
}


def _env(name: str, default: str) -> str:
    """Environment first, then the project-root .env file (no extra dependency)."""
    if os.environ.get(name):
        return os.environ[name]
    try:
        for line in (BASE_DIR / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return default


def _creds() -> tuple[str, str, str]:
    return (_env("DEMO_EMAIL", "demo@venturepulse.com").lower(),
            _env("DEMO_PASSWORD", "Demo@1234"),
            _env("DEMO_SECRET", "venturepulse-demo-secret"))


def _sign(email: str, exp: int, secret: str) -> str:
    return hmac.new(secret.encode(), f"{email}:{exp}".encode(), hashlib.sha256).hexdigest()


def make_token(email: str, ttl: int = 12 * 3600) -> str:
    exp = int(time.time()) + ttl
    sig = _sign(email, exp, _creds()[2])
    return base64.urlsafe_b64encode(f"{email}|{exp}|{sig}".encode()).decode()


def read_token(token: str | None) -> str | None:
    try:
        email, exp, sig = base64.urlsafe_b64decode((token or "").encode()).decode().split("|")
        if int(exp) < time.time():
            return None
        if hmac.compare_digest(sig, _sign(email, int(exp), _creds()[2])) and email == _creds()[0]:
            return email
    except Exception:
        pass
    return None


class LoginPayload(BaseModel):
    email: str
    password: str


@router.post("/api/auth/login")
def login(p: LoginPayload):
    email, password, _ = _creds()
    ok = hmac.compare_digest(p.email.strip().lower(), email) & hmac.compare_digest(p.password, password)
    if not ok:
        return JSONResponse({"detail": "Incorrect email or password."}, status_code=401)
    return {"token": make_token(email), "user": {"name": "Demo Analyst", "email": email}}


@router.get("/api/auth/me")
def me(authorization: str | None = Header(default=None)):
    email = read_token((authorization or "").removeprefix("Bearer ").strip())
    if not email:
        return JSONResponse({"detail": "Session expired. Sign in again."}, status_code=401)
    return {"name": "Demo Analyst", "email": email}


@router.get("/api/config")
def config():
    try:
        st = ensure_artifacts()
        meta = st["metadata"]
        return {
            "app": APP_NAME,
            "states": STATES,
            "industries": INDUSTRIES,
            "ks": RETRIEVAL_KS,
            "default_k": DEFAULT_K,
            "max_description": MAX_DESC_LEN,
            "fields": {k: {"min": a, "max": b, "step": s, "default": d} for k, (a, b, s, d) in NUMERIC_FIELDS.items()},
            "best_model": meta["best_model"],
            "n_train": meta["n_train"],
            "class_counts": meta["class_counts"],
            "alpha": meta["alpha"],
            "embedding_dim": meta["embedding_dim"],
            "embedding_backend": meta.get("embedding_backend"),
            "dataset": meta.get("dataset_meta", {}),
            "demo_email": _creds()[0],
        }
    except Exception as e:
        log.exception("config failed")
        return JSONResponse({"detail": str(e)}, status_code=500)


@router.get("/api/feature-importance")
def feature_importance(top: int = 15):
    """Same numbers the matplotlib feature_importance.png is drawn from."""
    try:
        st = ensure_artifacts()
        meta, model = st["metadata"], st["model"]
        names = meta["feature_names_structured"]
        sdim = meta["structured_dim"]
        signed = None
        if hasattr(model, "feature_importances_"):
            raw = np.asarray(model.feature_importances_, dtype=float)[:sdim]
            kind = "importance"
        elif hasattr(model, "coef_"):
            signed = np.asarray(model.coef_, dtype=float).ravel()[:sdim]
            raw = np.abs(signed)
            kind = "abs_coefficient"
        else:
            return {"model": meta["best_model"], "kind": "none", "features": []}
        order = np.argsort(-raw)[: max(1, min(top, len(raw)))]
        feats = [{"feature": names[i], "value": round(float(raw[i]), 5),
                  **({"coefficient": round(float(signed[i]), 5)} if signed is not None else {})}
                 for i in order]
        return {"model": meta["best_model"], "kind": kind, "features": feats}
    except Exception as e:
        log.exception("feature importance failed")
        return JSONResponse({"detail": str(e)}, status_code=500)
