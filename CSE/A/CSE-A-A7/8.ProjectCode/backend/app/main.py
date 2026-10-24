import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import hash_password
from .db import Base, Patient, SessionLocal, User, engine
from .routes.api import router
from .services import extract, triage
from .services.features import FLAGS, REPORT_FLAGS, VITALS

log = logging.getLogger("athena")
ROOT = Path(__file__).resolve().parents[2]

DEMO_USERS = [
    ("Dr. Maya Rao", "clinician@athena.health", "Athena@123", "clinician"),
    ("Ops Admin", "admin@athena.health", "Athena@123", "admin"),
]


def seed_users(db):
    for name, email, pw, role in DEMO_USERS:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(name=name, email=email, password_hash=hash_password(pw), role=role))
    db.commit()


def seed_sample_queue(db, n=12):
    """Fill an empty queue with hold-out rows from the synthetic dataset (source='sample')."""
    path = ROOT / "data" / "sample" / "holdout_sample.csv"
    if db.query(Patient).count() or not path.exists():
        return
    df = pd.read_csv(path).head(n)
    for i, r in df.iterrows():
        vitals = {k: (int(r[k]) if k not in ("temp_c",) else float(r[k])) for k in
                  ("age", "heart_rate", "sbp", "dbp", "spo2", "temp_c", "resp_rate")}
        vitals["arrival_mode"] = r["arrival_mode"]
        flags = {f: int(r[f]) for f in FLAGS}
        res = triage.predict(vitals, flags)
        groups = {"symptoms": "symptom", "findings": "finding", "history": "history"}
        report = {k: [{"flag": f, "label": REPORT_FLAGS[f][1], "text": REPORT_FLAGS[f][1].lower(), "category": c, "page": 1}
                      for f in FLAGS if flags[f] and REPORT_FLAGS[f][0] == c] for k, c in groups.items()}
        report["labs"] = []
        report["flags"] = flags
        report["note"] = "Sample case from the synthetic dataset"
        db.add(Patient(
            name=f"Sample case {i + 1:02d}", source="sample", vitals=vitals, report=report, fused=res["fused"],
            model_priority=res["priority"], priority=res["priority"], risk_level=res["risk_level"],
            confidence=res["confidence"], probabilities=res["probabilities"], shap=res["shap"],
            model_seconds=res["seconds"], total_seconds=res["seconds"], recorded_outcome=int(r["priority"]),
        ))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    # warm the model/SHAP explainer and the OCR engine so the first patient is not slow
    try:
        triage.predict({"age": 40, "heart_rate": 80, "sbp": 120, "dbp": 80, "spo2": 98, "temp_c": 36.8, "resp_rate": 16}, {})
    except Exception as exc:
        log.warning("model warm-up skipped: %s", exc)
    threading.Thread(target=lambda: extract._ocr(), daemon=True).start()
    db = SessionLocal()
    try:
        seed_users(db)
        try:
            seed_sample_queue(db)
        except Exception as exc:  # model missing on a fresh checkout: queue stays empty
            log.warning("sample queue not seeded: %s", exc)
    finally:
        db.close()
    yield


app = FastAPI(title="ATHENA triage API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5307", "http://127.0.0.1:5307"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
