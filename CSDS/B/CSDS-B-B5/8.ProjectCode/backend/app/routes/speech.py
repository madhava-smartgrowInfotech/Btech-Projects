from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .. import state
from ..auth import current_user
from ..services import tts
from ..services.sentence import build_sentence

router = APIRouter(prefix="/api", tags=["speech"])


class SentenceIn(BaseModel):
    glosses: list[str] = Field(min_length=1, max_length=40)
    use_gemini: bool = True


class TTSIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    rate: int = Field(165, ge=80, le=300)


@router.post("/sentence")
async def sentence(body: SentenceIn, user=Depends(current_user)):
    glosses = [g.strip().upper() for g in body.glosses if g.strip()]
    return await run_in_threadpool(build_sentence, glosses, body.use_gemini)


@router.post("/tts")
async def speak(body: TTSIn, user=Depends(current_user)):
    try:
        wav, ms = await run_in_threadpool(tts.synth, body.text, body.rate)
    except Exception as e:
        raise HTTPException(500, str(e))
    return Response(wav, media_type="audio/wav", headers={"X-Latency-Ms": f"{ms:.0f}"})


@router.post("/speech/transcribe")
async def transcribe(request: Request, language: str = Query("en", pattern="^(en|hi|auto)$"),
                     user=Depends(current_user)):
    """Body: 16 kHz mono 16-bit little-endian PCM."""
    body = await request.body()
    if len(body) > 16000 * 2 * 30:
        raise HTTPException(413, "Send at most 30 seconds of audio at a time")
    try:
        return await run_in_threadpool(state.stt.transcribe, body[: len(body) // 2 * 2],
                                       None if language == "auto" else language)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
