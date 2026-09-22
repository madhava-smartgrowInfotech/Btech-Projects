"""Login / registration, reference data and admin settings (departments + SLAs)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import admin_only, current_user, hash_password, make_token, user_out, verify_password
from ..config import GEMINI_API_KEY
from ..db import Department, User, Ward, get_db
from ..services.predictor import get_predictor
from ..services.taxonomy import CATEGORIES, CATEGORY_TO_DEPT, PRIORITIES

router = APIRouter(prefix="/api", tags=["auth", "admin"])


class Login(BaseModel):
    email: str
    password: str


class Register(BaseModel):
    name: str
    email: str
    password: str


@router.post("/auth/login")
def login(body: Login, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=body.email.strip().lower()).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(u), "user": user_out(u)}


@router.post("/auth/register")
def register(body: Register, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Enter a valid email address")
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if len(body.name.strip()) < 2:
        raise HTTPException(400, "Enter your name")
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(400, "An account with this email already exists - please log in")
    u = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password), role="citizen")
    db.add(u)
    db.commit()
    return {"token": make_token(u), "user": user_out(u)}


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_out(user)


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    return {
        "categories": [{"name": c, "department": CATEGORY_TO_DEPT[c]} for c in CATEGORIES],
        "departments": [{"id": d.id, "name": d.name, "sla_days": d.sla_days}
                        for d in db.query(Department).order_by(Department.name).all()],
        "priorities": PRIORITIES,
        "wards": [{"name": w.name, "lat": w.lat, "lng": w.lng} for w in db.query(Ward).order_by(Ward.name).all()],
    }


@router.get("/health")
def health():
    return {"status": "ok", "model_version": get_predictor().version, "gemini_configured": bool(GEMINI_API_KEY)}


class SlaUpdate(BaseModel):
    sla_days: int


@router.put("/departments/{dept_id}")
def update_department(dept_id: int, body: SlaUpdate, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    d = db.get(Department, dept_id)
    if not d:
        raise HTTPException(404, "Department not found")
    if not 1 <= body.sla_days <= 90:
        raise HTTPException(400, "SLA must be between 1 and 90 days")
    d.sla_days = body.sla_days
    db.commit()
    return {"id": d.id, "name": d.name, "sla_days": d.sla_days}
