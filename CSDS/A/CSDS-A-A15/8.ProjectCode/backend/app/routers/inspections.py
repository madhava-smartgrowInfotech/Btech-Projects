import base64
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.ml.inference import get_inspector
from app.models import Inspection, User
from app.schemas import InspectionOut
from app.services.root_cause import build_root_cause_report

router = APIRouter(prefix="/api/inspections", tags=["inspections"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


def _to_out(inspection: Inspection) -> InspectionOut:
    return InspectionOut(
        id=inspection.id,
        asset_name=inspection.asset_name,
        original_filename=inspection.original_filename,
        image_url=f"/api/inspections/{inspection.id}/image",
        heatmap_url=f"/api/inspections/{inspection.id}/heatmap",
        defect_type=inspection.defect_type,
        display_name=inspection.display_name,
        confidence=inspection.confidence,
        severity=inspection.severity,
        class_probabilities=json.loads(inspection.class_probabilities),
        description=inspection.description,
        root_cause_text=inspection.root_cause_text,
        corrective_actions=json.loads(inspection.corrective_actions),
        created_at=inspection.created_at,
    )


@router.post("", response_model=InspectionOut)
async def create_inspection(
    file: UploadFile,
    asset_name: str = "Unnamed Asset",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image format. Use JPG, PNG, WEBP or BMP.")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    inspector = get_inspector()
    result = inspector.predict(image_bytes)

    uid = uuid.uuid4().hex[:12]
    ext = Path(file.filename or "upload.jpg").suffix or ".jpg"
    original_name = f"{uid}{ext}"
    heatmap_name = f"{uid}_heatmap.png"

    (settings.uploads_dir / original_name).write_bytes(image_bytes)
    (settings.heatmaps_dir / heatmap_name).write_bytes(base64.b64decode(result["heatmap_png_b64"]))

    rc = build_root_cause_report(result["defect_type"], result["confidence"], result["severity"])

    inspection = Inspection(
        user_id=current_user.id,
        asset_name=asset_name or "Unnamed Asset",
        original_filename=file.filename or original_name,
        image_path=str(settings.uploads_dir / original_name),
        heatmap_path=str(settings.heatmaps_dir / heatmap_name),
        defect_type=result["defect_type"],
        display_name=result["display_name"],
        confidence=result["confidence"],
        severity=result["severity"],
        class_probabilities=json.dumps(result["class_probabilities"]),
        description=result["description"],
        root_cause_text=rc["root_cause_text"],
        corrective_actions=json.dumps(rc["corrective_actions"]),
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    return _to_out(inspection)


@router.get("", response_model=list[InspectionOut])
def list_inspections(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Inspection)
        .filter(Inspection.user_id == current_user.id)
        .order_by(Inspection.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_to_out(r) for r in rows]


@router.get("/{inspection_id}", response_model=InspectionOut)
def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = _get_owned(db, inspection_id, current_user)
    return _to_out(inspection)


def _get_owned(db: Session, inspection_id: int, current_user: User) -> Inspection:
    inspection = db.get(Inspection, inspection_id)
    if not inspection or inspection.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.get("/{inspection_id}/image")
def get_original_image(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = _get_owned(db, inspection_id, current_user)
    return FileResponse(inspection.image_path)


@router.get("/{inspection_id}/heatmap")
def get_heatmap_image(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = _get_owned(db, inspection_id, current_user)
    return FileResponse(inspection.heatmap_path)
