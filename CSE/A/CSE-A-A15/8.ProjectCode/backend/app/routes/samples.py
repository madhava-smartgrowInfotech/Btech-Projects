from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..auth import current_user
from ..config import COVERS_DIR, PAYLOADS_DIR
from ..services import lsb

router = APIRouter(prefix="/api/samples", tags=["samples"], dependencies=[Depends(current_user)])


def sample_path(folder, name: str):
    """Resolve a sample by matching against the directory listing, never by joining raw input."""
    for p in folder.iterdir():
        if p.is_file() and p.name == name:
            return p
    raise HTTPException(404, f"Sample '{name}' not found")


@router.get("/covers")
def covers():
    rows = []
    for p in sorted(COVERS_DIR.glob("*.png")):
        arr = lsb.load_rgb(str(p))
        h, w = arr.shape[:2]
        rows.append({"name": p.name, "width": w, "height": h, "size_bytes": p.stat().st_size,
                     "capacity_bytes": lsb.capacity_bytes(arr)})
    return rows


@router.get("/payloads")
def payloads():
    return [{"name": p.name, "size_bytes": p.stat().st_size} for p in sorted(PAYLOADS_DIR.iterdir()) if p.is_file()]


@router.get("/covers/{name}")
def cover_file(name: str):
    return FileResponse(sample_path(COVERS_DIR, name))


@router.get("/payloads/{name}")
def payload_file(name: str):
    return FileResponse(sample_path(PAYLOADS_DIR, name), filename=name)
