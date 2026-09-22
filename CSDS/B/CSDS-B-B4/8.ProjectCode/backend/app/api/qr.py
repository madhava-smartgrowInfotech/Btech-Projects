from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.wallet import _qr_png
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.guard import qr_guard

router = APIRouter(prefix="/qr", tags=["qr"])


class ParseIn(BaseModel):
    payload: str = Field(min_length=1, max_length=1000)


@router.post("/parse")
def parse(body: ParseIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Checks a scanned QR code (F9 guard) before the payment screen is shown."""
    result = qr_guard(db, body.payload)
    result["is_self"] = result.get("payee_upi_id") == user.wallet.upi_id
    return result


@router.get("/image")
def image(payload: str = Query(..., min_length=1, max_length=1000)):
    """Renders any UPI payload as a QR image (used for the sample QR codes)."""
    return _qr_png(payload)
