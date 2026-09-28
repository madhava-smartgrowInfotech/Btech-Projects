from typing import Literal

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import FACILITIES, OPERATING_DAY, WARDS, day_to_date
from ..db import Admission, User, get_db
from ..services.engine import FLAGS, NUMERIC, TRAIN_END_DAY, get_engine

router = APIRouter(prefix="/api/admissions", tags=["admissions"])


class PatientIn(BaseModel):
    patient_ref: str = Field(default="", max_length=40)
    facility: Literal["A", "B", "C", "D", "E"]
    ward: Literal["General", "Surgical", "Maternity", "Paediatric", "ICU"]
    gender: Literal["F", "M"]
    rcount: int = Field(ge=0, le=5)
    dialysisrenalendstage: int = Field(0, ge=0, le=1)
    asthma: int = Field(0, ge=0, le=1)
    irondef: int = Field(0, ge=0, le=1)
    pneum: int = Field(0, ge=0, le=1)
    substancedependence: int = Field(0, ge=0, le=1)
    psychologicaldisordermajor: int = Field(0, ge=0, le=1)
    depress: int = Field(0, ge=0, le=1)
    psychother: int = Field(0, ge=0, le=1)
    fibrosisandother: int = Field(0, ge=0, le=1)
    malnutrition: int = Field(0, ge=0, le=1)
    hemo: int = Field(0, ge=0, le=1)
    hematocrit: float = Field(ge=2, le=30)
    neutrophils: float = Field(ge=0, le=300)
    sodium: float = Field(ge=110, le=170)
    glucose: float = Field(ge=0, le=400)
    bloodureanitro: float = Field(ge=0, le=700)
    creatinine: float = Field(ge=0.1, le=10)
    bmi: float = Field(ge=10, le=70)
    pulse: float = Field(ge=20, le=220)
    respiration: float = Field(ge=0, le=15)
    secondarydiagnosisnonicd9: int = Field(ge=0, le=15)


def to_record(p: PatientIn) -> dict:
    r = p.model_dump()
    r["facid"] = r.pop("facility")
    return r


DISCLAIMER = ("Decision support only: the estimate supports, and does not replace, the judgement of the "
              "treating clinician.")


@router.post("/predict")
def predict(p: PatientIn, user: User = Depends(current_user)):
    return {**get_engine().predict_one(to_record(p)), "disclaimer": DISCLAIMER}


@router.post("")
def admit(p: PatientIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pred = get_engine().predict_one(to_record(p))
    n = db.query(Admission).count() + 1
    a = Admission(admit_date=day_to_date(OPERATING_DAY).isoformat(), patient_ref=p.patient_ref or f"ADM-{n:05d}",
                  facility=p.facility, ward=p.ward, features=p.model_dump(), predicted_days=pred["predicted_days"],
                  long_stay=pred["long_stay"], long_stay_probability=pred["long_stay_probability"], prediction=pred,
                  created_by=user.email)
    db.add(a)
    db.commit()
    return {**admission_out(a), "disclaimer": DISCLAIMER}


def admission_out(a: Admission):
    return {"id": a.id, "patient_ref": a.patient_ref, "admit_date": a.admit_date, "facility": a.facility,
            "ward": a.ward, "predicted_days": a.predicted_days, "long_stay": a.long_stay,
            "long_stay_probability": a.long_stay_probability, "prediction": a.prediction,
            "created_by": a.created_by, "created_at": a.created_at.isoformat()}


@router.get("")
def list_admissions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [admission_out(a) for a in db.scalars(select(Admission).order_by(Admission.id.desc()).limit(100))]


@router.get("/sample")
def sample(profile: Literal["long", "short", "any"] = "any", ward: str | None = None,
           user: User = Depends(current_user)):
    """A real held-out record from the dataset, to prefill the admission form (clearly marked as sample data)."""
    p = get_engine().patients
    pool = p[p.admit_day >= TRAIN_END_DAY]
    if profile == "long":
        pool = pool[(pool.pred_los >= 5.8) & (pool.pred_los <= 7.5)]
    elif profile == "short":
        pool = pool[pool.pred_los <= 3]
    if ward in WARDS:
        pool = pool[pool.ward == ward]
    if pool.empty:
        raise HTTPException(404, "No sample record matches")
    r = pool.iloc[int(np.random.default_rng().integers(len(pool)))]
    out = {"patient_ref": f"SAMPLE-{int(r.eid)}", "facility": r.facid, "ward": r.ward, "gender": r.gender,
           "rcount": int(r.rcount)}
    out.update({c: int(r[c]) for c in FLAGS})
    out.update({c: round(float(r[c]), 2) for c in NUMERIC})
    out["secondarydiagnosisnonicd9"] = int(r.secondarydiagnosisnonicd9)
    return {"sample": out, "source": "Held-out record from the Hospital Length of Stay dataset (sample data)",
            "facilities": FACILITIES}
