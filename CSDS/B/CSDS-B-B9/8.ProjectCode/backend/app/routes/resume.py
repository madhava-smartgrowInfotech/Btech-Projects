"""F7 AI resume analysis."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, require
from ..db import Resume, User, get_db, jdump, jload
from ..services import ai, progress
from ..services import resume as svc

router = APIRouter(prefix="/api/resume", tags=["resume"])
MAX_BYTES = 5 * 1024 * 1024


@router.get("/roles")
def roles():
    return [{"id": r, "label": svc.pretty(r)} for r in svc.roles()]


@router.post("/analyze")
async def analyze(file: UploadFile = File(...), target_role: str = Form(""), ai_tips: bool = Form(True),
                  user: User = Depends(require("candidate")), db: Session = Depends(get_db)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "The file is empty")
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "PDF must be 5 MB or smaller")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Please upload a PDF file")
    try:
        text = svc.extract_text(data)
    except Exception:
        raise HTTPException(400, "Could not read this PDF - is it password-protected or corrupted?")
    if len(text) < 100:
        raise HTTPException(400, "Too little text found - scanned-image PDFs are not supported")
    rep = svc.analyze(text, target_role or None)
    rep["ai"] = None
    if ai_tips and ai.configured():
        try:
            rep["ai"] = ai.resume_tips(text, rep["target_label"], rep["missing_skills"])
        except Exception as e:  # keep the core analysis even if the AI call fails
            rep["ai_error"] = getattr(e, "detail", str(e))[:200]
    r = Resume(user_id=user.id, filename=file.filename or "resume.pdf", text=text, target_role=rep["target_role"],
               predicted_role=rep["predicted_role"], ats_score=rep["ats_score"], skills=jdump(rep["skills"]),
               report=jdump(rep))
    db.add(r)
    db.commit()
    before = user.level
    st = progress.recompute(db, user)
    return {"id": r.id, "filename": r.filename, **rep, "level": st["level"], "leveled_up": st["level"] > before}


@router.get("/latest")
def latest(user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())).first()
    if not r:
        return None
    return {"id": r.id, "filename": r.filename, **jload(r.report, {})}
