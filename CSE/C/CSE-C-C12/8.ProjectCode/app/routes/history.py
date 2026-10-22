import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Consultation
from app.routes.auth import require_user

router = APIRouter(prefix="/api/history", tags=["history"])

def _ser(c: Consultation):
    try:
        ev = json.loads(c.retrieved_evidence or "[]")
    except Exception:
        ev = []
    return {
        "id": c.id,
        "symptom_query": c.symptom_query,
        "generated_response": c.generated_response,
        "top_condition": c.top_condition,
        "retrieved_evidence": ev,
        "retrieval_score": c.retrieval_score,
        "safety_flag": c.safety_flag,
        "created_at": c.created_at.isoformat() if c.created_at else "",
    }

@router.get("")
def list_history(search: str = Query(default=""), user=Depends(require_user), db: Session = Depends(get_db)):
    q = db.query(Consultation).filter(Consultation.user_id == user.id).order_by(Consultation.id.desc())
    items = q.limit(200).all()
    if search:
        s = search.lower()
        items = [c for c in items if s in (c.symptom_query or "").lower() or s in (c.top_condition or "").lower()]
    return [_ser(c) for c in items]

@router.get("/{cid}")
def get_one(cid: int, user=Depends(require_user), db: Session = Depends(get_db)):
    c = db.query(Consultation).filter(Consultation.id == cid, Consultation.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found.")
    return _ser(c)

@router.delete("/{cid}")
def delete_one(cid: int, user=Depends(require_user), db: Session = Depends(get_db)):
    c = db.query(Consultation).filter(Consultation.id == cid, Consultation.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found.")
    db.delete(c)
    db.commit()
    return {"ok": True}
