"""User directory endpoints (needed for sharing)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.schemas.schemas import UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


def _safe(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role,
            "public_key": u.public_key, "has_private_key": bool(u.encrypted_private_key),
            "is_active": u.is_active, "created_at": u.created_at}


@router.get("", response_model=list[UserOut])
def list_users(q: str = Query(default="", max_length=120), db: Session = Depends(get_db),
               current: User = Depends(get_current_user)):
    query = db.query(User).filter(User.is_active.is_(True))
    if q:
        like = f"%{q.strip().lower()}%"
        query = query.filter((User.email.ilike(like)) | (User.name.ilike(like)))
    users = query.order_by(User.id.asc()).limit(50).all()
    return [_safe(u) for u in users]


@router.get("/{user_id}/public-key")
def get_public_key(user_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None or not user.public_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User or public key not found")
    return {"user_id": user.id, "email": user.email, "public_key": user.public_key}
