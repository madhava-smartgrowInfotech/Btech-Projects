from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import KeyPair, User, get_db, log_op
from ..services import crypto

router = APIRouter(prefix="/api/keys", tags=["keys"])


def key_dict(k: KeyPair) -> dict:
    return {"id": k.id, "name": k.name, "bits": k.bits, "fingerprint": k.fingerprint,
            "has_private": k.private_pem is not None, "public_pem": k.public_pem,
            "created_at": k.created_at.isoformat()}


def get_key(db: Session, user: User, key_id: int) -> KeyPair:
    k = db.get(KeyPair, key_id)
    if not k or k.user_id != user.id:
        raise HTTPException(404, "Key not found")
    return k


@router.get("")
def list_keys(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(KeyPair).where(KeyPair.user_id == user.id).order_by(KeyPair.id.desc())).all()
    return [key_dict(k) for k in rows]


class GenBody(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    bits: int = 3072


@router.post("/generate")
def generate(body: GenBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        priv, pub = crypto.generate_keypair(body.bits)
    except crypto.CryptoError as exc:
        raise HTTPException(400, str(exc))
    k = KeyPair(user_id=user.id, name=body.name, bits=body.bits, fingerprint=crypto.fingerprint(pub),
                public_pem=pub, private_pem=priv)
    db.add(k)
    db.commit()
    log_op(db, user.id, "key_generate", True, {"key_id": k.id, "bits": k.bits, "fingerprint": k.fingerprint})
    return key_dict(k)


class ImportBody(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    pem: str = Field(min_length=20, max_length=20000)


@router.post("/import")
def import_key(body: ImportBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Accepts an unencrypted RSA private key (becomes a full keypair) or a public key (recipient only)."""
    pem = body.pem.strip()
    try:
        if "PRIVATE KEY" in pem:
            priv, pub = pem, crypto.public_from_private(pem)
            bits = crypto.key_bits(pem, private=True)
        else:
            priv, pub = None, pem
            bits = crypto.key_bits(pem)
        fp = crypto.fingerprint(pub)
    except crypto.CryptoError as exc:
        raise HTTPException(400, str(exc))
    k = KeyPair(user_id=user.id, name=body.name, bits=bits, fingerprint=fp, public_pem=pub, private_pem=priv)
    db.add(k)
    db.commit()
    log_op(db, user.id, "key_import", True,
           {"key_id": k.id, "bits": bits, "fingerprint": fp, "kind": "keypair" if priv else "public only"})
    return key_dict(k)


@router.get("/{key_id}/export", response_class=PlainTextResponse)
def export(key_id: int, part: str = Query("public", pattern="^(public|private)$"),
           user: User = Depends(current_user), db: Session = Depends(get_db)):
    k = get_key(db, user, key_id)
    if part == "private":
        if not k.private_pem:
            raise HTTPException(400, "This entry has no private key")
        log_op(db, user.id, "key_export_private", True, {"key_id": k.id, "fingerprint": k.fingerprint})
        return k.private_pem
    return k.public_pem


@router.delete("/{key_id}")
def delete(key_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    k = get_key(db, user, key_id)
    log_op(db, user.id, "key_delete", True, {"key_id": k.id, "fingerprint": k.fingerprint})
    db.delete(k)
    db.commit()
    return {"ok": True}
