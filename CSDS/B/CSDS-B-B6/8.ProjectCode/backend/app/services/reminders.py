"""Medication and follow-up reminders derived from the unified record and synced summaries."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import HOSPITALS
from ..db import Reminder


def _upsert(db: Session, person_id: str, kind: str, text: str, due: str, source_key: str, source: str) -> bool:
    if db.scalar(select(Reminder.id).where(Reminder.person_id == person_id, Reminder.source_key == source_key)):
        return False
    db.add(Reminder(person_id=person_id, kind=kind, text=text, due=due, source_key=source_key, source=source))
    return True


def from_resources(db: Session, person_id: str, resources: list[tuple[str, dict]]) -> int:
    added = 0
    today = date.today().isoformat()
    for hkey, r in resources:
        src = HOSPITALS[hkey]["name"]
        if r["resourceType"] == "MedicationRequest" and r.get("status") == "active":
            med = r.get("medicationCodeableConcept", {})
            name = med.get("text") or (med.get("coding") or [{}])[0].get("display", "Medication")
            dose = (r.get("dosageInstruction") or [{}])[0].get("text", "")
            added += _upsert(db, person_id, "medication", f"Take {name}" + (f" - {dose}" if dose else ""), today,
                             f"med:{hkey}:{r['id']}", src)
        elif r["resourceType"] == "CarePlan" and r.get("status") == "active":
            due = r.get("period", {}).get("start", today)[:10]
            added += _upsert(db, person_id, "follow-up", r.get("description") or "Follow-up visit", due,
                             f"plan:{hkey}:{r['id']}", src)
    db.commit()
    return added


def listing(db: Session, person_id: str) -> list[dict]:
    today = date.today().isoformat()
    out = []
    for r in db.scalars(select(Reminder).where(Reminder.person_id == person_id).order_by(Reminder.done, Reminder.due)):
        state = "done" if r.done else "overdue" if r.due < today else "due today" if r.due == today else "upcoming"
        out.append({"id": r.id, "kind": r.kind, "text": r.text, "due": r.due, "done": r.done, "state": state, "source": r.source})
    return out
