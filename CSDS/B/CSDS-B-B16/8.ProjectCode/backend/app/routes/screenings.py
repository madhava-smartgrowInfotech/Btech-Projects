import base64

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import UPLOAD_DIR
from ..db import Patient, Screening, User, get_db
from ..services import heart, retina, staging
from ..services.preprocess import decode_image, preprocess
from ..services.report import build_report
from ..services.wavelet import band_images

router = APIRouter(prefix="/api/screenings", tags=["screenings"])

MAX_UPLOAD = 15 * 1024 * 1024
STEP_IMAGES = ["original", "green", "clahe", "resized"]
WAVELET_IMAGES = [f"{lvl}_{b}" for lvl in ("1", "2") for b in ("LL", "LH", "HL", "HH")]


def _dir(sid: int):
    return UPLOAD_DIR / str(sid)


def _b64(path) -> str | None:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode() if path.exists() else None


def screening_summary(s: Screening) -> dict:
    return {
        "id": s.id, "patient_id": s.patient_id, "patient_name": s.patient.name, "patient_code": s.patient.code,
        "eye": s.eye, "created_at": s.created_at.isoformat() + "Z", "retina_prob": s.retina_prob,
        "heart_prob": s.heart_prob, "stage": s.stage["stage"] if s.stage else None,
        "quality_passed": (s.quality or {}).get("passed"), "screened_by": s.user.name,
    }


def screening_full(s: Screening) -> dict:
    d = _dir(s.id)
    return {
        **screening_summary(s),
        "patient": {"id": s.patient.id, "code": s.patient.code, "name": s.patient.name, "age": s.patient.age,
                    "sex": s.patient.sex},
        "image_name": s.image_name,
        "quality": s.quality,
        "retina": s.retina_findings,
        "clinical": s.clinical,
        "heart": {"probability": s.heart_prob, "factors": s.heart_factors} if s.heart_prob is not None else None,
        "stage_detail": s.stage,
        "images": {
            "steps": {n: _b64(d / f"{n}.png") for n in STEP_IMAGES},
            "wavelet": {n: _b64(d / f"{n}.png") for n in WAVELET_IMAGES},
            "heatmap": _b64(d / "heatmap.png"),
            "vessels": _b64(d / "vessels.png"),
        },
    }


def _get(db: Session, sid: int) -> Screening:
    s = db.get(Screening, sid)
    if not s:
        raise HTTPException(404, "Screening not found")
    return s


def _analyse_image(data: bytes) -> tuple[dict, dict, dict]:
    img = decode_image(data)
    pre = preprocess(img)
    res = retina.analyse(pre)
    images = {n: pre[n] for n in STEP_IMAGES}
    images.update(band_images(pre["input"]))
    images.update(res.pop("images"))
    return pre["quality"], res, images


@router.post("/image")
async def upload_image(patient_id: int = Form(...), eye: str = Form("Right"), file: UploadFile = File(...),
                       db: Session = Depends(get_db), user: User = Depends(current_user)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Image is larger than 15 MB")
    try:
        quality, res, images = await run_in_threadpool(_analyse_image, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    s = Screening(patient_id=patient.id, user_id=user.id, eye=eye if eye in ("Left", "Right") else "",
                  image_name=file.filename or "", quality=quality, retina_prob=res["probability"], retina_findings=res)
    db.add(s)
    db.commit()
    d = _dir(s.id)
    d.mkdir(parents=True, exist_ok=True)
    for name, arr in images.items():
        cv2.imwrite(str(d / f"{name}.png"), arr)
    db.refresh(s)
    return screening_full(s)


@router.post("/{sid}/clinical")
def add_clinical(sid: int, body: dict, db: Session = Depends(get_db), _: User = Depends(current_user)):
    s = _get(db, sid)
    try:
        h = heart.predict(body)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    rf = s.retina_findings or {}
    s.clinical = h["inputs"]
    s.heart_prob = h["probability"]
    s.heart_factors = h["factors"]
    s.stage = staging.combine(s.retina_prob or 0.0, h["probability"], rf.get("threshold", 0.5), h["inputs"]["trestbps"])
    db.commit()
    db.refresh(s)
    return screening_full(s)


@router.get("")
def list_screenings(limit: int = 50, db: Session = Depends(get_db), _: User = Depends(current_user)):
    rows = db.query(Screening).order_by(Screening.id.desc()).limit(min(limit, 500)).all()
    return [screening_summary(s) for s in rows]


@router.get("/{sid}")
def get_screening(sid: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return screening_full(_get(db, sid))


@router.get("/{sid}/report")
def report(sid: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    s = _get(db, sid)
    pdf = build_report(s, _dir(s.id))
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="retinaguard_report_{s.id}.pdf"'})

