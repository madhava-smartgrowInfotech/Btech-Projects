import json
import statistics

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from ml.vocab import LETTERS, WORDS

from .. import state
from ..config import EXPERIMENTS_DIR, GEMINI_API_KEY
from ..services.sentence import is_online

router = APIRouter(prefix="/api", tags=["info"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "models_loaded": state.recognizer is not None,
        "speech_ready": bool(state.stt and state.stt.ready),
        "speech_model": state.stt.size if state.stt else None,
        "online": await run_in_threadpool(is_online),
        "gemini_configured": bool(GEMINI_API_KEY),
    }


@router.get("/vocab")
def vocab():
    words = [{"gloss": w["gloss"], "text": w["text"], "category": w["source"].split("/")[0]} for w in WORDS]
    return {"words": words, "letters": LETTERS}


@router.get("/metrics")
def metrics():
    out = {}
    for key, path in (("evaluation", EXPERIMENTS_DIR / "eval" / "metrics.json"),
                      ("training", EXPERIMENTS_DIR / "train_metrics.json")):
        if path.exists():
            data = json.loads(path.read_text())
            if key == "training":
                data = {k: {kk: vv for kk, vv in v.items() if kk != "history"} for k, v in data.items()}
            out[key] = data
    lat = sorted(state.recognizer.recent_latency) if state.recognizer else []
    out["live"] = {
        "frames": len(lat),
        "avg_frame_ms": round(statistics.mean(lat), 1) if lat else None,
        "p95_frame_ms": round(lat[int(len(lat) * 0.95) - 1], 1) if len(lat) >= 20 else None,
    }
    return out
