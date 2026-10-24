"""Auth, health, graph summary and the overview dashboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, make_token, user_out, verify_password
from ..db import Review, User, get_db
from ..services.store import C, get_store

router = APIRouter(prefix="/api")


class LoginIn(BaseModel):
    email: str
    password: str


@router.get("/health")
def health():
    s = get_store()
    m = s.metrics["models"] if s.metrics else None
    return {"status": "ok", "accounts": s.n, "edges": int(len(s.g["edge_index"])), "model": C.MODEL_LABELS[s.best],
            "trained_at": s.meta["trained_at"], "flagged": int(s.accounts["flagged"].sum()),
            "botnets": sum(1 for c in s.clusters if c["kind"] == "coordinated"),
            "best_f1": m[s.best]["f1"]["mean"] if m else None, "baseline_f1": m[C.BASELINE]["f1"]["mean"] if m else None}


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "That email and password do not match. Use one of the demo logins shown on the sign-in page.")
    return {"token": make_token(user), "user": user_out(user)}


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_out(user)


@router.get("/graph/summary")
def graph_summary(_: User = Depends(current_user)):
    return get_store().graph_summary


@router.get("/overview")
def overview(_: User = Depends(current_user), db: Session = Depends(get_db)):
    from .queue import pending_counts

    s = get_store()
    acc = s.accounts
    reviews = list(db.scalars(select(Review).order_by(Review.created_at.desc())))
    dec = s.decisions_map(reviews)
    flagged = acc[acc["flagged"]]
    bins = []
    for k in range(10):
        lo, hi = k / 10, (k + 1) / 10
        m = (acc["score"] >= lo) & (acc["score"] < hi if k < 9 else acc["score"] <= hi)
        bins.append({"bin": f"{int(lo * 100)}-{int(hi * 100)}%", "count": int(m.sum()), "flagged": bool(lo >= s.thr - 1e-9)})
    top = flagged.sort_values("score", ascending=False).head(8)
    best = s.metrics["models"][s.best] if s.metrics else None
    base = s.metrics["models"][C.BASELINE] if s.metrics else None
    counts = pending_counts(s, reviews)
    coord = [c for c in s.clusters if c["kind"] == "coordinated"]
    return {
        "kpis": {
            "accounts": s.n, "ties": int(len(s.g["edge_index"])), "flagged": int(len(flagged)),
            "botnets": len(coord), "diffuse_groups": len(s.clusters) - len(coord),
            "pending_accounts": counts["accounts"], "pending_clusters": counts["clusters"],
            "decided": len(reviews), "fake_share": float(s.g["y"].mean()),
        },
        "model": {"best": s.best, "label": C.MODEL_LABELS[s.best], "threshold": s.thr,
                  "f1": best["f1"] if best else None, "precision": best["precision"] if best else None,
                  "recall": best["recall"] if best else None, "baseline_f1": base["f1"] if base else None,
                  "trained_at": s.meta["trained_at"], "kind": s.meta["kind"]},
        "score_histogram": bins,
        "top_accounts": [{**s.node_brief(int(r.id)), "status": dec.get(int(r.id), {}).get("decision", "pending")} for r in top.itertuples()],
        "top_clusters": [{k: c[k] for k in ("id", "size", "mean_score", "density", "kind", "peak_hour", "peak_hour_share")} for c in s.clusters[:5]],
        "recent_decisions": [
            {"id": r.id, "target_type": r.target_type, "target_id": r.target_id, "decision": r.decision,
             "by": r.user.name, "at": r.created_at.isoformat()} for r in reviews[:5]
        ],
        "model_f1": [{"model": n, "label": C.MODEL_LABELS[n], "f1": s.metrics["models"][n]["f1"]["mean"]} for n in C.ALL_MODELS] if s.metrics else [],
    }
