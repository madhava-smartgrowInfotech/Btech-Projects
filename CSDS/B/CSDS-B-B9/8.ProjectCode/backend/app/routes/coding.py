"""F2 coding practice and judge."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, require
from ..db import Contest, Submission, User, get_db, jdump, jload
from ..services import contests as contest_svc
from ..services import judge, problems, progress

router = APIRouter(prefix="/api", tags=["coding"])


@router.get("/languages")
def languages():
    return judge.available_languages()


@router.get("/problems")
def list_problems(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(Submission.problem_slug, Submission.verdict).where(Submission.user_id == user.id)).all()
    solved = {s for s, v in rows if v == "Accepted"}
    tried = {s for s, _ in rows}
    return [{**problems.public(p), "status": "solved" if p["slug"] in solved else "tried" if p["slug"] in tried else "new"}
            for p in problems.all_problems()]


@router.get("/problems/{slug}")
def get_problem(slug: str, user: User = Depends(current_user)):
    p = problems.get(slug)
    if not p:
        raise HTTPException(404, "Problem not found")
    return problems.public(p, full=True)


class CodeIn(BaseModel):
    language: str
    code: str
    contest_id: int | None = None


def _check(body):
    if body.language not in judge.LANGS:
        raise HTTPException(400, "Language must be python, cpp or java")
    if not body.code.strip():
        raise HTTPException(400, "Write some code first")
    if len(body.code) > 64_000:
        raise HTTPException(400, "Code is too long (64 KB max)")


@router.post("/problems/{slug}/run")
def run_samples(slug: str, body: CodeIn, user: User = Depends(current_user)):
    p = problems.get(slug)
    if not p:
        raise HTTPException(404, "Problem not found")
    _check(body)
    return judge.judge(body.language, body.code, p["samples"], stop_on_fail=False, show_io=True)


@router.post("/problems/{slug}/submit")
def submit(slug: str, body: CodeIn, user: User = Depends(require("candidate")), db: Session = Depends(get_db)):
    p = problems.get(slug)
    if not p:
        raise HTTPException(404, "Problem not found")
    _check(body)
    contest_id = None
    if body.contest_id:
        c = db.get(Contest, body.contest_id)
        if not c or slug not in jload(c.problem_slugs, []):
            raise HTTPException(400, "This problem is not part of that contest")
        if contest_svc.status(c) != "running":
            raise HTTPException(400, "The contest is not running")
        contest_id = c.id
    res = judge.judge(body.language, body.code, problems.tests_for_submit(p))
    sub = Submission(user_id=user.id, problem_slug=slug, language=body.language, code=body.code,
                     verdict=res["verdict"], passed=res["passed"], total=res["total"], time_ms=res["time_ms"],
                     detail=jdump({"message": res["message"], "tests": res["tests"]}), contest_id=contest_id)
    db.add(sub)
    db.commit()
    before = user.level
    st = progress.recompute(db, user)
    return {**res, "submission_id": sub.id, "level": st["level"], "leveled_up": st["level"] > before}


@router.get("/submissions")
def my_submissions(slug: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Submission).where(Submission.user_id == user.id)
    if slug:
        q = q.where(Submission.problem_slug == slug)
    rows = db.scalars(q.order_by(Submission.created_at.desc()).limit(50)).all()
    return [{"id": s.id, "problem": s.problem_slug, "language": s.language, "verdict": s.verdict, "passed": s.passed,
             "total": s.total, "time_ms": s.time_ms, "contest_id": s.contest_id, "at": s.created_at.isoformat(),
             "message": (jload(s.detail, {}) or {}).get("message", "")} for s in rows]


@router.get("/submissions/{sid}")
def get_submission(sid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = db.get(Submission, sid)
    if not s or s.user_id != user.id:
        raise HTTPException(404, "Submission not found")
    return {"id": s.id, "problem": s.problem_slug, "language": s.language, "code": s.code, "verdict": s.verdict}
