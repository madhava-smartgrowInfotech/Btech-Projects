"""Contest standings (solved count, then penalty minutes) and Elo-style rating updates."""
from datetime import datetime

from sqlalchemy import select

from ..db import Contest, Notification, Submission, User, jdump, jload

WRONG_PENALTY_MIN = 5
K = 80


def status(c, at=None):
    at = at or datetime.utcnow()
    return "upcoming" if at < c.start_at else "running" if at <= c.end_at else "ended"


def standings(db, c):
    subs = db.scalars(select(Submission).where(Submission.contest_id == c.id, Submission.created_at >= c.start_at,
                                               Submission.created_at <= c.end_at)
                      .order_by(Submission.created_at)).all()
    slugs = jload(c.problem_slugs, [])
    rows = {}
    for s in subs:
        r = rows.setdefault(s.user_id, {"user_id": s.user_id, "solved": 0, "penalty": 0, "problems": {}})
        p = r["problems"].setdefault(s.problem_slug, {"solved": False, "attempts": 0, "minute": None})
        if p["solved"]:
            continue
        if s.verdict == "Accepted":
            p["solved"] = True
            p["minute"] = int((s.created_at - c.start_at).total_seconds() // 60)
            r["solved"] += 1
            r["penalty"] += p["minute"] + WRONG_PENALTY_MIN * p["attempts"]
        elif s.verdict != "Compile Error":
            p["attempts"] += 1
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(list(rows)))).all()} if rows else {}
    table = sorted(rows.values(), key=lambda r: (-r["solved"], r["penalty"]))
    changes = jload(c.rating_changes, {}) or {}
    rank = 0
    prev = None
    for i, r in enumerate(table, 1):
        key = (r["solved"], r["penalty"])
        if key != prev:
            rank = i
            prev = key
        u = users.get(r["user_id"])
        r.update(rank=rank, name=u.name if u else "?", rating=u.rating if u else None, is_sample=u.is_sample if u else False,
                 rating_change=changes.get(str(r["user_id"])))
        r["problems"] = [{"slug": sl, **r["problems"].get(sl, {"solved": False, "attempts": 0, "minute": None})} for sl in slugs]
    return table


def apply_ratings(db, c):
    """Rate a finished contest once: expected vs actual pairwise score, K-factor update."""
    if c.rated or status(c) != "ended":
        return False
    table = standings(db, c)
    n = len(table)
    changes = {}
    if n >= 2:
        users = {u.id: u for u in db.scalars(select(User).where(User.id.in_([r["user_id"] for r in table]))).all()}
        for r in table:
            me = users[r["user_id"]]
            exp = sum(1 / (1 + 10 ** ((users[o["user_id"]].rating - me.rating) / 400)) for o in table if o is not r) / (n - 1)
            better = sum(1 for o in table if o["rank"] > r["rank"])
            ties = sum(1 for o in table if o["rank"] == r["rank"] and o is not r)
            actual = (better + 0.5 * ties) / (n - 1)
            changes[str(me.id)] = round(K * (actual - exp))
        for uid, d in changes.items():
            u = users[int(uid)]
            u.rating += d
            db.add(Notification(user_id=u.id, text=f"{c.title} is rated: rating {'+' if d >= 0 else ''}{d} -> {u.rating}."))
    c.rated = True
    c.rating_changes = jdump(changes)
    db.commit()
    return True


def rate_finished(db):
    for c in db.scalars(select(Contest).where(Contest.rated.is_(False), Contest.end_at < datetime.utcnow())).all():
        apply_ratings(db, c)
