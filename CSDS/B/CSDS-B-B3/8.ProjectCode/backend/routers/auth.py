from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_db, current_user, make_token, user_dict
from database.models import (
    User, StudentProfile, MentorProfile, UserPoints, Resource, LearningTopic, CareerRole, CodingProblem, InterviewQuestion,
)
from services.authentication import authenticate_user, register_user
from services.gamification_service import award_xp

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"


@router.post("/login")
def login(body: LoginIn, db=Depends(get_db)):
    user, error = authenticate_user(db, body.email, body.password)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return {"token": make_token(user.id), "user": user_dict(user)}


@router.post("/register")
def register(body: RegisterIn, db=Depends(get_db)):
    if body.role not in ("student", "mentor"):
        raise HTTPException(status_code=422, detail="Choose student or mentor.")
    user, error = register_user(db, body.name, body.email, body.password, body.role)
    if error:
        raise HTTPException(status_code=422, detail=error)
    if body.role == "student":
        db.add(StudentProfile(user_id=user.id, wallet_balance=500.0))
    else:
        db.add(MentorProfile(user_id=user.id))
    db.add(UserPoints(user_id=user.id, xp=0, level="Newcomer"))
    db.flush()
    award_xp(db, user.id, "profile_completed")
    msg = "Account created. You can sign in now."
    if body.role == "mentor":
        msg += " An admin must verify your mentor profile before students can find you."
    return {"message": msg}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"user": user_dict(user)}


@router.get("/public/stats")
def public_stats(db=Depends(get_db)):
    """Real catalogue counts for the landing page (no login needed, read-only)."""
    return {
        "students": db.query(User).filter_by(role="student").count(),
        "mentors": db.query(User).filter_by(role="mentor").count(),
        "resources": db.query(Resource).filter_by(is_approved=True).count(),
        "topics": db.query(LearningTopic).count(),
        "careers": db.query(CareerRole).count(),
        "problems": db.query(CodingProblem).count(),
        "interview_questions": db.query(InterviewQuestion).count(),
    }
