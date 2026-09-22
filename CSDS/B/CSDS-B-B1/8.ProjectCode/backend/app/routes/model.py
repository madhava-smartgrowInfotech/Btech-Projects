"""Human-in-the-loop retraining: officer decisions become labels, one click refits the models."""
import json
import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import staff
from ..db import Complaint, Feedback, ModelRun, User, get_db
from ..services import training
from ..services.predictor import get_predictor

router = APIRouter(prefix="/api/model", tags=["model"])
_retrain_lock = threading.Lock()


def officer_labels(db):
    """Latest officer value per complaint and field (accepted suggestions are confirmed labels too)."""
    rows = db.query(Feedback).order_by(Feedback.created_at).all()
    by_complaint = {}
    for f in rows:
        by_complaint.setdefault(f.complaint_id, {})[f.field] = f.officer_value
    texts = dict(db.query(Complaint.id, Complaint.text).filter(Complaint.id.in_(list(by_complaint))).all())
    return [{"text": texts[cid], "category": v.get("category"), "department": v.get("department"),
             "priority": v.get("priority")} for cid, v in by_complaint.items() if cid in texts]


def _current_metrics():
    if not training.METRICS_PATH.exists():
        return None
    return json.loads(training.METRICS_PATH.read_text(encoding="utf-8"))


@router.get("/metrics")
def metrics(user: User = Depends(staff), db: Session = Depends(get_db)):
    last = db.query(ModelRun).order_by(ModelRun.id.desc()).first()
    q = db.query(Feedback)
    if last:
        q = q.filter(Feedback.created_at > last.created_at)
    runs = db.query(ModelRun).order_by(ModelRun.id.desc()).limit(10).all()
    return {
        "current": _current_metrics(),
        "model_version": get_predictor().version,
        "new_labels_since_last_run": q.filter(Feedback.action == "override").count(),
        "total_officer_labels": len(officer_labels(db)),
        "runs": [{"version": r.version, "labels_used": r.labels_used, "at": r.created_at.isoformat(),
                  "category_acc": r.metrics["category"]["test"]["accuracy"],
                  "department_acc": r.metrics["department"]["test"]["accuracy"],
                  "priority_acc": r.metrics["priority"]["test"]["accuracy"],
                  "agreement_before": (r.metrics.get("feedback") or {}).get("officer_agreement_before"),
                  "agreement_after": (r.metrics.get("feedback") or {}).get("officer_agreement_after")}
                 for r in runs],
    }


@router.post("/retrain")
def retrain(user: User = Depends(staff), db: Session = Depends(get_db)):
    if not _retrain_lock.acquire(blocking=False):
        raise HTTPException(409, "A retraining run is already in progress.")
    try:
        before = _current_metrics()
        labels = officer_labels(db)
        m = training.retrain(labels)
        get_predictor().load()  # hot-swap the live models
        db.add(ModelRun(version=m["version"], labels_used=len(labels), metrics=m, triggered_by=user.id))
        db.commit()
        return {"before": before, "after": m}
    finally:
        _retrain_lock.release()
