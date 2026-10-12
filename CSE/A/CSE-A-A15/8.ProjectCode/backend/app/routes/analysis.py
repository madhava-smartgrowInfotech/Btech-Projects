import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import OUTPUTS_DIR
from ..db import KeyPair, OpLog, User, get_db, log_op
from ..services import benchmark, lsb, plots, robustness
from .ops import get_op

router = APIRouter(prefix="/api", tags=["analysis"])


def _load_pair(op_id: int):
    d = OUTPUTS_DIR / str(op_id)
    return lsb.load_rgb(str(d / "cover.png")), lsb.load_rgb(str(d / "stego.png"))


@router.get("/analysis/{op_id}")
def analysis(op_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = get_op(db, user, op_id, "send")
    return {"op_id": op_id, **row.data()}


@router.get("/analysis/{op_id}/histogram.png")
def histogram(op_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_op(db, user, op_id, "send")
    cache = OUTPUTS_DIR / str(op_id) / "histogram.png"
    if not cache.exists():
        cache.write_bytes(plots.histogram_png(*_load_pair(op_id)))
    return Response(cache.read_bytes(), media_type="image/png")


@router.get("/analysis/{op_id}/bitplanes.png")
def bitplanes(op_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_op(db, user, op_id, "send")
    cache = OUTPUTS_DIR / str(op_id) / "bitplanes.png"
    if not cache.exists():
        cache.write_bytes(plots.bitplanes_png(*_load_pair(op_id)))
    return Response(cache.read_bytes(), media_type="image/png")


@router.post("/robustness/{op_id}")
def run_robustness(op_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = get_op(db, user, op_id, "send")
    d = row.data()
    key = db.get(KeyPair, d["key_id"])
    if not key or key.user_id != user.id or not key.private_pem:
        raise HTTPException(400, "The recipient key for this operation is no longer available with its private half")
    _, stego = _load_pair(op_id)
    results = robustness.run_attacks(stego, key.private_pem, d["input_sha256"], d["bundle_bytes"])
    out = {"op_id": op_id, "results": results,
           "survived": [r["label"] for r in results if r["status"] == "recovered"],
           "lost": [r["label"] for r in results if r["status"] != "recovered"]}
    (OUTPUTS_DIR / str(op_id) / "robustness.json").write_text(json.dumps(out))
    log_op(db, user.id, "robustness", True, {"send_op": op_id, "survived": out["survived"], "lost": out["lost"]})
    return out


@router.get("/robustness/{op_id}")
def last_robustness(op_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_op(db, user, op_id, "send")
    f = OUTPUTS_DIR / str(op_id) / "robustness.json"
    return json.loads(f.read_text()) if f.exists() else None


@router.get("/benchmark/capacity")
def capacity(user: User = Depends(current_user)):
    from ..config import COVERS_DIR
    covers = [(p.name, lsb.load_rgb(str(p))) for p in sorted(COVERS_DIR.glob("*.png"))]
    return benchmark.capacity_table(covers)


@router.post("/benchmark/run")
def run_benchmark(user: User = Depends(current_user), db: Session = Depends(get_db)):
    from ..config import COVERS_DIR
    covers = [(p.name, lsb.load_rgb(str(p))) for p in sorted(COVERS_DIR.glob("*.png"))]
    result = benchmark.run(covers, [1024, 16 * 1024, 64 * 1024], key_bits=2048, repeats=2)
    log_op(db, user.id, "benchmark", True, {"covers": len(covers), "rows": len(result["rows"]),
                                          "key_bits": result["key_bits"]})
    return result


@router.get("/log")
def log(op: str | None = None, limit: int = 100, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(OpLog).where(OpLog.user_id == user.id)
    if op:
        q = q.where(OpLog.op == op)
    rows = db.scalars(q.order_by(OpLog.id.desc()).limit(min(max(limit, 1), 500))).all()
    return [{"id": r.id, "op": r.op, "ok": r.ok, "created_at": r.created_at.isoformat(), "details": r.data()}
            for r in rows]
