import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import BenchRun, User, get_db
from ..services import bench
from ..services.imaging import list_samples, read_path, sample_path

router = APIRouter(prefix="/api/bench", tags=["bench"])


class BenchIn(BaseModel):
    size: int = 512
    images: int = 5
    repeats: int = 3


@router.post("/run")
async def run(body: BenchIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.size not in (256, 512, 1024) or not (1 <= body.images <= 20) or not (1 <= body.repeats <= 10):
        raise HTTPException(400, "Size must be 256/512/1024, images 1-20, repeats 1-10")
    samples = [s for s in list_samples() if s["kind"] == "visdrone"][: body.images]
    if not samples:
        raise HTTPException(400, "No sample drone images found - run scripts/download_data.py")
    imgs = [read_path(sample_path(s["kind"], s["name"]))[0] for s in samples]
    data = await asyncio.to_thread(bench.run, imgs, body.size, body.repeats)
    data["image_names"] = [s["name"] for s in samples]
    run = BenchRun(user_id=user.id, data_json=json.dumps(data))
    db.add(run)
    db.commit()
    return {"id": run.id, "created_at": run.created_at.isoformat(), **data}


@router.get("/runs")
def runs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(BenchRun).filter(BenchRun.user_id == user.id).order_by(BenchRun.id.desc()).limit(10).all()
    return [{"id": r.id, "created_at": r.created_at.isoformat(), **json.loads(r.data_json)} for r in rows]
