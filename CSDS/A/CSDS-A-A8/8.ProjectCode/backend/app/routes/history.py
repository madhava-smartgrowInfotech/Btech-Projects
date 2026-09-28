from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Analysis, User, get_db

router = APIRouter(prefix="/api/history", tags=["history"])


def save(db, user, kind, title, summary, report):
    a = Analysis(user_id=user.id, kind=kind, title=title, summary=summary, report=report)
    db.add(a)
    db.commit()
    return a.id


@router.get("")
def list_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Analysis).where(Analysis.user_id == user.id).order_by(Analysis.id.desc()).limit(50))
    return [{"id": a.id, "kind": a.kind, "title": a.title, "created_at": a.created_at.isoformat()} for a in rows]


@router.get("/{aid}")
def get_one(aid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = db.get(Analysis, aid)
    if not a or a.user_id != user.id:
        raise HTTPException(404, "Not found")
    return {"id": a.id, "kind": a.kind, "title": a.title, "summary": a.summary, "report": a.report,
            "created_at": a.created_at.isoformat()}
