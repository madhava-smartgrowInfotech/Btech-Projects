"""Behaviour ingestion.

Every event is persisted and folded straight into the live agents, so the next
recommendation request for that shopper already reflects it.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Event, Product
from ..recommender.orchestrator import orchestrator
from ..schemas import EventIn, EventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut)
def track_event(payload: EventIn, db: Session = Depends(get_db)):
    if payload.product_id is not None and db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=404, detail=f"No product with id {payload.product_id}")

    now = datetime.utcnow()
    event = Event(
        session_id=payload.session_id,
        user_id=payload.user_id,
        product_id=payload.product_id,
        type=payload.type,
        query=payload.query,
        value=payload.value,
        rec_id=payload.rec_id,
        source_agent=payload.source_agent,
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    orchestrator.record_event(
        user_id=payload.user_id,
        session_id=payload.session_id,
        product_id=payload.product_id,
        etype=payload.type,
        value=payload.value,
        query=payload.query,
        created_at=now,
    )

    return EventOut(ok=True, event_id=event.id)
