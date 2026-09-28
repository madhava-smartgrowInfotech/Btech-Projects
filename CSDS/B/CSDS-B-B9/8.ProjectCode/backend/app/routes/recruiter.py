"""F8 recruiter drives: eligibility rules, ranked shortlist with skill evidence, status pipeline."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import require
from ..db import Application, Drive, Notification, User, get_db, jdump, jload
from ..services import progress
from ..services.skills import normalise

router = APIRouter(prefix="/api/drives", tags=["recruiter"])
STATUSES = ["shortlisted", "invited", "interviewing", "offered", "hired", "rejected"]
SKILL_ALIASES = {"cpp": "c++", "c plus plus": "c++", "js": "javascript", "node": "node.js", "postgres": "postgresql"}


def _skill(s):
    s = normalise(s)
    return SKILL_ALIASES.get(s, s)


class DriveIn(BaseModel):
    title: str
    company: str
    role: str
    min_level: int = 1
    required_skills: list[str] = []
    min_readiness: float = 0
    min_aptitude: float = 0


def _drive_out(d, db):
    apps = db.scalars(select(Application).where(Application.drive_id == d.id)).all()
    counts = {s: sum(1 for a in apps if a.status == s) for s in STATUSES}
    return {"id": d.id, "title": d.title, "company": d.company, "role": d.role, "min_level": d.min_level,
            "required_skills": jload(d.required_skills, []), "min_readiness": d.min_readiness,
            "min_aptitude": d.min_aptitude, "created_at": d.created_at.isoformat(), "pipeline": counts,
            "shortlisted_total": len(apps)}


def _own(did, user, db):
    d = db.get(Drive, did)
    if not d or d.recruiter_id != user.id:
        raise HTTPException(404, "Drive not found")
    return d


@router.get("")
def list_drives(user: User = Depends(require("recruiter")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Drive).where(Drive.recruiter_id == user.id).order_by(Drive.created_at.desc())).all()
    return [_drive_out(d, db) for d in rows]


@router.post("")
def create_drive(body: DriveIn, user: User = Depends(require("recruiter")), db: Session = Depends(get_db)):
    if not body.title.strip() or not body.role.strip():
        raise HTTPException(400, "Title and role are required")
    d = Drive(recruiter_id=user.id, title=body.title.strip(), company=body.company.strip(), role=body.role.strip(),
              min_level=max(1, min(5, body.min_level)),
              required_skills=jdump(sorted({_skill(s) for s in body.required_skills if s.strip()})),
              min_readiness=body.min_readiness, min_aptitude=body.min_aptitude)
    db.add(d)
    db.commit()
    return _drive_out(d, db)


def rank_candidates(db, d):
    req = jload(d.required_skills, [])
    ranked, excluded = [], []
    for u in progress.candidates(db):
        st = progress.stats(db, u)
        reasons = []
        if st["level"] < d.min_level:
            reasons.append(f"level {st['level']} < {d.min_level}")
        missing = [s for s in req if s not in st["skills"]]
        if missing:
            reasons.append("missing " + ", ".join(missing))
        if st["readiness"] < d.min_readiness:
            reasons.append(f"readiness {st['readiness']} < {d.min_readiness}")
        if st["aptitude"]["best"] < d.min_aptitude:
            reasons.append(f"aptitude {st['aptitude']['best']} < {d.min_aptitude}")
        ev = progress.evidence(st)
        if reasons:
            excluded.append({"candidate_id": u.id, "name": u.name, "reasons": reasons, "readiness": st["readiness"]})
            continue
        rating_pct = max(0, min(100, (u.rating - 1000) / 8))
        score = round(0.5 * st["readiness"] + 0.2 * st["level"] * 20 + 0.15 * min(st["solved_count"], 10) * 10
                      + 0.15 * rating_pct, 1)
        skill_ev = []
        for s in req:
            src = []
            lang = {"python": "python", "c++": "cpp", "java": "java"}.get(s)
            if lang and st["languages"].get(lang):
                src.append(f"{st['languages'][lang]} problems accepted in {s}")
            if st["resume_role"] is not None and s in st["skills"] and not src:
                src.append("listed on resume")
            skill_ev.append({"skill": s, "evidence": src or ["listed on resume"]})
        ev["skill_evidence"] = skill_ev
        ranked.append({"candidate_id": u.id, "name": u.name, "email": u.email, "is_sample": u.is_sample,
                       "score": score, "evidence": ev})
    ranked.sort(key=lambda r: -r["score"])
    return ranked, excluded


@router.post("/{did}/shortlist")
def build_shortlist(did: int, user: User = Depends(require("recruiter")), db: Session = Depends(get_db)):
    d = _own(did, user, db)
    ranked, excluded = rank_candidates(db, d)
    existing = {a.candidate_id: a for a in db.scalars(select(Application).where(Application.drive_id == d.id)).all()}
    keep = {r["candidate_id"] for r in ranked}
    for cid, a in existing.items():
        if cid not in keep and a.status == "shortlisted":
            db.delete(a)
    for i, r in enumerate(ranked, 1):
        a = existing.get(r["candidate_id"])
        if not a:
            a = Application(drive_id=d.id, candidate_id=r["candidate_id"])
            db.add(a)
        a.rank, a.score, a.evidence, a.updated_at = i, r["score"], jdump(r["evidence"]), datetime.utcnow()
    db.commit()
    return {"drive": _drive_out(d, db), "shortlist": get_shortlist(did, user, db)["shortlist"],
            "excluded": excluded[:25], "excluded_total": len(excluded)}


@router.get("/{did}")
def get_shortlist(did: int, user: User = Depends(require("recruiter")), db: Session = Depends(get_db)):
    d = _own(did, user, db)
    rows = db.execute(select(Application, User).join(User, User.id == Application.candidate_id)
                      .where(Application.drive_id == d.id).order_by(Application.rank)).all()
    return {"drive": _drive_out(d, db),
            "shortlist": [{"candidate_id": u.id, "name": u.name, "email": u.email, "is_sample": u.is_sample,
                           "rank": a.rank, "score": a.score, "status": a.status, "evidence": jload(a.evidence, {})}
                          for a, u in rows]}


class StatusIn(BaseModel):
    candidate_ids: list[int]
    status: str


@router.post("/{did}/status")
def set_status(did: int, body: StatusIn, user: User = Depends(require("recruiter")), db: Session = Depends(get_db)):
    d = _own(did, user, db)
    if body.status not in STATUSES:
        raise HTTPException(400, f"Status must be one of {', '.join(STATUSES)}")
    apps = db.scalars(select(Application).where(Application.drive_id == d.id,
                                                Application.candidate_id.in_(body.candidate_ids))).all()
    if not apps:
        raise HTTPException(400, "Select at least one shortlisted candidate")
    for a in apps:
        if a.status != body.status:
            a.status = body.status
            a.updated_at = datetime.utcnow()
            msg = (f"You are invited to the {d.company} hiring drive '{d.title}' ({d.role})." if body.status == "invited"
                   else f"Your status in {d.company} - {d.title} is now: {body.status}.")
            db.add(Notification(user_id=a.candidate_id, text=msg))
    db.commit()
    return {"updated": len(apps), "status": body.status}
