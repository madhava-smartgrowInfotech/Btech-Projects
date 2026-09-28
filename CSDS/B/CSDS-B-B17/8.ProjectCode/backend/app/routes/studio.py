import json
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user, require_supervisor
from ..config import SAMPLE_CALLS_DIR, UPLOAD_DIR
from ..db import Call, User, get_db
from ..services import pipeline, studio
from .calls import call_brief

router = APIRouter(prefix="/api/studio", tags=["studio"])


@router.get("/scripts")
def scripts(user: User = Depends(current_user)):
    out = []
    for s in studio.load_scripts():
        lines = studio.normalise_lines(s["lines"])
        out.append({"id": s["id"], "title": s["title"], "intent": s["intent"], "agent": s["agent"],
                    "text": "\n".join(f"{'Agent' if l['speaker'] == 'agent' else 'Customer'} [{l['sentiment']}]: {l['text']}"
                                      for l in lines)})
    return out


class GenerateIn(BaseModel):
    script_id: str | None = None
    script_text: str | None = None
    title: str | None = None
    agent_id: int | None = None


@router.post("/generate")
def generate(body: GenerateIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ref_intent = None
    if body.script_text and body.script_text.strip():
        lines, bad = studio.parse_script_text(body.script_text)
        if bad:
            raise HTTPException(400, f"Lines {', '.join(map(str, bad[:8]))} are not in the form 'Agent: text' or 'Customer: text'")
        base = studio.get_script(body.script_id) if body.script_id else None
        if base and [l["text"] for l in lines] == [l["text"] for l in studio.normalise_lines(base["lines"])]:
            ref_intent = base["intent"]
            lines = studio.normalise_lines(base["lines"])  # keep pause / overlap timing of the stock script
        title = body.title or (base["title"] if base else "Custom sample call")
    elif body.script_id:
        base = studio.get_script(body.script_id)
        if not base:
            raise HTTPException(404, "Unknown script")
        lines, ref_intent, title = studio.normalise_lines(base["lines"]), base["intent"], body.title or base["title"]
    else:
        raise HTTPException(400, "Pick a script or write one")
    if len(lines) < 2 or not any(l["speaker"] == "customer" for l in lines):
        raise HTTPException(400, "The script needs at least one agent line and one customer line")
    if len(lines) > 40:
        raise HTTPException(400, "Keep sample scripts to 40 lines or fewer")

    agent_id = user.id if user.role == "agent" else body.agent_id
    if agent_id and not db.query(User).filter_by(id=agent_id, role="agent").first():
        raise HTTPException(400, "Unknown agent")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"sample_{uuid.uuid4().hex[:10]}.flac"
    try:
        ref = studio.synthesize(lines, path, seed=int(datetime.utcnow().timestamp()) % 10000)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(500, str(e))
    c = Call(title=f"[Sample] {title}"[:200], audio_path=str(path), source="sample", is_sample=True, agent_id=agent_id,
             uploaded_by=user.id, duration=ref["duration"], channels=2,
             reference={"intent": ref_intent, "lines": ref["lines"]})
    db.add(c)
    db.commit()
    pipeline.enqueue(c.id)
    return call_brief(c)


@router.post("/import-samples")
def import_samples(db: Session = Depends(get_db), user: User = Depends(require_supervisor)):
    """Register the committed sample recordings (data/sample/calls) as calls and queue them for analysis."""
    metas = sorted(SAMPLE_CALLS_DIR.glob("*.json"))
    if not metas:
        raise HTTPException(404, "No sample recordings found - run scripts/generate_sample_calls.py")
    existing = {c.audio_path for c in db.query(Call).filter(Call.source == "sample")}
    added = []
    for m in metas:
        meta = json.loads(m.read_text())
        audio = str(m.with_suffix(".flac"))
        if audio in existing:
            continue
        agent = db.query(User).filter_by(email=meta.get("agent")).first()
        c = Call(title=f"[Sample] {meta['title']}", audio_path=audio, source="sample", is_sample=True,
                 agent_id=agent.id if agent else None, uploaded_by=user.id, duration=meta.get("duration"), channels=2,
                 reference={"intent": meta["intent"], "lines": meta["lines"], "script_id": meta["id"]},
                 recorded_at=datetime.utcnow() - timedelta(days=int(meta.get("day_offset", 0))))
        db.add(c)
        db.commit()
        added.append(c)
    for c in added:
        pipeline.enqueue(c.id)
    return {"added": len(added), "skipped": len(metas) - len(added), "calls": [call_brief(c) for c in added]}
