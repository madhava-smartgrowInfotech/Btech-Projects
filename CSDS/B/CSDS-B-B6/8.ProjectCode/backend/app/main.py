"""UniHealth platform API."""
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .auth import hash_password
from .config import DATA_DIR, DEMO_PASSWORD, HOSPITALS
from .db import SessionLocal, User, init_db
from .routes import consents, platform, records

app = FastAPI(title="UniHealth API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5206", "http://127.0.0.1:5206"],
                   allow_methods=["*"], allow_headers=["*"])
for r in (platform.router, records.router, consents.router):
    app.include_router(r, prefix="/api")


def seed_users():
    """Demo accounts (all use DEMO_PASSWORD). Patient accounts point at a sample hospital record."""
    short = {"A": "northbridge", "B": "riverside", "C": "lakeview"}
    users = [("admin", "admin", "Platform Administrator", None, None)]
    for k, h in HOSPITALS.items():
        users.append((f"dr.{short[k]}", "doctor", f"Physician, {h['name']}", k, None))
        users.append((f"staff.{short[k]}", "staff", f"Records Staff, {h['name']}", k, None))
    demo_file = DATA_DIR / "sample" / "demo_patients.json"
    if demo_file.exists():
        for p in json.loads(demo_file.read_text()):
            users.append((p["username"], "patient", p["name"], p["hospital"], p["local_id"]))
    with SessionLocal() as db:
        pw = None
        for username, role, name, hkey, local in users:
            if db.scalar(select(User).where(User.username == username)):
                continue
            pw = pw or hash_password(DEMO_PASSWORD)
            db.add(User(username=username, password_hash=pw, role=role, display_name=name,
                        hospital_key=hkey, local_patient_id=local))
        db.commit()


@app.on_event("startup")
def startup():
    init_db()
    seed_users()


@app.get("/api/health")
def health():
    return {"status": "ok"}
