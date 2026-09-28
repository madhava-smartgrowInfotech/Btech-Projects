import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import current_user, user_from_header_or_query
from ..config import UPLOAD_DIR
from ..db import Call, User, get_db
from ..services import pipeline
from ..services.summary import SummaryError

router = APIRouter(prefix="/api", tags=["calls"])

AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".webm", ".m4a", ".mp4", ".aac", ".opus"}
MAX_MB = 60


def visible(db: Session, user: User):
    q = db.query(Call)
    return q if user.role == "supervisor" else q.filter(Call.agent_id == user.id)


def get_call(db: Session, user: User, call_id: int) -> Call:
    c = visible(db, user).filter(Call.id == call_id).first()
    if c is None:
        raise HTTPException(404, "Call not found")
    return c


def call_brief(c: Call, q: str | None = None) -> dict:
    d = {
        "id": c.id, "title": c.title, "source": c.source, "is_sample": c.is_sample, "status": c.status,
        "stage": c.stage, "error": c.error, "duration": c.duration, "agent": c.agent.name if c.agent else None,
        "agent_id": c.agent_id, "intent": c.intent, "topic": c.topic, "sentiment": c.sentiment, "score": c.score,
        "flags": len(c.flags or []), "recorded_at": c.recorded_at.isoformat() + "Z",
        "summary": (c.summary or {}).get("summary"),
    }
    if q and c.transcript_text:
        m = re.search(re.escape(q), c.transcript_text, re.I)
        if m:
            s = max(0, m.start() - 60)
            d["snippet"] = ("..." if s else "") + c.transcript_text[s:m.end() + 80].replace("\n", " ") + "..."
    return d


def call_full(c: Call) -> dict:
    d = call_brief(c)
    d.update({
        "channels": c.channels, "segments": c.segments or [], "intent_confidence": c.intent_confidence,
        "intent_top": (c.intent_top or {}).get("top", []), "intent_evidence": (c.intent_top or {}).get("evidence"),
        "keywords": c.keywords or [], "sentiment_change": c.sentiment_change, "flags": c.flags or [],
        "summary": c.summary, "summary_error": c.summary_error, "scorecard": c.scorecard,
        "reference": c.reference, "processed_at": c.processed_at.isoformat() + "Z" if c.processed_at else None,
    })
    return d


@router.get("/agents")
def agents(db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = db.query(User).filter(User.role == "agent")
    if user.role != "supervisor":
        q = q.filter(User.id == user.id)
    return [{"id": u.id, "name": u.name, "email": u.email} for u in q.order_by(User.name)]


@router.get("/calls")
def list_calls(q: str | None = None, agent_id: int | None = None, intent: str | None = None, status: str | None = None,
               limit: int = 200, db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = visible(db, user)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Call.transcript_text.ilike(like), Call.title.ilike(like), Call.intent.ilike(like)))
    if agent_id:
        query = query.filter(Call.agent_id == agent_id)
    if intent:
        query = query.filter(Call.intent == intent)
    if status:
        query = query.filter(Call.status == status)
    rows = query.order_by(Call.recorded_at.desc(), Call.id.desc()).limit(min(limit, 500)).all()
    return {"calls": [call_brief(c, q) for c in rows], "queue": pipeline.queue_size()}


@router.post("/calls")
async def upload_calls(files: list[UploadFile] = File(...), agent_id: int | None = Form(None),
                       source: str = Form("upload"), title: str | None = Form(None),
                       db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role == "agent":
        agent_id = user.id
    elif agent_id is not None and not db.query(User).filter_by(id=agent_id, role="agent").first():
        raise HTTPException(400, "Unknown agent")
    if not files:
        raise HTTPException(400, "Choose at least one recording")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    created = []
    for f in files:
        ext = Path(f.filename or "").suffix.lower() or (".webm" if source == "microphone" else "")
        if ext not in AUDIO_EXT:
            raise HTTPException(400, f"{f.filename}: unsupported file type (use {', '.join(sorted(AUDIO_EXT))})")
        data = await f.read()
        if len(data) > MAX_MB * 1024 * 1024:
            raise HTTPException(400, f"{f.filename}: larger than {MAX_MB} MB")
        if len(data) < 1000:
            raise HTTPException(400, f"{f.filename}: the file is empty or too short")
        path = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        path.write_bytes(data)
        name = title if (title and len(files) == 1) else Path(f.filename or "recording").stem
        c = Call(title=name[:200] or "Recording", audio_path=str(path), source="microphone" if source == "microphone" else "upload",
                 agent_id=agent_id, uploaded_by=user.id)
        db.add(c)
        db.commit()
        created.append(c)
    for c in created:
        pipeline.enqueue(c.id)
    return {"calls": [call_brief(c) for c in created]}


@router.get("/calls/{call_id}")
def get_one(call_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return call_full(get_call(db, user, call_id))


@router.get("/calls/{call_id}/audio")
def audio(call_id: int, db: Session = Depends(get_db), user: User = Depends(user_from_header_or_query)):
    c = get_call(db, user, call_id)
    p = Path(c.audio_path)
    if not p.exists():
        raise HTTPException(404, "Audio file is missing")
    media = {".flac": "audio/flac", ".wav": "audio/wav", ".mp3": "audio/mpeg", ".webm": "audio/webm",
             ".ogg": "audio/ogg", ".m4a": "audio/mp4", ".mp4": "audio/mp4"}.get(p.suffix.lower(), "application/octet-stream")
    return FileResponse(p, media_type=media)


@router.post("/calls/{call_id}/reprocess")
def reprocess(call_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = get_call(db, user, call_id)
    if c.status in ("queued", "processing"):
        raise HTTPException(409, "This call is already being analysed")
    c.status, c.stage, c.error = "queued", "", ""
    db.commit()
    pipeline.enqueue(c.id)
    return call_brief(c)


@router.post("/calls/{call_id}/summary")
def regenerate_summary(call_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = get_call(db, user, call_id)
    if c.status != "done":
        raise HTTPException(409, "The call has not been analysed yet")
    try:
        pipeline.resummarise(c.id)
    except SummaryError as e:
        raise HTTPException(502, str(e))
    db.refresh(c)
    return call_full(c)


@router.delete("/calls/{call_id}")
def delete(call_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = get_call(db, user, call_id)
    if c.status in ("queued", "processing"):
        raise HTTPException(409, "Wait until the analysis finishes before deleting")
    p = Path(c.audio_path)
    if p.exists() and p.parent == UPLOAD_DIR:
        p.unlink()
    db.delete(c)
    db.commit()
    return {"ok": True}
