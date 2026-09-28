"""Level progression, readiness score and skill evidence for a candidate."""
from sqlalchemy import func, select

from ..db import Interview, Notification, Resume, Submission, TestAttempt, User, jload

MIN_TEST_QUESTIONS = 10
LEVELS = [
    {"level": 1, "name": "Foundation", "requirement": "Create your candidate profile"},
    {"level": 2, "name": "Aptitude", "requirement": f"Score 60%+ on an aptitude test of {MIN_TEST_QUESTIONS}+ questions"},
    {"level": 3, "name": "Coder", "requirement": "Solve 3 coding problems (Accepted on hidden tests) and score 60%+ on a technical MCQ test"},
    {"level": 4, "name": "Interview-ready", "requirement": "Score 6/10+ in an AI mock interview and 55+ on the resume ATS check"},
    {"level": 5, "name": "Job-ready", "requirement": "Pass an expert-led mock interview (7/10+) - earns the Job-ready badge"},
]
WEIGHTS = {"aptitude": 0.25, "technical": 0.20, "coding": 0.25, "interview": 0.15, "resume": 0.15}
LANG_SKILL = {"python": "python", "cpp": "c++", "java": "java"}


def _tests(db, uid, kind):
    rows = db.scalars(select(TestAttempt).where(TestAttempt.user_id == uid, TestAttempt.kind == kind,
                                                TestAttempt.submitted_at.is_not(None))
                      .order_by(TestAttempt.submitted_at.desc())).all()
    full = [r for r in rows if r.total >= MIN_TEST_QUESTIONS]
    return {"attempts": len(rows), "best": max((r.score_pct for r in full), default=0.0),
            "recent_avg": round(sum(r.score_pct for r in rows[:5]) / min(5, len(rows)), 1) if rows else 0.0}


def stats(db, user):
    uid = user.id
    apt, tech = _tests(db, uid, "aptitude"), _tests(db, uid, "technical")
    acc = db.execute(select(Submission.problem_slug, Submission.language)
                     .where(Submission.user_id == uid, Submission.verdict == "Accepted")).all()
    solved = sorted({s for s, _ in acc})
    langs = {}
    for s, l in set(acc):
        langs[l] = langs.get(l, 0) + 1
    subs = db.scalar(select(func.count()).select_from(Submission).where(Submission.user_id == uid)) or 0
    ai_best = db.scalar(select(func.max(Interview.score)).where(Interview.user_id == uid, Interview.kind == "ai",
                                                                  Interview.status == "completed")) or 0.0
    ai_count = db.scalar(select(func.count()).select_from(Interview).where(
        Interview.user_id == uid, Interview.kind == "ai", Interview.status == "completed")) or 0
    expert_best = db.scalar(select(func.max(Interview.score)).where(
        Interview.user_id == uid, Interview.kind == "expert", Interview.status == "completed"))
    resume = db.scalars(select(Resume).where(Resume.user_id == uid).order_by(Resume.created_at.desc())).first()
    ats = resume.ats_score if resume else 0.0
    skills = set(jload(resume.skills, []) if resume else [])
    skills |= {LANG_SKILL[l] for l in langs}

    checks = {
        2: apt["best"] >= 60,
        3: len(solved) >= 3 and tech["best"] >= 60,
        4: ai_best >= 6 and ats >= 55,
        5: (expert_best or 0) >= 7,
    }
    level = 1
    for lv in (2, 3, 4, 5):
        if checks[lv]:
            level = lv
        else:
            break
    comp = {"aptitude": apt["recent_avg"], "technical": tech["recent_avg"], "coding": min(len(solved), 10) * 10,
            "interview": ai_best * 10, "resume": ats}
    readiness = round(sum(WEIGHTS[k] * v for k, v in comp.items()), 1)
    return {
        "level": level, "checks": checks, "readiness": readiness, "components": comp,
        "aptitude": apt, "technical": tech, "solved": solved, "solved_count": len(solved), "languages": langs,
        "submissions": subs, "ai_interview_best": ai_best, "ai_interviews": ai_count, "expert_score": expert_best,
        "ats": ats, "resume_role": resume.predicted_role if resume else None, "skills": sorted(skills),
        "rating": user.rating, "job_ready": level == 5,
    }


def ladder(st):
    out = []
    for L in LEVELS:
        lv = L["level"]
        out.append({**L, "done": st["level"] >= lv, "current": st["level"] + 1 == lv})
    return out


def recompute(db, user, notify=True):
    st = stats(db, user)
    if st["level"] > user.level and notify:
        name = LEVELS[st["level"] - 1]["name"]
        msg = f"Level up! You reached Level {st['level']} - {name}."
        if st["level"] == 5:
            msg += " You earned the Job-ready badge."
        db.add(Notification(user_id=user.id, text=msg))
    user.level = st["level"]
    user.job_ready = st["job_ready"]
    db.commit()
    return st


def evidence(st):
    return {"level": st["level"], "readiness": st["readiness"], "aptitude_best": st["aptitude"]["best"],
            "technical_best": st["technical"]["best"], "solved": st["solved_count"], "languages": st["languages"],
            "ai_interview": st["ai_interview_best"], "expert_interview": st["expert_score"], "ats": st["ats"],
            "rating": st["rating"], "skills": st["skills"], "job_ready": st["job_ready"]}


def candidates(db):
    return db.scalars(select(User).where(User.role == "candidate")).all()
