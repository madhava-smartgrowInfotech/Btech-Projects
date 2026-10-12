import json
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import COVERS_DIR, MAX_UPLOAD_BYTES, OUTPUTS_DIR, PAYLOADS_DIR
from ..db import OpLog, User, get_db, log_op
from ..services import crypto, lsb, pipeline
from .keys import get_key
from .samples import sample_path

router = APIRouter(prefix="/api", tags=["operations"])


async def read_upload(f: UploadFile) -> bytes:
    data = await f.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 25 MB")
    return data


def get_op(db: Session, user: User, op_id: int, kind: str | None = None) -> OpLog:
    row = db.get(OpLog, op_id)
    if not row or row.user_id != user.id or (kind and row.op != kind):
        raise HTTPException(404, "Operation not found")
    return row


def op_dir(op_id: int):
    d = OUTPUTS_DIR / str(op_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)[:80] or "payload.bin"


@router.post("/send")
async def send(key_id: int = Form(...),
               payload: UploadFile | None = File(None), payload_sample: str | None = Form(None),
               cover: UploadFile | None = File(None), cover_sample: str | None = Form(None),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    key = get_key(db, user, key_id)

    if payload is not None and payload.filename:
        filename, data = payload.filename, await read_upload(payload)
    elif payload_sample:
        p = sample_path(PAYLOADS_DIR, payload_sample)
        filename, data = p.name, p.read_bytes()
    else:
        raise HTTPException(400, "Choose a file to protect")
    if not data:
        raise HTTPException(400, "The file is empty")

    try:
        if cover is not None and cover.filename:
            cover_name, cover_arr = cover.filename, lsb.load_rgb(await read_upload(cover))
        elif cover_sample:
            p = sample_path(COVERS_DIR, cover_sample)
            cover_name, cover_arr = p.name, lsb.load_rgb(str(p))
        else:
            raise HTTPException(400, "Choose a cover image")
        result = pipeline.hide(key.public_pem, filename, data, cover_arr)
    except (lsb.StegoError, crypto.CryptoError) as exc:
        log_op(db, user.id, "send", False, {"error": str(exc), "payload_bytes": len(data)})
        raise HTTPException(400, str(exc))

    details = {
        "key_id": key.id, "key_name": key.name, "fingerprint": key.fingerprint, "key_bits": key.bits,
        "filename": filename, "payload_bytes": len(data), "cover": cover_name,
        "input_sha256": result["info"]["input_sha256"], "bundle_bytes": result["bundle_len"],
        "capacity": result["capacity"], "timings_ms": result["timings_ms"], "quality": result["quality"],
    }
    row = log_op(db, user.id, "send", True, details)
    d = op_dir(row.id)
    (d / "cover.png").write_bytes(lsb.to_png_bytes(cover_arr))
    (d / "stego.png").write_bytes(result["stego_png"])
    return {"op_id": row.id, **details}


@router.post("/receive")
async def receive(key_id: int = Form(...), stego: UploadFile | None = File(None),
                  from_op: int | None = Form(None),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    key = get_key(db, user, key_id)
    if not key.private_pem:
        raise HTTPException(400, "This entry has no private key - choose one of your own keypairs")
    source = ""
    try:
        if stego is not None and stego.filename:
            source, arr = stego.filename, lsb.load_rgb(await read_upload(stego))
        elif from_op:
            get_op(db, user, from_op, "send")
            source, arr = f"send #{from_op}", lsb.load_rgb(str(OUTPUTS_DIR / str(from_op) / "stego.png"))
        else:
            raise HTTPException(400, "Choose a stego image")
        result = pipeline.reveal(key.private_pem, arr)
    except (lsb.StegoError, crypto.CryptoError) as exc:
        log_op(db, user.id, "receive", False, {"error": str(exc), "key_id": key.id, "source": source})
        raise HTTPException(400, str(exc))

    info = result["info"]
    details = {
        "key_id": key.id, "key_name": key.name, "fingerprint": key.fingerprint, "source": source,
        "filename": result["filename"], "output_bytes": info["size"], "bundle_bytes": result["bundle_len"],
        "embedded_sha256": info["embedded_sha256"], "output_sha256": info["output_sha256"],
        "hash_match": info["match"], "gcm_verified": True, "timings_ms": result["timings_ms"],
    }
    row = log_op(db, user.id, "receive", True, details)
    (op_dir(row.id) / "restored.bin").write_bytes(result["data"])
    return {"op_id": row.id, **details}


@router.get("/ops/{op_id}/{what}")
def op_file(op_id: int, what: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = get_op(db, user, op_id)
    d = OUTPUTS_DIR / str(op_id)
    if what in ("cover", "stego") and row.op == "send":
        return FileResponse(d / f"{what}.png", media_type="image/png",
                            filename=f"{what}_{op_id}.png" if what == "stego" else None)
    if what == "restored" and row.op == "receive":
        return FileResponse(d / "restored.bin", filename=safe_name(row.data()["filename"]))
    raise HTTPException(404, "No such file for this operation")
