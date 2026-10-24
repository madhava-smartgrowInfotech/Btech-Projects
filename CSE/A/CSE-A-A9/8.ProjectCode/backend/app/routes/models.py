"""F7 - model comparison, scalability and the in-app retraining run that learns from moderator decisions."""
from __future__ import annotations

import threading
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, require_moderator
from ..db import Review, SessionLocal, TrainingRun, User, get_db, utcnow
from ..services.store import C, D, get_store, reload_store

router = APIRouter(prefix="/api/models")

_job = {"state": "idle", "progress": 0.0, "message": "", "run_id": None}
_job_lock = threading.Lock()


def _models_payload(metrics: dict) -> list[dict]:
    base_f1 = metrics["models"][C.BASELINE]["f1"]["mean"]
    out = []
    for name in C.ALL_MODELS:
        m = metrics["models"][name]
        out.append({**{k: m[k] for k in ("label", "uses_graph", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc",
                                         "train_seconds", "threshold", "confusion", "roc", "is_best", "per_seed")},
                    "name": name, "f1_lift": m["f1"]["mean"] - base_f1})
    return out


@router.get("")
def models(_: User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_store()
    if not s.metrics:
        raise HTTPException(404, "No evaluation file found. Run `python -m ml.train` first.")
    runs = list(db.scalars(select(TrainingRun).order_by(TrainingRun.started_at.desc()).limit(10)))
    return {
        "best": s.best, "meta": s.meta, "models": _models_payload(s.metrics), "cluster_recovery": s.metrics["cluster_recovery"],
        "split": s.metrics["meta"]["splits"],
        "latest_retrain": {"models": _models_payload(s.metrics_retrain), "meta": s.metrics_retrain["meta"]} if s.metrics_retrain else None,
        "runs": [_run_out(r) for r in runs], "retrain": dict(_job),
    }


@router.get("/scalability")
def scalability(_: User = Depends(current_user)):
    s = get_store()
    if not s.scalability:
        raise HTTPException(404, "No scalability sweep found. Run `python -m ml.eval` first.")
    return {**s.scalability, "labels": C.MODEL_LABELS}


def _run_out(r: TrainingRun) -> dict:
    return {"id": r.id, "started_at": r.started_at.isoformat(), "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "status": r.status, "feedback_labels": r.feedback_labels, "best": r.best, "f1_before": r.f1_before,
            "f1_after": r.f1_after, "message": r.message}


@router.get("/retrain/status")
def retrain_status(_: User = Depends(current_user)):
    return dict(_job)


def _feedback(db: Session) -> tuple[dict[int, int], list[int]]:
    reviews = list(db.scalars(select(Review).order_by(Review.created_at)))
    fb: dict[int, int] = {}
    for r in reviews:
        for m in r.members or []:
            fb[int(m)] = 1 if r.decision == "confirm" else 0
    return fb, [r.id for r in reviews]


def _current_f1(s) -> dict:
    src = s.metrics_retrain if s.meta["kind"] != "full" and s.metrics_retrain else s.metrics
    return {n: (src["models"][n]["per_seed"][0]["f1"] if src is s.metrics else src["models"][n]["f1"]["mean"]) for n in C.ALL_MODELS}


def _run_job(run_id: int, fb: dict[int, int], review_ids: list[int]) -> None:
    from ml import train  # imported late: pulls in torch

    def progress(f, msg):
        _job.update(progress=round(f, 3), message=msg)

    try:
        g = D.load()
        res = train.fit_all(g, [0], fb, progress)
        out = train.write_artifacts(g, res, "retrain")
        reload_store()
        with SessionLocal() as db:
            run = db.get(TrainingRun, run_id)
            run.status, run.finished_at = "done", utcnow()
            run.best = res["best"]
            run.f1_after = {n: out["models"][n]["f1"]["mean"] for n in C.ALL_MODELS}
            run.message = f"{res['feedback_labels_used']} moderator labels used in training."
            for rv in db.scalars(select(Review).where(Review.id.in_(review_ids))):
                if rv.used_in_run is None:
                    rv.used_in_run = run_id
            db.commit()
        _job.update(state="done", progress=1.0, message="Retraining finished - scores and clusters are updated.")
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI
        traceback.print_exc()
        with SessionLocal() as db:
            run = db.get(TrainingRun, run_id)
            run.status, run.finished_at, run.message = "error", utcnow(), str(exc)[:400]
            db.commit()
        _job.update(state="error", message=f"Retraining failed: {exc}")


@router.post("/retrain", status_code=202)
def retrain(user: User = Depends(require_moderator), db: Session = Depends(get_db)):
    fb, review_ids = _feedback(db)
    if not fb:
        raise HTTPException(409, "There are no moderator decisions yet. Confirm or dismiss a few flagged accounts first.")
    with _job_lock:
        if _job["state"] == "running":
            raise HTTPException(409, "A retraining run is already in progress.")
        s = get_store()
        run = TrainingRun(feedback_labels=len(fb), f1_before=_current_f1(s), user_id=user.id)
        db.add(run)
        db.commit()
        _job.update(state="running", progress=0.0, message="Starting...", run_id=run.id)
    threading.Thread(target=_run_job, args=(run.id, fb, review_ids), daemon=True).start()
    return {"run_id": run.id, "feedback_labels": len(fb)}
