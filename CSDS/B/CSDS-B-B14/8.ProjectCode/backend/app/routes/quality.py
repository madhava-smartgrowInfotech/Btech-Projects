from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import QualityCheck, User, add_alert, get_db
from ..services import quality

router = APIRouter(prefix="/api/quality", tags=["quality"])


class SampleIn(BaseModel):
    sample_name: str = "Lab sample"
    ph: float | None = None
    Hardness: float | None = None
    Solids: float | None = None
    Chloramines: float | None = None
    Sulfate: float | None = None
    Conductivity: float | None = None
    Organic_carbon: float | None = None
    Trihalomethanes: float | None = None
    Turbidity: float | None = None


@router.post("/predict")
def predict(body: SampleIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    values = {f: getattr(body, f) for f in quality.FEATURES}
    r = quality.predict(values)
    exceeded = sum(1 for x in r["limits"] if x["status"] == "exceeds")
    qc = QualityCheck(user_email=user.email, sample_name=body.sample_name, values=values, potable=r["potable"],
                      confidence=r["confidence"], exceeded=exceeded)
    db.add(qc)
    db.commit()
    if not r["potable"]:
        top = ", ".join(x["label"] for x in r["reasons"][:3] if x["shap"] < 0) or "several parameters"
        add_alert(db, "quality", "high" if r["confidence"] >= 0.7 else "medium",
                  f"{body.sample_name}: not potable ({round(r['confidence'] * 100)}%)",
                  f"Main drivers: {top}. {exceeded} parameter(s) outside guideline limits.", ref=f"quality:{qc.id}")
    return {"id": qc.id, **r}


@router.get("/samples")
def samples(user: User = Depends(current_user)):
    return quality.samples()


@router.get("/limits")
def limits(user: User = Depends(current_user)):
    return [{"parameter": f, "label": quality.LABELS[f], "min": lo, "max": hi, "unit": u, "source": s}
            for f, (lo, hi, u, s) in quality.LIMITS.items()]


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(QualityCheck).order_by(QualityCheck.id.desc()).limit(30)).all()
    return [{"id": r.id, "created_at": r.created_at.isoformat(), "sample_name": r.sample_name, "potable": r.potable,
             "confidence": r.confidence, "exceeded": r.exceeded, "user": r.user_email} for r in rows]
