from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Conversation, Message, get_db

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class MessageIn(BaseModel):
    side: str = Field(pattern="^(signer|hearing)$")
    text: str = Field(min_length=1, max_length=2000)
    gloss: list[str] | None = None
    confidence: float | None = None
    latency_ms: float | None = None
    source: str | None = Field(None, max_length=20)


class ConversationIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    messages: list[MessageIn] = Field(min_length=1, max_length=1000)


def _msg(m):
    return {"id": m.id, "side": m.side, "text": m.text, "gloss": m.gloss, "confidence": m.confidence,
            "latency_ms": m.latency_ms, "source": m.source, "created_at": m.created_at.isoformat()}


def _own(db, cid, user):
    c = db.get(Conversation, cid)
    if not c or c.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return c


@router.post("")
def create(body: ConversationIn, db: Session = Depends(get_db), user=Depends(current_user)):
    c = Conversation(user_id=user.id, title=body.title.strip())
    c.messages = [Message(**m.model_dump()) for m in body.messages]
    db.add(c)
    db.commit()
    return {"id": c.id, "title": c.title, "messages": len(c.messages)}


@router.get("")
def list_all(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.execute(
        select(Conversation, func.count(Message.id))
        .outerjoin(Message).where(Conversation.user_id == user.id)
        .group_by(Conversation.id).order_by(Conversation.id.desc())
    ).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat(), "messages": n} for c, n in rows]


@router.get("/{cid}")
def get(cid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    c = _own(db, cid, user)
    return {"id": c.id, "title": c.title, "created_at": c.created_at.isoformat(),
            "messages": [_msg(m) for m in c.messages]}


@router.post("/{cid}/messages")
def add_message(cid: int, body: MessageIn, db: Session = Depends(get_db), user=Depends(current_user)):
    c = _own(db, cid, user)
    m = Message(conversation_id=c.id, **body.model_dump())
    db.add(m)
    db.commit()
    return _msg(m)


@router.delete("/{cid}")
def delete(cid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    db.delete(_own(db, cid, user))
    db.commit()
    return {"ok": True}
