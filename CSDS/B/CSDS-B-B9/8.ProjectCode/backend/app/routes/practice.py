"""F1 aptitude practice and F3 technical MCQs: topic/difficulty bank, timed tests, scoring, explanations."""
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import current_user, require
from ..db import AnswerLog, Question, TestAttempt, User, get_db, jdump, jload
from ..services import ai, progress

router = APIRouter(prefix="/api/practice", tags=["practice"])
SECONDS_PER_QUESTION = {"aptitude": 60, "technical": 45}
GRACE_SEC = 30


@router.get("/topics")
def topics(kind: str = "aptitude", db: Session = Depends(get_db)):
    rows = db.execute(select(Question.topic, Question.difficulty, func.count()).where(Question.kind == kind)
                      .group_by(Question.topic, Question.difficulty)).all()
    out = {}
    for t, d, n in rows:
        out.setdefault(t, {"topic": t, "total": 0, "by_difficulty": {}})
        out[t]["total"] += n
        out[t]["by_difficulty"][d] = n
    return sorted(out.values(), key=lambda x: -x["total"])


class StartIn(BaseModel):
    kind: str = "aptitude"
    topic: str = "All"
    difficulty: str = "Any"
    count: int = 10


@router.post("/start")
def start(body: StartIn, user: User = Depends(require("candidate")), db: Session = Depends(get_db)):
    if body.kind not in SECONDS_PER_QUESTION:
        raise HTTPException(400, "kind must be aptitude or technical")
    q = select(Question).where(Question.kind == body.kind)
    if body.topic != "All":
        q = q.where(Question.topic == body.topic)
    if body.difficulty != "Any":
        q = q.where(Question.difficulty == body.difficulty)
    pool = db.scalars(q).all()
    if not pool:
        raise HTTPException(404, "No questions match this topic and difficulty")
    count = max(1, min(body.count, 30, len(pool)))
    picked = random.sample(pool, count)
    limit = count * SECONDS_PER_QUESTION[body.kind]
    att = TestAttempt(user_id=user.id, kind=body.kind, topic=body.topic, difficulty=body.difficulty,
                      question_ids=jdump([x.id for x in picked]), time_limit_sec=limit, total=count)
    db.add(att)
    db.commit()
    return {"attempt_id": att.id, "time_limit_sec": limit, "started_at": att.started_at.isoformat(),
            "questions": [{"id": x.id, "text": x.text, "options": jload(x.options), "topic": x.topic,
                           "difficulty": x.difficulty} for x in picked]}


class SubmitIn(BaseModel):
    answers: dict[str, int] = {}


def score_attempt(db, att, answers, when=None):
    """Score answers {question_id: option_index}; shared by the API and the sample-data seeder."""
    when = when or datetime.utcnow()
    ids = jload(att.question_ids, [])
    qs = {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(ids))).all()}
    late = (when - att.started_at).total_seconds() > att.time_limit_sec + GRACE_SEC
    correct, review = 0, []
    for qid in ids:
        q = qs[qid]
        chosen = -1 if late else int(answers.get(str(qid), answers.get(qid, -1)))
        ok = chosen == q.answer
        correct += ok
        db.add(AnswerLog(user_id=att.user_id, attempt_id=att.id, question_id=qid, kind=att.kind, topic=q.topic,
                         chosen=chosen, correct=ok))
        review.append({"id": qid, "text": q.text, "options": jload(q.options), "chosen": chosen, "answer": q.answer,
                       "correct": ok, "topic": q.topic, "explanation": q.explanation, "ai_explanation": q.ai_explanation})
    att.correct = correct
    att.score_pct = round(100 * correct / len(ids), 1) if ids else 0
    att.submitted_at = when
    return review, late


@router.post("/{attempt_id}/submit")
def submit(attempt_id: int, body: SubmitIn, user: User = Depends(require("candidate")), db: Session = Depends(get_db)):
    att = db.get(TestAttempt, attempt_id)
    if not att or att.user_id != user.id:
        raise HTTPException(404, "Test not found")
    if att.submitted_at:
        raise HTTPException(409, "This test was already submitted")
    review, late = score_attempt(db, att, body.answers)
    db.commit()
    before = user.level
    st = progress.recompute(db, user)
    by_topic = {}
    for r in review:
        t = by_topic.setdefault(r["topic"], {"topic": r["topic"], "correct": 0, "total": 0})
        t["total"] += 1
        t["correct"] += r["correct"]
    return {"attempt_id": att.id, "score_pct": att.score_pct, "correct": att.correct, "total": att.total,
            "late": late, "duration_sec": int((att.submitted_at - att.started_at).total_seconds()),
            "by_topic": list(by_topic.values()), "review": review, "level": st["level"], "leveled_up": st["level"] > before}


@router.post("/explain/{qid}")
def explain(qid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404, "Question not found")
    if not q.ai_explanation:
        q.ai_explanation = ai.explain_question(q.text, jload(q.options), q.answer)
        db.commit()
    return {"id": q.id, "ai_explanation": q.ai_explanation}


@router.get("/history")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(TestAttempt).where(TestAttempt.user_id == user.id, TestAttempt.submitted_at.is_not(None))
                      .order_by(TestAttempt.submitted_at.desc()).limit(30)).all()
    return [{"id": r.id, "kind": r.kind, "topic": r.topic, "difficulty": r.difficulty, "score": r.score_pct,
             "correct": r.correct, "total": r.total, "at": r.submitted_at.isoformat()} for r in rows]
