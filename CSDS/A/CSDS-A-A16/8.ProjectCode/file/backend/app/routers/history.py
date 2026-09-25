from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Analysis, User
from app.schemas import AnalysisResponse, HistoryListResponse
from app.routers.analyze import analysis_to_response

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
def list_history(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Analysis).filter(Analysis.user_id == user.id).order_by(Analysis.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return HistoryListResponse(items=[analysis_to_response(a) for a in items], total=total)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_history_item(analysis_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Not found")
    return analysis_to_response(item)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(analysis_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return None
