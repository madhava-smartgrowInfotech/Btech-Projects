import cv2
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.config import MEDIA_DIR
from app.db import get_db
from app.deps import get_current_user_optional
from app.ml.inference import analyze_image_bytes
from app.models import Analysis, User
from app.schemas import AnalysisResponse

router = APIRouter(prefix="/api", tags=["analyze"])


def analysis_to_response(a: Analysis) -> AnalysisResponse:
    thumb_url = f"/api/media/thumbs/{a.id}.jpg" if a.thumbnail_path else None
    return AnalysisResponse(
        id=a.id,
        created_at=a.created_at,
        face_detected=a.face_detected,
        basic_emotions=a.basic_emotions or [],
        compound_emotions=a.compound_emotions or [],
        dominant=a.dominant,
        thumbnail_url=thumb_url,
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    image: UploadFile = File(...),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    image_bytes = await image.read()
    face_detected, basic, compound, dominant, face_gray = analyze_image_bytes(image_bytes)

    if user is None:
        from datetime import datetime, timezone

        return AnalysisResponse(
            id=None,
            created_at=datetime.now(timezone.utc),
            face_detected=face_detected,
            basic_emotions=basic,
            compound_emotions=compound,
            dominant=dominant,
            thumbnail_url=None,
        )

    record = Analysis(
        user_id=user.id,
        face_detected=face_detected,
        basic_emotions=basic,
        compound_emotions=compound,
        dominant=dominant,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if face_detected and face_gray is not None:
        thumb_path = MEDIA_DIR / f"{record.id}.jpg"
        cv2.imwrite(str(thumb_path), face_gray)
        record.thumbnail_path = str(thumb_path)
        db.commit()
        db.refresh(record)

    return analysis_to_response(record)
