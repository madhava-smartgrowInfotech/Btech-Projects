from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db
from ..core.security import require_role
from ..models import Notification, User
from ..schemas.auth import AdminUserUpdate, UserOut
from ..services import notifier, settings_service
from ..services.sample_data import remove_sample_data, seed_in_background
from ..services.sample_data import status as sample_status

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: AdminUserUpdate, admin: User = Depends(require_role("admin")),
                db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id and (body.role not in (None, "admin") or body.is_active is False):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You cannot remove your own admin access")
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/settings", summary="Detection thresholds, notification switches and channel status")
def get_settings(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> dict:
    ok_tg, chat = notifier.telegram_ready(db)
    return {
        "settings": settings_service.describe(db),
        "channels": {
            "telegram": {"token": bool(settings.telegram_bot_token), "chat_id": chat or None, "ready": ok_tg},
            "email": {"configured": bool(settings.smtp_user and settings.smtp_password), "from": settings.smtp_user or None,
                      "desk_email": settings.desk_email or None, "ready": notifier.email_ready(db)},
            "gemini": {"configured": bool(settings.gemini_api_key), "model": settings.gemini_model},
            "opencellid": {"configured": bool(settings.opencellid_api_key)},
        },
        "sample_data": dict(sample_status),
        "demo_preset": settings_service.DEMO_PRESET,
    }


@router.put("/settings", summary="Change settings (only the keys you send)")
def put_settings(changes: dict[str, Any] = Body(...), admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> dict:
    try:
        settings_service.update(db, changes, admin.id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, detail=str(exc))
    return get_settings(admin, db)


@router.post("/settings/preset/{name}", summary="Apply the demo (fast) or standard detection thresholds")
def apply_preset(name: str, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> dict:
    if name == "demo":
        settings_service.update(db, settings_service.DEMO_PRESET, admin.id)
    elif name == "standard":
        settings_service.update(db, {k: settings_service.SPEC[k][1] for k in settings_service.DEMO_PRESET}, admin.id)
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown preset")
    return get_settings(admin, db)


@router.post("/notifications/test", summary="Send a real test message on every configured channel")
def test_notifications(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[dict]:
    return notifier.send_test(db)


@router.post("/telegram/link", summary="Use the chat that last messaged the bot for desk notifications")
def link_telegram(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> dict:
    return notifier.link_telegram_chat(db, admin.id)


@router.get("/notifications", summary="Recent notifications and their delivery state")
def list_notifications(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Notification).order_by(Notification.created_at.desc()).limit(50).all()
    return [{"id": n.id, "complaint_id": n.complaint_id, "channel": n.channel, "recipient": n.recipient, "subject": n.subject,
             "status": n.status, "attempts": n.attempts, "last_error": n.last_error, "created_at": n.created_at.isoformat() + "Z",
             "sent_at": n.sent_at.isoformat() + "Z" if n.sent_at else None} for n in rows]


@router.delete("/sample-data", summary="Remove the replayed public-dataset readings and their complaints")
def delete_sample(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> dict:
    return remove_sample_data(db)


@router.post("/sample-data", summary="Load the sample data again")
def load_sample(_: User = Depends(require_role("admin"))) -> dict:
    seed_in_background()
    return {"state": "loading"}
