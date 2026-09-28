"""Live queue ordering, position and waiting-time estimates, plus WebSocket fan-out."""
import asyncio
from datetime import datetime, timedelta

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Booking, Hospital


def today_str() -> str:
    return datetime.now().date().isoformat()


def ordered_waiting(db: Session, hospital_id: int, day: str) -> list[Booking]:
    rows = db.scalars(select(Booking).where(Booking.hospital_id == hospital_id, Booking.date == day,
                                            Booking.status == "waiting")).all()
    return sorted(rows, key=lambda b: (b.priority, b.token))


def current_called(db: Session, hospital_id: int, day: str) -> list[Booking]:
    return list(db.scalars(select(Booking).where(Booking.hospital_id == hospital_id, Booking.date == day,
                                                 Booking.status == "called").order_by(Booking.called_at)).all())


def consult_minutes(db: Session, h: Hospital, day: str) -> float:
    """Rolling mean of today's actual consultation times, falling back to the hospital setting."""
    done = db.scalars(select(Booking).where(Booking.hospital_id == h.id, Booking.date == day,
                                            Booking.status == "done", Booking.called_at.is_not(None),
                                            Booking.completed_at.is_not(None))
                      .order_by(Booking.completed_at.desc()).limit(10)).all()
    mins = [(b.completed_at - b.called_at).total_seconds() / 60 for b in done]
    mins = [m for m in mins if 0.3 <= m <= 30]
    if len(mins) >= 3:
        return round(0.5 * (sum(mins) / len(mins)) + 0.5 * h.avg_consult_min, 2)
    return h.avg_consult_min


def token_label(b: Booking) -> str:
    return f"E{b.token}" if b.kind == "emergency" else str(b.token)


def booking_status(db: Session, b: Booking) -> dict:
    h = db.get(Hospital, b.hospital_id)
    base = {"booking_id": b.id, "status": b.status, "token": token_label(b), "date": b.date,
            "hospital_id": h.id, "hospital": h.name, "severity": b.severity}
    if b.status != "waiting":
        return {**base, "position": 0 if b.status == "called" else None, "wait_min": 0 if b.status == "called" else None}
    queue = ordered_waiting(db, b.hospital_id, b.date)
    pos = next(i for i, q in enumerate(queue) if q.id == b.id)
    m = consult_minutes(db, h, b.date)
    wait = sum((1 - q.noshow_prob) * m for q in queue[:pos])
    now = datetime.now()
    hh, mm = map(int, h.op_start.split(":"))
    opening = datetime.fromisoformat(b.date).replace(hour=hh, minute=mm)
    start = max(now, opening)
    return {**base, "position": pos + 1, "ahead": pos, "wait_min": round(wait),
            "consult_min": m, "eta": (start + timedelta(minutes=wait)).strftime("%Y-%m-%d %H:%M")}


class QueueHub:
    """Tracks WebSocket listeners per hospital and pushes a 'changed' event after any queue update."""

    def __init__(self):
        self.clients: dict[int, set[WebSocket]] = {}

    async def connect(self, hospital_id: int, ws: WebSocket):
        await ws.accept()
        self.clients.setdefault(hospital_id, set()).add(ws)

    def disconnect(self, hospital_id: int, ws: WebSocket):
        self.clients.get(hospital_id, set()).discard(ws)

    async def notify(self, hospital_id: int, event: str = "queue_changed"):
        dead = []
        for ws in list(self.clients.get(hospital_id, set())):
            try:
                await ws.send_json({"type": event, "hospital_id": hospital_id, "at": datetime.now().isoformat()})
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(hospital_id, ws)
        # the district dashboard listens on hospital id 0
        if hospital_id != 0:
            await asyncio.gather(*(self._send(ws, hospital_id, event) for ws in list(self.clients.get(0, set()))))

    async def _send(self, ws, hospital_id, event):
        try:
            await ws.send_json({"type": event, "hospital_id": hospital_id})
        except Exception:
            self.disconnect(0, ws)


hub = QueueHub()
