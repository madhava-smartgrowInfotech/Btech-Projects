from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import check_password, current_user, hash_password, make_token, public_user
from ..db import Application, Drive, Notification, Submission, TestAttempt, User, get_db, jload
from ..services import progress

router = APIRouter(prefix="/api", tags=["auth"])


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str
    role: str = "candidate"
    target_role: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if body.role not in ("candidate", "recruiter"):
        raise HTTPException(400, "Self sign-up is available for candidates and recruiters")
    if len(body.password) < 6 or "@" not in email or not body.name.strip():
        raise HTTPException(400, "Enter a name, a valid email and a password of 6+ characters")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    u = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password), role=body.role,
             target_role=body.target_role)
    db.add(u)
    db.commit()
    return {"token": make_token(u), "user": public_user(u)}


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not u or not check_password(body.password, u.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(u), "user": public_user(u)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return public_user(user)


@router.get("/me/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    st = progress.recompute(db, user) if user.role == "candidate" else None
    notes = db.scalars(select(Notification).where(Notification.user_id == user.id)
                       .order_by(Notification.created_at.desc()).limit(15)).all()
    out = {"user": public_user(user),
           "notifications": [{"id": n.id, "text": n.text, "read": n.read, "at": n.created_at.isoformat()} for n in notes]}
    if st:
        tests = db.scalars(select(TestAttempt).where(TestAttempt.user_id == user.id, TestAttempt.submitted_at.is_not(None))
                           .order_by(TestAttempt.submitted_at.desc()).limit(5)).all()
        subs = db.scalars(select(Submission).where(Submission.user_id == user.id)
                          .order_by(Submission.created_at.desc()).limit(5)).all()
        apps = db.execute(select(Application, Drive).join(Drive, Drive.id == Application.drive_id)
                          .where(Application.candidate_id == user.id)).all()
        out.update(
            stats=st, ladder=progress.ladder(st),
            recent_tests=[{"id": t.id, "kind": t.kind, "topic": t.topic, "score": t.score_pct, "correct": t.correct,
                           "total": t.total, "at": t.submitted_at.isoformat()} for t in tests],
            recent_submissions=[{"id": s.id, "problem": s.problem_slug, "language": s.language, "verdict": s.verdict,
                                 "at": s.created_at.isoformat()} for s in subs],
            drives=[{"drive": d.title, "company": d.company, "role": d.role, "status": a.status} for a, d in apps],
        )
    return out


@router.post("/me/notifications/read")
def read_notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    for n in db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read.is_(False))).all():
        n.read = True
    db.commit()
    return {"ok": True}
