import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Consultation
from app.schemas import ChatRequest
from app.routes.auth import require_user
from app.config import settings

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat")
def chat(payload: ChatRequest, user=Depends(require_user), db: Session = Depends(get_db)):
    q = (payload.query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Please describe your symptoms.")
    if len(q) > settings.MAX_QUERY_CHARS:
        raise HTTPException(status_code=400, detail=f"Input too long (max {settings.MAX_QUERY_CHARS} characters).")
    try:
        from app.rag.pipeline import get_pipeline
        pipe = get_pipeline()
        result = pipe.answer(q)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Medical knowledge base not ready: {e}")
    except Exception as e:
        print(f"[chat] pipeline error: {e}")
        raise HTTPException(status_code=500, detail="The assistant is temporarily unavailable. Please try again.")
    try:
        c = Consultation(
            user_id=user.id,
            symptom_query=q,
            generated_response=result["answer"],
            top_condition=result.get("top_condition", ""),
            retrieved_evidence=json.dumps(result.get("evidence", [])),
            retrieval_score=float(result.get("retrieval_score", 0.0)),
            safety_flag=result.get("safety_flag", "routine"),
        )
        db.add(c)
        db.commit()
        db.refresh(c)
    except Exception as e:
        db.rollback()
        print(f"[chat] db error: {e}")
        raise HTTPException(status_code=500, detail="Could not save consultation.")
    ev = [{"record_id": e["record_id"], "disease": e["disease"], "symptoms": e["symptoms"],
           "description": e["description"], "guidance": e["guidance"], "severity": e["severity"],
           "red_flags": e["red_flags"], "relevance": e["relevance"]} for e in result["evidence"]]
    return {
        "answer": result["answer"],
        "top_condition": result["top_condition"],
        "evidence": ev,
        "safety_flag": result["safety_flag"],
        "safety_message": result["safety_message"],
        "relevance_label": result["relevance_label"],
        "consultation_id": c.id,
        "created_at": c.created_at.isoformat() if c.created_at else "",
        "generated_by": result["generated_by"],
    }
