import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import create_token, current_user, user_dict, verify_password
from ..config import EXPERIMENTS_DIR
from ..db import Call, User, get_db
from ..services import nlp, pipeline, summary
from .calls import visible

router = APIRouter(prefix="/api", tags=["misc"])


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.strip().lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": create_token(user), "user": user_dict(user)}


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_dict(user)


@router.get("/health")
def health():
    return {"ok": True, "models_ready": nlp.models_ready(), "gemini_configured": summary.configured(),
            "queue": pipeline.queue_size()}


@router.get("/analytics")
def analytics(days: int = 30, db: Session = Depends(get_db), user: User = Depends(current_user)):
    since = datetime.utcnow() - timedelta(days=max(1, min(days, 365)))
    calls = visible(db, user).filter(Call.recorded_at >= since).all()
    done = [c for c in calls if c.status == "done"]

    per_day = defaultdict(lambda: {"calls": 0, "sent": [], "score": []})
    for c in calls:
        d = per_day[c.recorded_at.date().isoformat()]
        d["calls"] += 1
        if c.status == "done":
            if c.sentiment is not None:
                d["sent"].append(c.sentiment)
            if c.score is not None:
                d["score"].append(c.score)
    trend = [{"date": k, "calls": v["calls"],
              "sentiment": round(sum(v["sent"]) / len(v["sent"]), 3) if v["sent"] else None,
              "score": round(sum(v["score"]) / len(v["score"]), 1) if v["score"] else None}
             for k, v in sorted(per_day.items())]

    board = defaultdict(lambda: {"calls": 0, "scores": [], "change": [], "flags": 0})
    for c in done:
        if c.agent:
            b = board[(c.agent.id, c.agent.name)]
            b["calls"] += 1
            b["scores"].append(c.score or 0)
            b["change"].append(c.sentiment_change or 0)
            b["flags"] += len(c.flags or [])
    leaderboard = sorted(
        [{"agent_id": k[0], "agent": k[1], "calls": v["calls"], "avg_score": round(sum(v["scores"]) / len(v["scores"]), 1),
          "avg_sentiment_change": round(sum(v["change"]) / len(v["change"]), 3), "flags": v["flags"]}
         for k, v in board.items()], key=lambda r: -r["avg_score"])

    flags = [(c, f) for c in done for f in (c.flags or []) if f["severity"] == "high"]
    flags.sort(key=lambda x: x[0].recorded_at, reverse=True)
    return {
        "days": days,
        "totals": {
            "calls": len(calls), "analysed": len(done),
            "processing": sum(c.status in ("queued", "processing") for c in calls),
            "failed": sum(c.status == "failed" for c in calls),
            "avg_score": round(sum(c.score or 0 for c in done) / len(done), 1) if done else None,
            "avg_sentiment": round(sum(c.sentiment or 0 for c in done) / len(done), 3) if done else None,
            "escalations": sum(1 for c in done if any(f["severity"] == "high" for f in (c.flags or []))),
            "minutes": round(sum(c.duration or 0 for c in calls) / 60, 1),
        },
        "trend": trend,
        "intents": [{"intent": k, "count": v} for k, v in Counter(c.intent for c in done if c.intent).most_common(10)],
        "topics": [{"topic": k, "count": v} for k, v in Counter(c.topic for c in done if c.topic).most_common()],
        "emotions": [{"emotion": k, "count": v} for k, v in Counter(
            s.get("emotion") for c in done for s in (c.segments or []) if s.get("speaker") == "customer").most_common()],
        "leaderboard": leaderboard,
        "recent_escalations": [{"call_id": c.id, "title": c.title, "agent": c.agent.name if c.agent else None,
                                "t": f["t"], "text": f["text"]} for c, f in flags[:8]],
    }


def _read(path):
    return json.loads(path.read_text()) if path.exists() else None


@router.get("/metrics")
def metrics(user: User = Depends(current_user)):
    return {"training": _read(EXPERIMENTS_DIR / "metrics.json"), "evaluation": _read(EXPERIMENTS_DIR / "eval" / "metrics.json")}
