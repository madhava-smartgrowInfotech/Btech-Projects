from __future__ import annotations

import csv
import io
import json

import h3
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db, utcnow
from ..core.security import get_current_user, has_role, require_role
from ..models import STATUSES, Complaint, ComplaintEvent, Device, Reading, User
from ..schemas.complaints import AssignIn, ComplaintDetail, ComplaintEventOut, ComplaintOut, ComplaintPage, NoteIn, ReportIn, TransitionIn
from ..services import complaint_service as cs
from ..services import opencellid
from ..services.evidence import build_evidence, summary_text
from ..services.suggest_service import nearby_operator

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _visible(db: Session, user: User, q):
    if has_role(user, "engineer"):
        return q
    mine_cells = (db.query(Reading.h3_cell).join(Device, Device.id == Reading.device_id)
                  .filter(Device.owner_id == user.id, Reading.source == "phone").distinct())
    return q.filter(or_(Complaint.reporter_user_id == user.id, Complaint.h3_cell.in_(mine_cells)))


def _out(c: Complaint, names: dict[int, str]) -> ComplaintOut:
    o = ComplaintOut.model_validate(c)
    o.assigned_to_name = names.get(c.assigned_to_id) if c.assigned_to_id else None
    o.reporter_name = names.get(c.reporter_user_id) if c.reporter_user_id else None
    ev = c.evidence or {}
    o.readings, o.bad_share = ev.get("readings", 0), ev.get("bad_share")
    return o


def _names(db: Session, ids) -> dict[int, str]:
    ids = {i for i in ids if i}
    return {u.id: u.name for u in db.query(User).filter(User.id.in_(ids)).all()} if ids else {}


def _get(db: Session, user: User, complaint_id: int) -> Complaint:
    c = _visible(db, user, db.query(Complaint).filter(Complaint.id == complaint_id)).first()
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return c


@router.get("", response_model=ComplaintPage, summary="Complaints (field users: their own; engineers: the whole queue)")
def list_complaints(status_: str | None = Query(None, alias="status", description="Comma list of statuses"),
                    operator: str | None = None, source: str | None = None, q: str | None = None, mine: bool = False,
                    assigned_to_me: bool = False, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ComplaintPage:
    base = _visible(db, user, db.query(Complaint))
    if mine:
        base = base.filter(Complaint.reporter_user_id == user.id)
    if operator:
        base = base.filter(Complaint.operator == operator)
    if source:
        base = base.filter(Complaint.source.in_(source.split(",")))
    if assigned_to_me:
        base = base.filter(Complaint.assigned_to_id == user.id)
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(or_(Complaint.ref_code.ilike(like), Complaint.h3_cell.ilike(like), Complaint.operator.ilike(like)))
    counts = {s: 0 for s in STATUSES}
    for s, n in base.with_entities(Complaint.status, func.count()).group_by(Complaint.status).all():
        counts[s] = n
    listed = base.filter(Complaint.status.in_(status_.split(","))) if status_ else base
    total = listed.count()
    rows = listed.order_by(Complaint.updated_at.desc()).offset(offset).limit(limit).all()
    names = _names(db, [c.assigned_to_id for c in rows] + [c.reporter_user_id for c in rows])
    return ComplaintPage(items=[_out(c, names) for c in rows], total=total, counts=counts)


@router.get("/{complaint_id}", response_model=ComplaintDetail)
def get_complaint(complaint_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ComplaintDetail:
    c = _get(db, user, complaint_id)
    names = _names(db, [c.assigned_to_id, c.reporter_user_id])
    d = ComplaintDetail(**_out(c, names).model_dump(), evidence=c.evidence or {}, suggestion=(c.evidence or {}).get("nearest_strong_spot"),
                        boundary=[[lat, lng] for lat, lng in h3.cell_to_boundary(c.h3_cell)])
    events = db.query(ComplaintEvent).filter(ComplaintEvent.complaint_id == c.id).order_by(ComplaintEvent.ts).all()
    d.events = [ComplaintEventOut.model_validate(e) for e in events]
    return d


@router.post("", response_model=ComplaintDetail, status_code=201, summary="Report a problem at a location (evidence attached automatically)")
def report(body: ReportIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ComplaintDetail:
    cell = h3.latlng_to_cell(body.lat, body.lon, settings.h3_resolution)
    operator = (body.operator or nearby_operator(db, body.lat, body.lon) or "Unknown").strip()
    existing = db.query(Complaint).filter(Complaint.h3_cell == cell, Complaint.operator == operator,
                                          Complaint.status.in_(("detected", "registered", "acknowledged", "in_progress", "resolved"))).first()
    if existing:
        cs.add_event(db, existing, "note", f"Also reported by a user: {body.note}", user)
        db.commit()
        return get_complaint(existing.id, user, db)
    readings = (db.query(Reading).filter(Reading.h3_cell == cell, Reading.operator == operator, Reading.zone_label.is_not(None))
                .order_by(Reading.ts.desc()).limit(500).all())
    ev = build_evidence(db, readings, cell, operator) if readings else {"readings": 0, "classes": {"Strong": 0, "Weak": 0, "Dead": 0},
                                                                         "zone": {"h3_cell": cell, "center": list(h3.cell_to_latlng(cell)), "operator": operator}}
    lat, lon = h3.cell_to_latlng(cell)
    c = Complaint(h3_cell=cell, operator=operator, lat=lat, lon=lon, status="detected", severity="weak", origin="user", source="phone",
                  reporter_user_id=user.id, evidence=ev, detected_at=utcnow(), ref_code=f"tmp-{cell}-{utcnow().timestamp()}")
    db.add(c)
    db.flush()
    c.ref_code = cs.next_ref(db, c)
    c.summary = (summary_text(ev, operator, c.ref_code) if readings else f"Complaint {c.ref_code}: user report for {operator} in zone {cell}.") + f" User note: {body.note}"
    cs.add_event(db, c, "status", f"Reported by {user.name}: {body.note}", user, None, "detected")
    cs.register(db, c, "Registered from a user report", user)
    return get_complaint(c.id, user, db)


@router.post("/{complaint_id}/transition", response_model=ComplaintDetail)
def transition(complaint_id: int, body: TransitionIn, user: User = Depends(require_role("engineer")), db: Session = Depends(get_db)) -> ComplaintDetail:
    c = _get(db, user, complaint_id)
    if body.to == "resolved" and c.assigned_to_id is None:
        c.assigned_to_id = user.id
    cs.transition(db, c, body.to, user, body.note)
    return get_complaint(c.id, user, db)


@router.post("/{complaint_id}/assign", response_model=ComplaintDetail)
def assign(complaint_id: int, body: AssignIn, user: User = Depends(require_role("engineer")), db: Session = Depends(get_db)) -> ComplaintDetail:
    c = _get(db, user, complaint_id)
    target = db.get(User, body.user_id) if body.user_id else None
    if body.user_id and (not target or not has_role(target, "engineer")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Complaints can only be assigned to engineers")
    c.assigned_to_id = target.id if target else None
    cs.add_event(db, c, "assign", f"Assigned to {target.name}" if target else "Unassigned", user)
    db.commit()
    cs.publish(c, "assigned")
    return get_complaint(c.id, user, db)


@router.post("/{complaint_id}/notes", response_model=ComplaintDetail)
def add_note(complaint_id: int, body: NoteIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ComplaintDetail:
    c = _get(db, user, complaint_id)
    cs.add_event(db, c, "note", body.note.strip(), user)
    c.updated_at = utcnow()
    db.commit()
    return get_complaint(c.id, user, db)


@router.get("/{complaint_id}/evidence.json", summary="Download the evidence bundle as JSON")
def evidence_json(complaint_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    c = _get(db, user, complaint_id)
    body = {"ref_code": c.ref_code, "status": c.status, "operator": c.operator, "zone": c.h3_cell, "summary": c.summary,
            "evidence": c.evidence, "exported_at": utcnow().isoformat() + "Z"}
    return Response(json.dumps(body, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{c.ref_code}-evidence.json"'})


@router.get("/{complaint_id}/evidence.csv", summary="Download the readings behind the complaint as CSV")
def evidence_csv(complaint_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StreamingResponse:
    c = _get(db, user, complaint_id)
    q = (db.query(Reading).filter(Reading.h3_cell == c.h3_cell, Reading.operator == c.operator, Reading.zone_label.is_not(None))
         .order_by(Reading.ts))
    cols = ["ts", "source", "lat", "lon", "accuracy_m", "zone_label", "zone_confidence", "label_method", "rsrp", "rsrq", "sinr", "rssi",
            "cell_id", "latency_ms", "jitter_ms", "packet_loss", "dl_mbps", "ul_mbps", "wifi_rssi", "connected"]

    def rows():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(cols)
        yield buf.getvalue()
        for r in q.yield_per(1000):
            buf.seek(0)
            buf.truncate()
            w.writerow([getattr(r, k).isoformat() + "Z" if k == "ts" else getattr(r, k) for k in cols])
            yield buf.getvalue()

    return StreamingResponse(rows(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{c.ref_code}-readings.csv"'})


@router.get("/{complaint_id}/towers", summary="Known cell towers near the complaint (OpenCelliD, when a key is configured)")
def towers(complaint_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    c = _get(db, user, complaint_id)
    if not opencellid.enabled():
        return {"enabled": False, "towers": []}
    radio = (c.evidence or {}).get("radio") or {}
    try:
        found = opencellid.towers_near(db, c.lat, c.lon, serving=set(radio.get("cell_ids") or []))
    except opencellid.OpenCellIdError as exc:
        return {"enabled": True, "towers": [], "error": str(exc)}
    return {"enabled": True, "towers": found[:15]}


@router.get("/meta/engineers", summary="Engineers a complaint can be assigned to")
def engineers(user: User = Depends(require_role("engineer")), db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": u.id, "name": u.name} for u in db.query(User).filter(User.role.in_(("engineer", "admin")), User.is_active.is_(True)).order_by(User.name).all()]
