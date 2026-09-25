"""Demo persona switcher backing the storefront's identity picker."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import PersonaOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/demo-personas", response_model=list[PersonaOut])
def demo_personas(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(User).where(User.is_demo_persona.is_(True)).order_by(User.segment, User.id)
        )
        .scalars()
        .all()
    )
    return [
        PersonaOut(
            id=u.id,
            name=u.name,
            segment=u.segment,
            avatar_seed=u.avatar_seed,
            blurb=u.blurb,
        )
        for u in rows
    ]
