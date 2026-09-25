from fastapi import APIRouter, Depends, HTTPException

from .. import auth, models, schemas
from ..services.gemini import ask_gemini

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/ask")
async def ask(
    body: schemas.AiAskIn,
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        answer = await ask_gemini(body.question, body.lat, body.lng)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"answer": answer}
