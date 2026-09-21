"""Public seat lookup and seat slips (no sign-in; published plans only)."""
import io
from datetime import date

import qrcode
from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DB
from app.core.errors import AppError
from app.models import Candidate, Hall, Plan, SeatAssignment
from app.models.plan import PLAN_PUBLISHED
from app.services.exports.slips_pdf import Slip, lookup_url, slips_pdf
from app.services.ratelimit import RateLimiter, client_key

router = APIRouter(prefix="/public", tags=["public lookup"])
_limiter = RateLimiter(get_settings().lookup_rate_limit_per_minute)
NOT_FOUND = "We could not find a published seat for this candidate ID. Check the ID, or look again closer to the exam."


def _short_name(full_name: str) -> str:
    parts = full_name.split()
    return parts[0] if len(parts) == 1 else f"{parts[0]} {parts[-1][0]}."


def _where(hall: Hall) -> str:
    floor = f"floor {hall.floor}" if hall.floor.isdigit() else (f"{hall.floor.lower()} floor" if hall.floor else "")
    return ", ".join(x for x in (hall.building, floor) if x)


def _seats(db, roll_no: str) -> tuple[Candidate, list[tuple[SeatAssignment, Plan, Hall]]]:
    candidate = db.scalar(select(Candidate).where(Candidate.roll_no == roll_no.strip().upper()))
    if candidate is None:
        raise AppError(NOT_FOUND, 404)
    rows = db.execute(select(SeatAssignment, Plan, Hall)
                      .join(Plan, Plan.id == SeatAssignment.plan_id)
                      .join(Hall, Hall.id == SeatAssignment.hall_id)
                      .where(SeatAssignment.candidate_id == candidate.id, Plan.status == PLAN_PUBLISHED)).all()
    if not rows:
        raise AppError(NOT_FOUND, 404)
    return candidate, sorted(rows, key=lambda r: (r[1].session.date, r[1].session.start_time))


@router.get("/lookup/{roll_no}", summary="Where do I sit? (published plans only)")
def lookup(roll_no: str, request: Request, db: DB) -> dict:
    _limiter.check(client_key(request))
    candidate, rows = _seats(db, roll_no)
    today = date.today()
    seats = []
    for seat, plan, hall in rows:
        s = plan.session
        seats.append({
            "plan_id": plan.id,
            "session": {"label": s.label, "date": s.date.isoformat(), "start_time": s.start_time.strftime("%H:%M"),
                        "end_time": s.end_time.strftime("%H:%M")},
            "status": "today" if s.date == today else ("upcoming" if s.date > today else "completed"),
            "course": {"code": seat.course.code, "name": seat.course.name},
            "hall": {"code": hall.code, "name": hall.name, "where": _where(hall), "rows": hall.rows, "cols": hall.cols,
                     "blocked": hall.blocked_seats or [], "accessible": hall.accessible_seats or [],
                     "aisles": hall.aisles_after_cols or []},
            "seat": {"label": seat.seat_label, "row": seat.row, "col": seat.col,
                     "accessible": seat.seat_label in (hall.accessible_seats or [])},
        })
    return {"candidate": {"roll_no": candidate.roll_no, "name": _short_name(candidate.full_name)}, "seats": seats}


@router.get("/slip/{roll_no}/{plan_id}.pdf", summary="Seat slip with QR code (PDF)")
def slip(roll_no: str, plan_id: int, request: Request, db: DB) -> Response:
    _limiter.check(client_key(request))
    candidate, rows = _seats(db, roll_no)
    match = next(((seat, plan, hall) for seat, plan, hall in rows if plan.id == plan_id), None)
    if match is None:
        raise AppError(NOT_FOUND, 404)
    seat, plan, hall = match
    s = plan.session
    data = slips_pdf([Slip(
        roll_no=candidate.roll_no, full_name=candidate.full_name, course_code=seat.course.code,
        course_name=seat.course.name, when=f"{s.date:%a %d %b %Y} · {s.start_time:%H:%M}-{s.end_time:%H:%M}",
        hall_code=hall.code, hall_name=hall.name, where=_where(hall), seat=seat.seat_label,
        accessible=candidate.needs_accessible_seat, stamp=f"Plan v{plan.version} · {s.label}",
    )], f"Seat slip - {candidate.roll_no}", single=True)
    name = f"seat-slip_{candidate.roll_no}_{s.date:%Y-%m-%d}_{s.start_time:%H%M}.pdf"
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/qr/{roll_no}.png", summary="QR code that opens this candidate's lookup page")
def qr_png(roll_no: str, request: Request, db: DB) -> Response:
    _limiter.check(client_key(request))
    candidate, _ = _seats(db, roll_no)
    image = qrcode.make(lookup_url(candidate.roll_no), box_size=8, border=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return Response(buffer.getvalue(), media_type="image/png", headers={"Cache-Control": "no-store"})
