import re

from fastapi import APIRouter, Response
from sqlalchemy.orm import Session

from app.core.deps import DB, CurrentUser
from app.core.errors import AppError, NotFound
from app.models import Hall, Plan, User
from app.services import audit
from app.services.exports.data import load_plan_export
from app.services.exports.excel import attendance_xlsx, hall_lists_xlsx
from app.services.exports.invigilator_pdf import invigilator_pdf
from app.services.exports.seating_chart_pdf import seating_chart_pdf
from app.services.exports.slips_pdf import Slip, slips_pdf
from app.services.hallmap import can_view_hall

router = APIRouter(prefix="/plans/{plan_id}/exports", tags=["exports"])

PDF = "application/pdf"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _prepare(db: Session, plan_id: int, hall_id: int | None, user: User, what: str):
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise NotFound("Plan")
    if hall_id is not None:
        hall = db.get(Hall, hall_id)
        if hall is None or hall.id not in plan.hall_ids:
            raise NotFound("Hall in this plan")
        if not can_view_hall(db, plan, hall, user):
            raise AppError("You are not assigned to this hall.", 403)
    elif not user.is_admin:
        raise AppError("Only administrators can export every hall at once.", 403)
    export = load_plan_export(db, plan, hall_id)
    scope = export.halls[0].hall.code if hall_id is not None and export.halls else "all halls"
    audit.record(db, "plan.exported", f"{user.full_name} downloaded {what} ({scope}) for {plan.session.label} v{plan.version}",
                 actor=user, plan_id=plan.id, details={"what": what, "hall_id": hall_id})
    db.commit()
    return export


def _name(export, kind: str, ext: str) -> str:
    session = export.plan.session
    scope = export.halls[0].hall.code if len(export.halls) == 1 else "all-halls"
    raw = f"{kind}_{session.date:%Y-%m-%d}_{session.start_time:%H%M}_v{export.plan.version}_{scope}.{ext}"
    return re.sub(r"[^A-Za-z0-9_.-]", "-", raw)


def _file(data: bytes, media: str, name: str) -> Response:
    return Response(data, media_type=media, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/seating-charts.pdf", summary="Seating charts, one page per hall")
def seating_charts(plan_id: int, db: DB, user: CurrentUser, hall_id: int | None = None) -> Response:
    export = _prepare(db, plan_id, hall_id, user, "seating charts")
    return _file(seating_chart_pdf(export), PDF, _name(export, "seating-chart", "pdf"))


@router.get("/invigilator-sheets.pdf", summary="Invigilator sheets with attendance and signature columns")
def invigilator_sheets(plan_id: int, db: DB, user: CurrentUser, hall_id: int | None = None) -> Response:
    export = _prepare(db, plan_id, hall_id, user, "invigilator sheets")
    return _file(invigilator_pdf(export), PDF, _name(export, "invigilator-sheets", "pdf"))


@router.get("/hall-lists.xlsx", summary="Hall-wise lists and a roll-order door list (Excel)")
def hall_lists(plan_id: int, db: DB, user: CurrentUser, hall_id: int | None = None) -> Response:
    export = _prepare(db, plan_id, hall_id, user, "hall lists")
    return _file(hall_lists_xlsx(export), XLSX, _name(export, "hall-lists", "xlsx"))


@router.get("/attendance.xlsx", summary="Attendance report (Excel)")
def attendance_report(plan_id: int, db: DB, user: CurrentUser, hall_id: int | None = None) -> Response:
    export = _prepare(db, plan_id, hall_id, user, "attendance report")
    return _file(attendance_xlsx(export), XLSX, _name(export, "attendance", "xlsx"))


@router.get("/qr-slips.pdf", summary="Seat slips with QR codes, six per page")
def qr_slips(plan_id: int, db: DB, user: CurrentUser, hall_id: int | None = None) -> Response:
    export = _prepare(db, plan_id, hall_id, user, "seat slips")
    session = export.plan.session
    slips = [
        Slip(roll_no=s.roll_no, full_name=s.full_name, course_code=s.course_code, course_name=s.course_name,
             when=f"{session.date:%a %d %b %Y} · {session.start_time:%H:%M}-{session.end_time:%H:%M}",
             hall_code=h.hall.code, hall_name=h.hall.name,
             where=", ".join(x for x in (h.hall.building, f"floor {h.hall.floor}" if h.hall.floor.isdigit() else h.hall.floor) if x),
             seat=s.label, accessible=s.needs_accessible, stamp=export.stamp)
        for h in export.halls for s in sorted(h.seats, key=lambda r: (r.row, r.col))
    ]
    return _file(slips_pdf(slips, f"Seat slips - {export.title}"), PDF, _name(export, "seat-slips", "pdf"))
