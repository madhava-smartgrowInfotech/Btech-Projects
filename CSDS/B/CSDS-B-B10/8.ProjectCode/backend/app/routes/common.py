"""Shared helper: resolve the input image from an upload, a sample, or an earlier studio job."""
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db import Job, User
from ..services import cipher as C
from ..services.imaging import decode, read_path, sample_path


async def load_input(db: Session, user: User, file: Optional[UploadFile], sample_kind: str = "",
                     sample_name: str = "", job_id: Optional[int] = None):
    """Returns (img, name, source, resized)."""
    try:
        if file is not None and file.filename:
            img, resized = decode(await file.read())
            return img, file.filename, "upload", resized
        if job_id:
            job = db.get(Job, job_id)
            if not job or job.user_id != user.id:
                raise HTTPException(404, "Job not found")
            img, _ = read_path(job.plain_path, limit=False)
            return img, job.name, job.source, False
        if sample_kind and sample_name:
            img, resized = read_path(sample_path(sample_kind, sample_name))
            return img, sample_name, sample_kind, resized
    except ValueError as e:
        raise HTTPException(400, str(e))
    raise HTTPException(400, "Choose a sample image or upload one")


def key_or_new(key: str) -> str:
    if not key:
        return C.new_key()
    try:
        return C.parse_key(key).hex()
    except ValueError as e:
        raise HTTPException(400, str(e))
