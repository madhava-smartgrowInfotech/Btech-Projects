"""First-run seeding: question bank, demo accounts, contests and a clearly labelled SAMPLE cohort.

Sample candidates' activity is generated with a fixed seed, but every result goes through the real pipeline:
tests are scored by the practice scorer, code is judged by the local judge, resumes are real dataset resumes
analysed by the trained classifier, and contest ratings come from the rating engine.
Run manually:  python -m app.seed   (from backend/)
"""
import csv
import json
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from sqlalchemy import func, select

from .auth import hash_password
from .config import DATA
from .db import Contest, Question, Resume, SessionLocal, Submission, TestAttempt, User, init_db, jdump
from .routes.practice import score_attempt
from .services import contests as contest_svc
from .services import judge, problems, progress
from .services import resume as resume_svc

SEED = 7
DEMO_PASSWORD = "Demo@123"
DEMO_USERS = [
    ("Demo Candidate", "candidate@talenttrack.dev", "candidate"),
    ("Demo Recruiter", "recruiter@talenttrack.dev", "recruiter"),
    ("Career Services Team", "career@talenttrack.dev", "career"),
    ("Expert Interviewer", "expert@talenttrack.dev", "expert"),
]
SAMPLE_COUNT = 24
RESUME_CATEGORIES = ["INFORMATION-TECHNOLOGY", "INFORMATION-TECHNOLOGY", "ENGINEERING", "ENGINEERING", "FINANCE",
                     "DESIGNER", "BUSINESS-DEVELOPMENT", "CONSULTANT", "DIGITAL-MEDIA", "BANKING"]
WRONG_CODE = "print(0)\n"


def seed_questions(db):
    if db.scalar(select(func.count()).select_from(Question)):
        return
    bank = json.loads((DATA / "question_bank.json").read_text(encoding="utf-8"))
    for q in bank:
        db.add(Question(kind=q["kind"], topic=q["topic"], difficulty=q["difficulty"], text=q["text"],
                        options=jdump(q["options"]), answer=q["answer"], explanation=q["explanation"], source=q["source"]))
    db.commit()
    print(f"seeded {len(bank)} questions")


def seed_users(db):
    if db.scalar(select(func.count()).select_from(User).where(User.is_sample.is_(False))):
        return
    h = hash_password(DEMO_PASSWORD)
    for name, email, role in DEMO_USERS:
        db.add(User(name=name, email=email, password_hash=h, role=role,
                    target_role="Software Engineer" if role == "candidate" else ""))
    db.commit()
    print("seeded demo accounts")


def seed_contests(db):
    if db.scalar(select(func.count()).select_from(Contest)):
        return
    now = datetime.utcnow().replace(microsecond=0)
    db.add_all([
        Contest(title="Sample Contest #1", start_at=now - timedelta(days=3), end_at=now - timedelta(days=3) + timedelta(hours=2),
                problem_slugs=jdump(["array-sum", "balanced-brackets", "max-subarray", "longest-unique"])),
        Contest(title="Weekly Contest #2", start_at=now - timedelta(hours=1), end_at=now + timedelta(days=7),
                problem_slugs=jdump(["reverse-words", "two-sum-count", "merge-intervals", "island-count"])),
        Contest(title="Weekly Contest #3", start_at=now + timedelta(days=8), end_at=now + timedelta(days=8, hours=2),
                problem_slugs=jdump(["gcd-lcm", "coin-change-ways", "lis-length", "topo-order"])),
    ])
    db.commit()
    print("seeded contests")


def _resume_pool(rng):
    csv.field_size_limit(10**8)
    by_cat = {}
    with open(DATA / "resume" / "Resume.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            by_cat.setdefault(r["Category"], []).append(r["Resume_str"])
    return {c: rng.sample(v, min(6, len(v))) for c, v in by_cat.items()}


def _answer(rng, db, att, ability):
    ids = json.loads(att.question_ids)
    qs = {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(ids))).all()}
    ans = {}
    for qid in ids:
        q = qs[qid]
        ans[str(qid)] = q.answer if rng.random() < ability else rng.choice([i for i in range(4) if i != q.answer])
    return ans


def seed_sample_cohort(db):
    if db.scalar(select(func.count()).select_from(User).where(User.is_sample.is_(True))):
        return
    rng = random.Random(SEED)
    all_p = problems.all_problems()
    print("judging reference and wrong solutions for sample data ...")
    with ThreadPoolExecutor(max_workers=8) as ex:
        ok = dict(zip([p["slug"] for p in all_p], ex.map(
            lambda p: judge.judge("python", p["reference_python"], problems.tests_for_submit(p)), all_p)))
        bad = dict(zip([p["slug"] for p in all_p], ex.map(
            lambda p: judge.judge("python", WRONG_CODE, problems.tests_for_submit(p)), all_p)))
    pool = _resume_pool(rng)
    q_apt = db.scalars(select(Question.id).where(Question.kind == "aptitude")).all()
    q_tech = db.scalars(select(Question.id).where(Question.kind == "technical")).all()
    contests = db.scalars(select(Contest).order_by(Contest.start_at)).all()
    past, live = contests[0], contests[1]
    now = datetime.utcnow()
    h = hash_password(DEMO_PASSWORD)

    def add_sub(uid, p, res, when, contest=None, code=None):
        db.add(Submission(user_id=uid, problem_slug=p["slug"], language="python", code=code or p["reference_python"],
                          verdict=res["verdict"], passed=res["passed"], total=res["total"], time_ms=res["time_ms"],
                          detail=jdump({"message": res["message"], "tests": res["tests"]}),
                          contest_id=contest.id if contest else None, created_at=when))

    for i in range(1, SAMPLE_COUNT + 1):
        ability = rng.uniform(0.35, 0.92)
        u = User(name=f"Sample Candidate {i:02d}", email=f"sample{i:02d}@sample.talenttrack.dev", password_hash=h,
                 role="candidate", is_sample=True, target_role="Software Engineer",
                 created_at=now - timedelta(days=30))
        db.add(u)
        db.flush()
        for kind, pool_ids, n_tests in (("aptitude", q_apt, rng.randint(1, 3)), ("technical", q_tech, rng.randint(1, 2))):
            for _ in range(n_tests):
                started = now - timedelta(days=rng.randint(4, 28), minutes=rng.randint(0, 600))
                att = TestAttempt(user_id=u.id, kind=kind, topic="All", difficulty="Any",
                                  question_ids=jdump(rng.sample(pool_ids, 10)), time_limit_sec=600, total=10,
                                  started_at=started)
                db.add(att)
                db.flush()
                score_attempt(db, att, _answer(rng, db, att, ability), when=started + timedelta(minutes=rng.randint(4, 9)))
        k = max(0, min(len(all_p), int(ability * 14 + rng.uniform(-3, 3))))
        weights = [3 if p["difficulty"] == "Easy" else 2 if p["difficulty"] == "Medium" else 1 for p in all_p]
        chosen = set()
        while len(chosen) < k:
            chosen.add(rng.choices(range(len(all_p)), weights)[0])
        for idx in chosen:
            p = all_p[idx]
            when = now - timedelta(days=rng.randint(4, 28), minutes=rng.randint(0, 900))
            if rng.random() < 0.35:
                add_sub(u.id, p, bad[p["slug"]], when - timedelta(minutes=7), code=WRONG_CODE)
            add_sub(u.id, p, ok[p["slug"]], when)
        for contest, frac in ((past, 0.6), (live, 0.35)):
            if rng.random() < frac:
                window = (min(contest.end_at, now) - contest.start_at).total_seconds() / 60
                for slug in json.loads(contest.problem_slugs):
                    if rng.random() < ability:
                        p = problems.get(slug)
                        minute = rng.uniform(3, max(4, window - 1))
                        if rng.random() < 0.3:
                            add_sub(u.id, p, bad[slug], contest.start_at + timedelta(minutes=minute - 2), contest, WRONG_CODE)
                        add_sub(u.id, p, ok[slug], contest.start_at + timedelta(minutes=minute), contest)
        cat = rng.choice(RESUME_CATEGORIES)
        text = rng.choice(pool[cat])
        rep = resume_svc.analyze(text)
        rep["ai"] = None
        db.add(Resume(user_id=u.id, filename=f"sample_{cat.lower()}.pdf", text=text, target_role=rep["target_role"],
                      predicted_role=rep["predicted_role"], ats_score=rep["ats_score"], skills=jdump(rep["skills"]),
                      report=jdump(rep), created_at=now - timedelta(days=rng.randint(4, 25))))
        db.commit()
    contest_svc.apply_ratings(db, past)
    for u in progress.candidates(db):
        progress.recompute(db, u, notify=False)
    print(f"seeded {SAMPLE_COUNT} sample candidates")


def run():
    init_db()
    db = SessionLocal()
    try:
        seed_questions(db)
        seed_users(db)
        seed_contests(db)
        seed_sample_cohort(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
