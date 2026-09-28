import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import Scan, Target, User, get_db
from ..schemas import ImportSpec, ManualTarget
from ..services.scope import is_in_scope
from ..services.spec_parser import parse_spec

router = APIRouter(prefix="/api/targets", tags=["targets"])


def _serialize(db: Session, t: Target) -> dict:
    endpoints = json.loads(t.endpoints_json or "[]")
    last = (db.query(Scan).filter(Scan.target_id == t.id)
            .order_by(Scan.id.desc()).first())
    return {
        "id": t.id, "name": t.name, "base_url": t.base_url,
        "endpoint_count": len(endpoints), "endpoints": endpoints,
        "auth": json.loads(t.auth_json or "{}"),
        "known_vulns": json.loads(t.known_vulns_json or "[]"),
        "in_scope": is_in_scope(t.base_url),
        "last_scan": None if not last else {
            "id": last.id, "status": last.status, "score": last.score,
            "grade": last.grade},
    }


@router.get("")
def list_targets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Target).filter(Target.owner_id == user.id).order_by(Target.id).all()
    return [_serialize(db, t) for t in rows]


@router.post("")
def create_target(body: ManualTarget, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    t = Target(
        owner_id=user.id, name=body.name, base_url=body.base_url.rstrip("/"),
        endpoints_json=json.dumps(body.endpoints),
        auth_json=json.dumps(body.auth),
        known_vulns_json=json.dumps(body.known_vulns),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _serialize(db, t)


@router.post("/import-spec")
def import_spec(body: ImportSpec, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    try:
        base_url, endpoints, kind = parse_spec(body.spec_text)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    base_url = (body.base_url or base_url or "").rstrip("/")
    if not base_url:
        raise HTTPException(400, "Could not determine a base URL. Provide base_url.")
    if not endpoints:
        raise HTTPException(400, "No endpoints found in the spec.")
    t = Target(
        owner_id=user.id, name=body.name, base_url=base_url,
        endpoints_json=json.dumps(endpoints),
        auth_json=json.dumps(body.auth),
        known_vulns_json=json.dumps(body.known_vulns),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {**_serialize(db, t), "spec_kind": kind}


@router.get("/{target_id}")
def get_target(target_id: int, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    t = db.get(Target, target_id)
    if not t or t.owner_id != user.id:
        raise HTTPException(404, "Target not found")
    return _serialize(db, t)


@router.delete("/{target_id}")
def delete_target(target_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    t = db.get(Target, target_id)
    if not t or t.owner_id != user.id:
        raise HTTPException(404, "Target not found")
    db.delete(t)
    db.commit()
    return {"deleted": target_id}
