"""F6 AI mock interviews and F5 expert-led final interviews."""
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, public_user, require
from ..db import Interview, Notification, User, get_db, jdump, jload
from ..services import ai, progress

router = APIRouter(prefix="/api/interviews", tags=["interviews"])
FILLERS = ["um", "uh", "like", "basically", "actually", "you know", "sort of", "kind of"]
EXPERT_RUBRIC = ["technical_depth", "problem_solving", "communication", "role_knowledge", "professionalism"]
EXPERT_PASS = 7.0


def text_metrics(question, ideal, answer):
    """Local NLP signals: TF-IDF relevance to the question + ideal points, length and filler words."""
    answer = answer or ""
    words = re.findall(r"[a-zA-Z']+", answer.lower())
    rel = 0.0
    if words:
        vec = TfidfVectorizer(stop_words="english").fit([question + " " + " ".join(ideal), answer])
        m = vec.transform([question + " " + " ".join(ideal), answer])
        rel = float(cosine_similarity(m[0], m[1])[0][0])
    sentences = [s for s in re.split(r"[.!?]+", answer) if s.strip()]
    low = " " + " ".join(words) + " "
    fillers = sum(low.count(f" {f} ") for f in FILLERS)
    return {"relevance": round(rel, 3), "words": len(words), "fillers": fillers,
            "avg_sentence_words": round(len(words) / len(sentences), 1) if sentences else 0}


def _out(iv, db=None):
    d = {"id": iv.id, "kind": iv.kind, "role": iv.role, "level": iv.level, "status": iv.status, "score": iv.score,
         "questions": jload(iv.questions, []), "answers": jload(iv.answers, []), "report": jload(iv.report, None),
         "scheduled_at": iv.scheduled_at.isoformat() if iv.scheduled_at else None, "created_at": iv.created_at.isoformat()}
    if db is not None:
        u = db.get(User, iv.user_id)
        d["candidate"] = public_user(u) if u else None
        e = db.get(User, iv.expert_id) if iv.expert_id else None
        d["expert"] = e.name if e else None
    return d


class StartIn(BaseModel):
    role: str
    level: str = "Entry"
    count: int = 5


@router.post("/start")
def start(body: StartIn, user: User = Depends(require("candidate")), db: Session = Depends(get_db)):
    role = body.role.strip()
    if not role:
        raise HTTPException(400, "Enter the role you are preparing for")
    st = progress.stats(db, user)
    qs = ai.interview_questions(role, body.level, max(3, min(body.count, 8)), st["skills"])
    if not qs:
        raise HTTPException(502, "The AI did not return any questions - please try again")
    iv = Interview(user_id=user.id, kind="ai", role=role, level=body.level, questions=jdump(qs))
    db.add(iv)
    db.commit()
    return _out(iv)


class AnswersIn(BaseModel):
    answers: list[str]


@router.post("/{iid}/submit")
def submit(iid: int, body: AnswersIn, user: User = Depends(require("candidate")), db: Session = Depends(get_db)):
    iv = db.get(Interview, iid)
    if not iv or iv.user_id != user.id or iv.kind != "ai":
        raise HTTPException(404, "Interview not found")
    if iv.status == "completed":
        raise HTTPException(409, "This interview was already scored")
    qs = jload(iv.questions, [])
    answers = (body.answers + [""] * len(qs))[:len(qs)]
    qa = [{**q, "answer": a.strip()} for q, a in zip(qs, answers)]
    rep = ai.score_interview(iv.role, iv.level, qa)
    for item, q, a in zip(rep["answers"], qs, answers):
        item["nlp"] = text_metrics(q["q"], q.get("ideal_points", []), a)
    rubric_avg = {k: round(sum(x["scores"][k] for x in rep["answers"]) / len(rep["answers"]), 1) for k in ai.RUBRIC}
    rep["rubric_avg"] = rubric_avg
    iv.answers = jdump(answers)
    iv.report = jdump(rep)
    iv.score = round(sum(x["score"] for x in rep["answers"]) / len(rep["answers"]), 1)
    iv.status = "completed"
    db.commit()
    before = user.level
    st = progress.recompute(db, user)
    return {**_out(iv), "level": st["level"], "leveled_up": st["level"] > before}


@router.get("/mine")
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Interview).where(Interview.user_id == user.id).order_by(Interview.created_at.desc())).all()
    return [_out(x) for x in rows]


@router.get("/{iid}")
def get_one(iid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    iv = db.get(Interview, iid)
    if not iv or (iv.user_id != user.id and user.role not in ("expert", "career", "recruiter")):
        raise HTTPException(404, "Interview not found")
    return _out(iv, db)


# ---------------------------------------------------------------- expert-led final level
class RequestIn(BaseModel):
    role: str


@router.post("/expert/request")
def request_expert(body: RequestIn, user: User = Depends(require("candidate")), db: Session = Depends(get_db)):
    st = progress.recompute(db, user)
    if st["level"] < 4:
        raise HTTPException(400, "Reach Level 4 (Interview-ready) before booking the expert interview")
    open_iv = db.scalar(select(Interview).where(Interview.user_id == user.id, Interview.kind == "expert",
                                                Interview.status.in_(["requested", "scheduled"])))
    if open_iv:
        raise HTTPException(409, "You already have an expert interview pending")
    iv = Interview(user_id=user.id, kind="expert", role=body.role.strip() or "Software Engineer", status="requested")
    db.add(iv)
    for e in db.scalars(select(User).where(User.role == "expert")).all():
        db.add(Notification(user_id=e.id, text=f"{user.name} requested an expert mock interview for {iv.role}."))
    db.commit()
    return _out(iv)


@router.get("/expert/queue")
def expert_queue(user: User = Depends(require("expert")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Interview).where(Interview.kind == "expert").order_by(Interview.created_at.desc())).all()
    out = []
    for iv in rows:
        d = _out(iv, db)
        u = db.get(User, iv.user_id)
        d["evidence"] = progress.evidence(progress.stats(db, u))
        out.append(d)
    return out


class ScheduleIn(BaseModel):
    scheduled_at: datetime


@router.post("/expert/{iid}/schedule")
def schedule(iid: int, body: ScheduleIn, user: User = Depends(require("expert")), db: Session = Depends(get_db)):
    iv = db.get(Interview, iid)
    if not iv or iv.kind != "expert" or iv.status == "completed":
        raise HTTPException(404, "Open expert interview not found")
    iv.expert_id = user.id
    iv.scheduled_at = body.scheduled_at.replace(tzinfo=None)
    iv.status = "scheduled"
    db.add(Notification(user_id=iv.user_id, text=f"Your expert interview with {user.name} is scheduled for "
                                                 f"{iv.scheduled_at:%d %b %Y %H:%M} UTC."))
    db.commit()
    return _out(iv, db)


class EvalIn(BaseModel):
    scores: dict[str, int]
    notes: str = ""


@router.post("/expert/{iid}/evaluate")
def evaluate(iid: int, body: EvalIn, user: User = Depends(require("expert")), db: Session = Depends(get_db)):
    iv = db.get(Interview, iid)
    if not iv or iv.kind != "expert" or iv.status == "completed":
        raise HTTPException(404, "Open expert interview not found")
    sc = {k: max(0, min(10, int(body.scores.get(k, 0)))) for k in EXPERT_RUBRIC}
    iv.score = round(sum(sc.values()) / len(sc), 1)
    iv.expert_id = user.id
    iv.status = "completed"
    passed = iv.score >= EXPERT_PASS
    iv.report = jdump({"expert_scores": sc, "notes": body.notes, "passed": passed, "pass_mark": EXPERT_PASS,
                       "evaluated_at": datetime.utcnow().isoformat()})
    cand = db.get(User, iv.user_id)
    db.add(Notification(user_id=cand.id, text=f"Expert interview result: {iv.score}/10 - "
                                              f"{'passed' if passed else 'not passed yet, you can request another'}."))
    db.commit()
    st = progress.recompute(db, cand)
    return {**_out(iv, db), "candidate_level": st["level"], "job_ready": st["job_ready"]}
