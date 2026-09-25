from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..db import get_db

router = APIRouter(prefix="/api/guardians", tags=["guardians"])


@router.get("", response_model=list[schemas.GuardianOut])
def list_guardians(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return db.query(models.Guardian).filter(models.Guardian.owner_id == current_user.id).all()


@router.post("", response_model=schemas.GuardianOut)
def create_guardian(
    body: schemas.GuardianIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    g = models.Guardian(owner_id=current_user.id, **body.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.put("/{guardian_id}", response_model=schemas.GuardianOut)
def update_guardian(
    guardian_id: int,
    body: schemas.GuardianIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    g = db.get(models.Guardian, guardian_id)
    if not g or g.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Guardian not found")
    for k, v in body.model_dump().items():
        setattr(g, k, v)
    db.commit()
    db.refresh(g)
    return g


@router.delete("/{guardian_id}")
def delete_guardian(
    guardian_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    g = db.get(models.Guardian, guardian_id)
    if not g or g.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Guardian not found")
    db.delete(g)
    db.commit()
    return {"ok": True}
