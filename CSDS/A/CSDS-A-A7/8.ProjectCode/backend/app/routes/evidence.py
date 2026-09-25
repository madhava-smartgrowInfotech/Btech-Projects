from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from .. import auth, config, models
from ..db import get_db
from ..services.hashing import sha256_bytes

router = APIRouter(prefix="/api/sos", tags=["evidence"])

ALLOWED_KINDS = {"photo", "audio"}


@router.post("/{session_id}/evidence")
async def upload_evidence(
    session_id: int,
    kind: str = Form(...),
    lat: float | None = Form(None),
    lng: float | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=400, detail="kind must be photo or audio")

    session = db.get(models.EmergencySession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    digest = sha256_bytes(data)
    ext = (file.filename or "").split(".")[-1][:8] or ("jpg" if kind == "photo" else "webm")
    session_dir = config.EVIDENCE_DIR / str(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{digest[:16]}.{ext}"
    path = session_dir / filename
    path.write_bytes(data)

    ev = models.Evidence(
        session_id=session_id,
        kind=kind,
        file_path=str(path.relative_to(config.DATA_DIR)),
        sha256=digest,
        lat=lat,
        lng=lng,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return {
        "id": ev.id,
        "kind": ev.kind,
        "sha256": ev.sha256,
        "captured_at": ev.captured_at,
        "lat": ev.lat,
        "lng": ev.lng,
    }


@router.get("/{session_id}/evidence")
def list_evidence(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = db.get(models.EmergencySession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return [
        {
            "id": e.id,
            "kind": e.kind,
            "sha256": e.sha256,
            "captured_at": e.captured_at,
            "lat": e.lat,
            "lng": e.lng,
        }
        for e in session.evidence
    ]
