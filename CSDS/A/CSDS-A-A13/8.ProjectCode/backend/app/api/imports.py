from typing import Literal

from fastapi import APIRouter, File, Form, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.config import DATA_DIR
from app.core.deps import DB, AdminUser
from app.core.errors import AppError, NotFound
from app.models import ImportBatch, User
from app.schemas.data import ImportBatchOut
from app.services.importer.commit import commit_batch, create_batch
from app.services.importer.templates import template_csv, template_xlsx, workbook_xlsx

router = APIRouter(prefix="/imports", tags=["import"])

Kind = Literal["courses", "candidates", "halls", "timetable", "workbook"]
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _out(db, batch: ImportBatch, with_report: bool = True) -> ImportBatchOut:
    user = db.get(User, batch.created_by) if batch.created_by else None
    return ImportBatchOut(
        id=batch.id, kind=batch.kind, filename=batch.filename, status=batch.status, rows_total=batch.rows_total,
        rows_valid=batch.rows_valid, created_at=batch.created_at, committed_at=batch.committed_at,
        created_by=user.full_name if user else None, report=batch.report if with_report else None,
    )


@router.get("/templates/{kind}", summary="Download an empty import template")
def download_template(kind: Kind, _: AdminUser, format: Literal["xlsx", "csv"] = "xlsx") -> Response:
    if kind == "workbook":
        if format == "csv":
            raise AppError("The combined template is only available as .xlsx.")
        return Response(workbook_xlsx(None), media_type=XLSX,
                        headers={"Content-Disposition": 'attachment; filename="seatwise_import_template.xlsx"'})
    if format == "csv":
        return Response(template_csv(kind), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{kind}_template.csv"'})
    return Response(template_xlsx(kind), media_type=XLSX,
                    headers={"Content-Disposition": f'attachment; filename="{kind}_template.xlsx"'})


@router.get("/samples/{kind}", summary="Download the sample data (clearly labelled sample, fictional people)")
def download_sample(kind: Kind, _: AdminUser) -> FileResponse:
    name = "seatwise_sample_workbook.xlsx" if kind == "workbook" else f"{kind}.csv"
    path = DATA_DIR / "sample" / name
    if not path.exists():
        raise AppError("The sample files are missing. Run scripts\\generate_sample_data.py to create them.", 404)
    return FileResponse(path, filename=f"sample_{name}", media_type=XLSX if kind == "workbook" else "text/csv")


@router.post("/{kind}/validate", response_model=ImportBatchOut, summary="Upload a file and check it (nothing is saved yet)")
async def validate_upload(kind: Kind, db: DB, admin: AdminUser, file: UploadFile = File(...),
                          mode: Literal["update", "replace"] = Form("update")) -> ImportBatchOut:
    data = await file.read()
    batch = create_batch(db, kind, file.filename or f"{kind}.xlsx", data, mode, admin)
    return _out(db, batch)


@router.post("/{batch_id}/commit", response_model=ImportBatchOut, summary="Apply a checked upload")
def commit_upload(batch_id: int, db: DB, admin: AdminUser) -> ImportBatchOut:
    return _out(db, commit_batch(db, batch_id, admin))


@router.get("", response_model=list[ImportBatchOut], summary="Recent imports")
def list_imports(db: DB, _: AdminUser, limit: int = 20) -> list[ImportBatchOut]:
    batches = db.scalars(select(ImportBatch).order_by(ImportBatch.id.desc()).limit(min(limit, 100))).all()
    return [_out(db, b, with_report=False) for b in batches]


@router.get("/{batch_id}", response_model=ImportBatchOut, summary="One import with its validation report")
def get_import(batch_id: int, db: DB, _: AdminUser) -> ImportBatchOut:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise NotFound("Import")
    return _out(db, batch)
