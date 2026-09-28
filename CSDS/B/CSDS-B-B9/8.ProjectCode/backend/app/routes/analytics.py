"""F9 readiness analytics for career-services teams."""
from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..auth import require
from ..db import AnswerLog, Submission, User, get_db
from ..services import problems, progress

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/readiness")
def readiness(include_sample: bool = True, user: User = Depends(require("career", "recruiter")),
              db: Session = Depends(get_db)):
    cands = [u for u in progress.candidates(db) if include_sample or not u.is_sample]
    ids = [u.id for u in cands]
    rows = []
    for u in cands:
        st = progress.stats(db, u)
        rows.append({"id": u.id, "name": u.name, "is_sample": u.is_sample, "level": st["level"],
                     "readiness": st["readiness"], "components": st["components"], "solved": st["solved_count"],
                     "ats": st["ats"], "rating": u.rating, "job_ready": st["job_ready"]})
    n = len(rows) or 1
    buckets = [{"range": f"{lo}-{lo + 19 if lo < 80 else 100}",
                "count": sum(1 for r in rows if lo <= r["readiness"] < lo + 20 or (lo == 80 and r["readiness"] == 100))}
               for lo in range(0, 100, 20)]
    levels = [{"level": L["level"], "name": L["name"], "count": sum(1 for r in rows if r["level"] == L["level"])}
              for L in progress.LEVELS]
    comp_avg = {k: round(sum(r["components"][k] for r in rows) / n, 1) for k in progress.WEIGHTS}

    topic_rows = db.execute(select(AnswerLog.kind, AnswerLog.topic, func.count(),
                                   func.sum(case((AnswerLog.correct, 1), else_=0)),
                                   func.count(func.distinct(AnswerLog.user_id)))
                            .where(AnswerLog.user_id.in_(ids)).group_by(AnswerLog.kind, AnswerLog.topic)).all()
    topics = [{"kind": k, "topic": t, "attempts": a, "accuracy": round(100 * (c or 0) / a, 1), "candidates": nu}
              for k, t, a, c, nu in topic_rows if a]
    topics.sort(key=lambda x: x["accuracy"])

    sub_rows = db.execute(select(Submission.problem_slug, Submission.verdict, func.count())
                          .where(Submission.user_id.in_(ids)).group_by(Submission.problem_slug, Submission.verdict)).all()
    verdicts, by_topic = {}, {}
    for slug, v, c in sub_rows:
        verdicts[v] = verdicts.get(v, 0) + c
        p = problems.get(slug)
        t = by_topic.setdefault(p["topic"] if p else "Other", {"topic": p["topic"] if p else "Other", "submissions": 0, "accepted": 0})
        t["submissions"] += c
        t["accepted"] += c if v == "Accepted" else 0
    coding_topics = sorted(({**t, "acceptance": round(100 * t["accepted"] / t["submissions"], 1)} for t in by_topic.values()),
                           key=lambda x: x["acceptance"])
    return {
        "cohort_size": len(rows), "avg_readiness": round(sum(r["readiness"] for r in rows) / n, 1),
        "job_ready": sum(r["job_ready"] for r in rows), "buckets": buckets, "levels": levels,
        "component_avg": comp_avg, "weights": progress.WEIGHTS, "weak_topics": topics[:8], "topics": topics,
        "coding_topics": coding_topics, "verdicts": verdicts,
        "candidates": sorted(rows, key=lambda r: -r["readiness"]),
    }
