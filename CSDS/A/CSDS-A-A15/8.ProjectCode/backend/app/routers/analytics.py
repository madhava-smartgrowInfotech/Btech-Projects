import json
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.ml.labels import DEFECT_INFO
from app.models import Inspection, User
from app.schemas import AnalyticsSummary

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Inspection).filter(Inspection.user_id == current_user.id).all()

    total = len(rows)
    avg_conf = round(sum(r.confidence for r in rows) / total, 4) if total else 0.0

    defect_dist = Counter(r.display_name for r in rows)
    severity_dist = Counter(r.severity for r in rows)

    by_day: dict[str, int] = defaultdict(int)
    for r in rows:
        day = r.created_at.strftime("%Y-%m-%d")
        by_day[day] += 1
    inspections_over_time = [{"date": d, "count": c} for d, c in sorted(by_day.items())]

    model_metrics = {}
    if settings.metrics_path.exists():
        raw = json.loads(settings.metrics_path.read_text())
        model_metrics = {
            "test_accuracy": raw.get("test_accuracy"),
            "best_val_accuracy": raw.get("best_val_accuracy"),
            "class_names": raw.get("class_names"),
            "confusion_matrix": raw.get("confusion_matrix"),
            "classification_report": raw.get("classification_report"),
            "history": raw.get("history"),
            "dataset_sizes": raw.get("dataset_sizes"),
            "trained_at": raw.get("trained_at"),
        }

    return AnalyticsSummary(
        total_inspections=total,
        average_confidence=avg_conf,
        defect_distribution=dict(defect_dist),
        severity_distribution=dict(severity_dist),
        inspections_over_time=inspections_over_time,
        model_metrics=model_metrics,
    )


@router.get("/defect-catalog")
def get_defect_catalog(current_user: User = Depends(get_current_user)):
    return DEFECT_INFO
