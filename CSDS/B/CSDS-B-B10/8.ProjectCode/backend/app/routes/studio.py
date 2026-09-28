import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import STORE_DIR, Job, User, get_db
from ..services import cipher as C
from ..services.imaging import (decode, histograms, list_samples, png_bytes, preview_b64, read_path,
                                sample_path, subband_views)
from .common import key_or_new, load_input

router = APIRouter(prefix="/api", tags=["studio"])


@router.get("/samples")
def samples():
    return list_samples()


@router.get("/samples/file/{kind}/{name}")
def sample_file(kind: str, name: str):
    try:
        return FileResponse(sample_path(kind, name))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/keys/new")
def new_key(user: User = Depends(current_user)):
    return {"key": C.new_key()}


def _job_out(j: Job):
    return {"id": j.id, "name": j.name, "source": j.source, "width": j.width, "height": j.height,
            "channels": j.channels, "nonce": j.nonce, "key_fp": j.key_fp, "plain_sha256": j.plain_sha256,
            "cipher_sha256": j.cipher_sha256, "enc_ms": j.enc_ms, "created_at": j.created_at.isoformat()}


@router.post("/studio/encrypt")
async def encrypt(file: Optional[UploadFile] = File(None), sample_kind: str = Form(""), sample_name: str = Form(""),
                  key: str = Form(""), user: User = Depends(current_user), db: Session = Depends(get_db)):
    img, name, source, resized = await load_input(db, user, file, sample_kind, sample_name)
    key = key_or_new(key)
    nonce = C.new_nonce()
    ts = time.perf_counter()
    C.permutation(C.parse_key(key), img.size)   # one-off key setup, cached for this key and size
    t0 = time.perf_counter()
    enc = C.encrypt(img, key, nonce)
    enc_ms = (time.perf_counter() - t0) * 1000
    key_setup_ms = (t0 - ts) * 1000
    coef = C.dwt_forward(img)

    stem = uuid.uuid4().hex
    plain_path, cipher_path = STORE_DIR / f"{stem}_plain.png", STORE_DIR / f"{stem}_cipher.png"
    plain_path.write_bytes(png_bytes(img))
    cipher_path.write_bytes(png_bytes(enc))
    job = Job(user_id=user.id, name=name, source=source, width=img.shape[1], height=img.shape[0],
              channels=1 if img.ndim == 2 else img.shape[2], nonce=nonce, key_fp=C.key_fingerprint(key),
              plain_sha256=C.pixel_sha256(img), cipher_sha256=C.pixel_sha256(enc), enc_ms=enc_ms,
              plain_path=str(plain_path), cipher_path=str(cipher_path))
    db.add(job)
    db.commit()
    return {
        "job": _job_out(job), "key": key, "resized": resized, "key_setup_ms": key_setup_ms,
        "plain": preview_b64(img), "cipher": preview_b64(enc), "coefficients": preview_b64(coef),
        "subbands": subband_views(img),
        "histograms": {"plain": histograms(img), "cipher": histograms(enc)},
    }


@router.post("/studio/decrypt")
async def decrypt(key: str = Form(...), job_id: Optional[int] = Form(None), nonce: str = Form(""),
                  file: Optional[UploadFile] = File(None), user: User = Depends(current_user),
                  db: Session = Depends(get_db)):
    """Decrypt a stored job, or an uploaded cipher PNG with its nonce."""
    job = None
    try:
        C.parse_key(key)
        if file is not None and file.filename:
            enc, _ = decode(await file.read(), limit=False)
            C.parse_nonce(nonce)
        elif job_id:
            job = db.get(Job, job_id)
            if not job or job.user_id != user.id:
                raise HTTPException(404, "Job not found")
            enc, _ = read_path(job.cipher_path, limit=False)
            nonce = job.nonce
        else:
            raise HTTPException(400, "Choose an encrypted job or upload a cipher image")
    except ValueError as e:
        raise HTTPException(400, str(e))
    t0 = time.perf_counter()
    dec = C.decrypt(enc, key, nonce)
    dec_ms = (time.perf_counter() - t0) * 1000
    sha = C.pixel_sha256(dec)
    expected = job.plain_sha256 if job else None
    return {
        "decrypted": preview_b64(dec), "dec_ms": dec_ms, "sha256": sha, "expected_sha256": expected,
        "match": (sha == expected) if expected else None,
        "key_matches_job": (C.key_fingerprint(key) == job.key_fp) if job else None,
        "histogram": histograms(dec),
    }


@router.get("/studio/jobs")
def jobs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Job).filter(Job.user_id == user.id).order_by(Job.id.desc()).limit(50).all()
    return [_job_out(j) for j in rows]


@router.get("/studio/jobs/{job_id}/cipher.png")
def cipher_png(job_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Job not found")
    return Response(open(job.cipher_path, "rb").read(), media_type="image/png",
                    headers={"Content-Disposition": f'attachment; filename="cipher_{job.id}_{job.nonce}.png"'})
