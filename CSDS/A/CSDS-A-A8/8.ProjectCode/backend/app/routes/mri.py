from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import User, get_db
from ..services import mri, reports
from .history import save

router = APIRouter(prefix="/api/mri", tags=["mri"])


def _finish(res, user, db, title):
    compact = {k: v for k, v in res.items() if not k.endswith("_png")}
    res["report"] = reports.generate("mri", compact)
    res["analysis_id"] = save(db, user, "mri", title, compact, res["report"])
    return res


@router.get("/models")
def models(user: User = Depends(current_user)):
    return mri.available_models()


@router.get("/samples")
def samples(user: User = Depends(current_user)):
    return mri.list_samples()


@router.get("/samples/{name}")
def sample_image(name: str):
    try:
        path, _ = mri.sample_path(name)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return FileResponse(path, media_type="image/png")


@router.post("/segment")
async def segment(file: UploadFile = File(...), model: str = Form("jepa_10"), pixel_spacing_mm: float = Form(1.0),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    if model not in mri.MODEL_CHOICES:
        raise HTTPException(400, "Unknown model")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image is larger than 10 MB")
    try:
        res = mri.segment(data, model, pixel_spacing_mm)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))
    return _finish(res, user, db, f"MRI slice {file.filename}")


class SampleIn(BaseModel):
    name: str
    model: str = "jepa_10"
    pixel_spacing_mm: float = 1.0


@router.post("/segment-sample")
def segment_sample(body: SampleIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.model not in mri.MODEL_CHOICES:
        raise HTTPException(400, "Unknown model")
    try:
        res = mri.segment_sample(body.name, body.model, body.pixel_spacing_mm)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))
    return _finish(res, user, db, f"MRI sample {body.name}")
