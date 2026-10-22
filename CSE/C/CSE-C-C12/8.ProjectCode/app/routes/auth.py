from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import RegisterRequest, LoginRequest
from app.auth import hash_password, verify_password, create_token, decode_token
from app.database import SessionLocal

router = APIRouter(prefix="/api/auth", tags=["auth"])

def _get_current_user(request: Request, db: Session):
    token = request.cookies.get("carelens_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None
    data = decode_token(token)
    if not data:
        return None
    return db.query(User).filter(User.id == int(data["sub"])).first()

def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = _get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return user

@router.post("/register")
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not create account. Please try again.")
    db.refresh(user)
    token = create_token(user.id, user.email)
    response.set_cookie("carelens_token", token, httponly=True, samesite="lax", path="/")
    return {"email": user.email, "token": token}

@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_token(user.id, user.email)
    response.set_cookie("carelens_token", token, httponly=True, samesite="lax", path="/")
    return {"email": user.email, "token": token}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("carelens_token", path="/")
    return {"ok": True}

@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return {"email": user.email, "id": user.id}
