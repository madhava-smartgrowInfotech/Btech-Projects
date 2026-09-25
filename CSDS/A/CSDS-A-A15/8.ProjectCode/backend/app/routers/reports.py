from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import User
from app.routers.inspections import _get_owned
from app.services.report_pdf import generate_inspection_pdf

router = APIRouter(prefix="/api/inspections", tags=["reports"])


@router.get("/{inspection_id}/report")
def download_report(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inspection = _get_owned(db, inspection_id, current_user)
    output_path = settings.reports_dir / f"inspection_{inspection.id}.pdf"
    generate_inspection_pdf(inspection, output_path)
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"VisionForge_Inspection_{inspection.id}.pdf",
    )
