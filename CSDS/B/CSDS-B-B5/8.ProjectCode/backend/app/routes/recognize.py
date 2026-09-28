from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool

from .. import state
from ..auth import current_user

router = APIRouter(prefix="/api/recognize", tags=["recognition"])


@router.post("/frame")
async def frame(request: Request, session: str = Query(..., max_length=64),
                mode: str = Query("words", pattern="^(words|letters)$"), user=Depends(current_user)):
    """Body: one JPEG camera frame."""
    body = await request.body()
    if not body:
        raise HTTPException(400, "Empty camera frame")
    if len(body) > 2_000_000:
        raise HTTPException(413, "Frame too large")
    try:
        return await run_in_threadpool(state.recognizer.process, body, f"{user.id}:{session}", mode)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/reset")
def reset(session: str = Query(..., max_length=64), user=Depends(current_user)):
    state.recognizer.reset(f"{user.id}:{session}")
    return {"ok": True}
