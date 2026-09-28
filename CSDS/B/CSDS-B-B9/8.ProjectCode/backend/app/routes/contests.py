"""F4 contests, standings, ratings and the global leaderboard."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import current_user, require
from ..db import Contest, Submission, User, get_db, jdump, jload
from ..services import contests as svc
from ..services import problems

router = APIRouter(prefix="/api", tags=["contests"])


def _out(c, db=None):
    d = {"id": c.id, "title": c.title, "start_at": c.start_at.isoformat() + "Z", "end_at": c.end_at.isoformat() + "Z",
         "status": svc.status(c), "rated": c.rated, "problem_count": len(jload(c.problem_slugs, []))}
    if db is not None:
        d["participants"] = db.scalar(select(func.count(func.distinct(Submission.user_id)))
                                      .where(Submission.contest_id == c.id)) or 0
    return d


@router.get("/contests")
def list_contests(user: User = Depends(current_user), db: Session = Depends(get_db)):
    svc.rate_finished(db)
    rows = db.scalars(select(Contest).order_by(Contest.start_at.desc())).all()
    return [_out(c, db) for c in rows]


@router.get("/contests/{cid}")
def get_contest(cid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(Contest, cid)
    if not c:
        raise HTTPException(404, "Contest not found")
    svc.apply_ratings(db, c)
    st = svc.status(c)
    probs = [problems.public(problems.get(s)) for s in jload(c.problem_slugs, [])] if st != "upcoming" else []
    return {**_out(c, db), "problems": probs}


@router.get("/contests/{cid}/leaderboard")
def contest_leaderboard(cid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(Contest, cid)
    if not c:
        raise HTTPException(404, "Contest not found")
    svc.apply_ratings(db, c)
    return {"contest": _out(c), "rows": svc.standings(db, c), "server_time": datetime.utcnow().isoformat() + "Z"}


class ContestIn(BaseModel):
    title: str
    start_at: datetime
    duration_minutes: int = 120
    problem_slugs: list[str]


@router.post("/contests")
def create_contest(body: ContestIn, user: User = Depends(require("career")), db: Session = Depends(get_db)):
    bad = [s for s in body.problem_slugs if not problems.get(s)]
    if bad or not body.problem_slugs:
        raise HTTPException(400, f"Unknown problems: {', '.join(bad) or 'none selected'}")
    start = body.start_at.replace(tzinfo=None)
    c = Contest(title=body.title.strip() or "Contest", start_at=start,
                end_at=start + timedelta(minutes=max(10, body.duration_minutes)), problem_slugs=jdump(body.problem_slugs))
    db.add(c)
    db.commit()
    return _out(c)


POINTS = {"Easy": 10, "Medium": 20, "Hard": 30}


@router.get("/leaderboard")
def leaderboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Practice leaderboard: points for distinct accepted problems (Easy 10 / Medium 20 / Hard 30), then rating."""
    svc.rate_finished(db)
    pairs = db.execute(select(Submission.user_id, Submission.problem_slug).where(Submission.verdict == "Accepted")
                       .distinct()).all()
    solved, points = {}, {}
    for uid, slug in pairs:
        p = problems.get(slug)
        solved[uid] = solved.get(uid, 0) + 1
        points[uid] = points.get(uid, 0) + (POINTS.get(p["difficulty"], 10) if p else 0)
    users = db.scalars(select(User).where(User.role == "candidate")).all()
    rows = sorted(({"user_id": u.id, "name": u.name, "rating": u.rating, "solved": solved.get(u.id, 0),
                    "points": points.get(u.id, 0), "level": u.level, "job_ready": u.job_ready,
                    "is_sample": u.is_sample, "me": u.id == user.id} for u in users),
                  key=lambda r: (-r["points"], -r["rating"], r["name"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows
