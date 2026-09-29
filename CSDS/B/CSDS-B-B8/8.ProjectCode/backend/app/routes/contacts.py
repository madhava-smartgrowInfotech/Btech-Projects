from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Contact, get_db
from ..services.alerts import email_configured, telegram_chats, telegram_configured
from ..services.settings import get_settings, update_settings

router = APIRouter(prefix="/api", tags=["contacts"], dependencies=[Depends(current_user)])


class ContactIn(BaseModel):
    name: str
    relation: str = ""
    email: str = ""
    telegram_chat_id: str = ""
    active: bool = True


def out(c):
    return {"id": c.id, "name": c.name, "relation": c.relation, "email": c.email,
            "telegram_chat_id": c.telegram_chat_id, "active": c.active}


def check(body):
    if not body.name.strip():
        raise HTTPException(400, "Name is required")
    if not body.email.strip() and not body.telegram_chat_id.strip():
        raise HTTPException(400, "Add an email or a Telegram chat ID so alerts can reach this contact")
    if body.email and "@" not in body.email:
        raise HTTPException(400, "Email looks invalid")


def channels():
    return {"telegram": telegram_configured(), "email": email_configured()}


@router.get("/contacts")
def list_contacts(db: Session = Depends(get_db)):
    return [out(c) for c in db.query(Contact).order_by(Contact.id)]


@router.post("/contacts")
def add_contact(body: ContactIn, db: Session = Depends(get_db)):
    check(body)
    c = Contact(**{k: (v.strip() if isinstance(v, str) else v) for k, v in body.model_dump().items()})
    db.add(c)
    db.commit()
    return out(c)


@router.put("/contacts/{cid}")
def edit_contact(cid: int, body: ContactIn, db: Session = Depends(get_db)):
    check(body)
    c = db.get(Contact, cid)
    if not c:
        raise HTTPException(404, "Contact not found")
    for k, v in body.model_dump().items():
        setattr(c, k, v.strip() if isinstance(v, str) else v)
    db.commit()
    return out(c)


@router.delete("/contacts/{cid}")
def delete_contact(cid: int, db: Session = Depends(get_db)):
    c = db.get(Contact, cid)
    if not c:
        raise HTTPException(404, "Contact not found")
    db.delete(c)
    db.commit()
    return {"deleted": cid}


@router.get("/telegram/chats")
def find_chats():
    try:
        return telegram_chats()
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/settings")
def read_settings():
    return {**get_settings(), "channels": channels()}


@router.put("/settings")
def write_settings(body: dict):
    if "low_light" in body and body["low_light"] not in ("auto", "on", "off"):
        raise HTTPException(400, "low_light must be auto, on or off")
    limits = (("countdown_seconds", 5, 300), ("confirm_seconds", 1, 30), ("inactivity_minutes", 0.5, 720))
    for k, lo, hi in limits:
        if k in body:
            try:
                ok = lo <= float(body[k]) <= hi
            except (TypeError, ValueError):
                ok = False
            if not ok:
                raise HTTPException(400, f"{k.replace('_', ' ')} must be between {lo} and {hi}")
    body.pop("monitor_running", None)
    return {**update_settings(body), "channels": channels()}
