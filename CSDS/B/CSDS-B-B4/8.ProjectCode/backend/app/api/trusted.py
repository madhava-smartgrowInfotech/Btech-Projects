from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.models import TrustedContact, User, Wallet

router = APIRouter(prefix="/trusted-contacts", tags=["trusted contacts"])


class TrustedIn(BaseModel):
    identifier: str = Field(min_length=3, max_length=80, description="UPI ID or mobile number of the person")
    relation: str | None = Field(default=None, max_length=30)
    can_approve: bool = True


def _view(tc: TrustedContact, mine: bool) -> dict:
    person = tc.contact if mine else tc.owner
    return {
        "id": tc.id,
        "name": person.full_name,
        "upi_id": person.wallet.upi_id,
        "phone_last4": person.phone[-4:],
        "relation": tc.relation,
        "can_approve": tc.can_approve,
        "created_at": tc.created_at,
    }


@router.get("")
def list_contacts(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    mine = db.scalars(select(TrustedContact).where(TrustedContact.user_id == user.id).order_by(TrustedContact.created_at)).all()
    protecting = db.scalars(select(TrustedContact).where(TrustedContact.contact_user_id == user.id).order_by(TrustedContact.created_at)).all()
    return {"trusted": [_view(t, True) for t in mine], "protecting": [_view(t, False) for t in protecting]}


@router.post("", status_code=status.HTTP_201_CREATED)
def add_contact(body: TrustedIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    ident = body.identifier.strip().lower()
    person = db.scalar(select(User).join(Wallet).where(or_(Wallet.upi_id == ident, User.phone == ident)))
    if person is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "contact_not_found", "No UPI Guardian user has this UPI ID or mobile number.")
    if person.id == user.id:
        raise api_error(status.HTTP_400_BAD_REQUEST, "self_contact", "You cannot add yourself as a trusted contact.")
    if db.scalar(select(TrustedContact.id).where(TrustedContact.user_id == user.id, TrustedContact.contact_user_id == person.id)):
        raise api_error(status.HTTP_409_CONFLICT, "contact_exists", "This person is already your trusted contact.")
    tc = TrustedContact(user_id=user.id, contact_user_id=person.id, relation=body.relation, can_approve=body.can_approve)
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return _view(tc, True)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contact(contact_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    tc = db.get(TrustedContact, contact_id)
    if tc is None or tc.user_id != user.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "contact_not_found", "Trusted contact not found.")
    db.delete(tc)
    db.commit()
