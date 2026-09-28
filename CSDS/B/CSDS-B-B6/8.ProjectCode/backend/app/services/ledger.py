"""Hash-chained audit ledger: each entry stores the SHA-256 of its content plus the previous hash,
so editing or deleting any past entry breaks every hash after it."""
import hashlib
import json
import threading

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import LedgerEntry, utcnow

GENESIS = "0" * 64
_lock = threading.Lock()


def entry_hash(ts: str, actor: str, action: str, person_id: str | None, detail: str, prev_hash: str) -> str:
    payload = json.dumps({"ts": ts, "actor": actor, "action": action, "person_id": person_id,
                          "detail": detail, "prev_hash": prev_hash}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def append(db: Session, actor: str, action: str, person_id: str | None, detail: dict) -> LedgerEntry:
    with _lock:
        last = db.scalar(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(1))
        prev = last.hash if last else GENESIS
        ts = utcnow()
        det = json.dumps(detail, sort_keys=True)
        e = LedgerEntry(ts=ts, actor=actor, action=action, person_id=person_id, detail=det, prev_hash=prev,
                        hash=entry_hash(ts, actor, action, person_id, det, prev))
        db.add(e)
        db.commit()
        return e


def verify_entries(entries: list) -> dict:
    """Recompute the chain. Works on ORM rows or plain dicts."""
    get = (lambda e, k: e[k]) if entries and isinstance(entries[0], dict) else getattr
    prev = GENESIS
    for i, e in enumerate(entries):
        expected = entry_hash(get(e, "ts"), get(e, "actor"), get(e, "action"), get(e, "person_id"), get(e, "detail"), prev)
        if get(e, "prev_hash") != prev or get(e, "hash") != expected:
            return {"intact": False, "entries": len(entries), "broken_at": get(e, "id"), "position": i}
        prev = get(e, "hash")
    return {"intact": True, "entries": len(entries), "head": prev}


def verify(db: Session) -> dict:
    return verify_entries(list(db.scalars(select(LedgerEntry).order_by(LedgerEntry.id))))
