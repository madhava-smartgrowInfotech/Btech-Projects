from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Query as SAQuery
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import get_current_user, has_role
from ..models import Device, Reading, User
from ..schemas.readings import ReadingOut

router = APIRouter(prefix="/api/readings", tags=["readings"])

EXPORT_COLUMNS = ["id", "ts", "source", "device_id", "lat", "lon", "accuracy_m", "h3_cell", "operator", "link", "network_type",
                  "connected", "in_service", "rsrp", "rsrq", "sinr", "rssi", "cqi", "latency_ms", "jitter_ms", "packet_loss",
                  "dl_mbps", "ul_mbps", "wifi_rssi", "ble_rssi", "zone_label", "zone_confidence", "label_method",
                  "radio_estimate", "radio_estimate_conf", "model_version"]


def filtered(db: Session, user: User, device_id: int | None, source: str | None, operator: str | None, label: str | None,
             since: datetime | None, until: datetime | None, mine: bool) -> SAQuery:
    q = db.query(Reading)
    if mine or not has_role(user, "engineer"):
        own = db.query(Device.id).filter(Device.owner_id == user.id)
        q = q.filter(Reading.device_id.in_(own)) if mine else q.filter((Reading.device_id.in_(own)) | (Reading.source != "phone"))
    if device_id:
        q = q.filter(Reading.device_id == device_id)
    if source:
        q = q.filter(Reading.source.in_(source.split(",")))
    if operator:
        q = q.filter(Reading.operator == operator)
    if label:
        q = q.filter(Reading.zone_label.in_(label.split(",")))
    if since:
        q = q.filter(Reading.ts >= since.replace(tzinfo=None))
    if until:
        q = q.filter(Reading.ts <= until.replace(tzinfo=None))
    return q


@router.get("", response_model=list[ReadingOut], summary="Readings, newest first (field users see their own phone readings)")
def list_readings(device_id: int | None = None, source: str | None = None, operator: str | None = None, label: str | None = None,
                  since: datetime | None = None, until: datetime | None = None, mine: bool = False,
                  limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Reading]:
    q = filtered(db, user, device_id, source, operator, label, since, until, mine)
    return q.order_by(Reading.ts.desc()).offset(offset).limit(limit).all()


@router.get("/export.csv", summary="Download readings as CSV (same filters as the list)")
def export_csv(device_id: int | None = None, source: str | None = None, operator: str | None = None, label: str | None = None,
               since: datetime | None = None, until: datetime | None = None, mine: bool = False,
               user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StreamingResponse:
    q = filtered(db, user, device_id, source, operator, label, since, until, mine).order_by(Reading.ts.asc())

    def rows():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(EXPORT_COLUMNS)
        yield buf.getvalue()
        for r in q.yield_per(2000):
            buf.seek(0)
            buf.truncate()
            writer.writerow([getattr(r, c).isoformat() + "Z" if c == "ts" else getattr(r, c) for c in EXPORT_COLUMNS])
            yield buf.getvalue()

    return StreamingResponse(rows(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="signalscout-readings.csv"'})
