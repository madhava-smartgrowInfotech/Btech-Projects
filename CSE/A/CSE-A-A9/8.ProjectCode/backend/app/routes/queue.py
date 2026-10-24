"""F6 - moderator queue: confirm or dismiss flagged accounts / clusters, decisions log, feeding retraining."""
from __future__ import annotations

from typing import Literal

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, require_moderator
from ..db import Review, User, get_db
from ..services.store import Store, get_store

router = APIRouter(prefix="/api")


class DecisionIn(BaseModel):
    target_type: Literal["account", "cluster"]
    target_id: str
    decision: Literal["confirm", "dismiss"]
    note: str = Field("", max_length=500)


def pending_counts(s: Store, reviews: list) -> dict:
    """Open items: flagged accounts without any decision, clusters without a cluster decision."""
    dec = s.decisions_map(reviews)
    decided_clusters = {r.target_id for r in reviews if r.target_type == "cluster"}
    flagged = s.accounts.index[s.accounts["flagged"]]
    return {"accounts": sum(1 for i in flagged if int(i) not in dec),
            "clusters": sum(1 for c in s.clusters if c["id"] not in decided_clusters)}


def _reviews(db: Session) -> list[Review]:
    return list(db.scalars(select(Review).order_by(Review.created_at.desc())))


@router.get("/queue")
def queue(kind: Literal["accounts", "clusters"] = "accounts", state: Literal["pending", "decided"] = "pending",
          page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
          user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_store()
    reviews = _reviews(db)
    dec = s.decisions_map(reviews)
    cluster_dec = {}
    for rv in reviews:
        if rv.target_type == "cluster" and rv.target_id not in cluster_dec:
            cluster_dec[rv.target_id] = rv.decision
    counts = pending_counts(s, reviews)
    summary = {
        "pending_accounts": counts["accounts"], "pending_clusters": counts["clusters"],
        "confirmed": sum(1 for r in reviews if r.decision == "confirm"), "dismissed": sum(1 for r in reviews if r.decision == "dismiss"),
        "labels_for_next_run": len({m for r in reviews for m in (r.members or [])}),
        "can_decide": user.role == "moderator",
    }
    if kind == "accounts":
        acc = s.accounts
        if state == "pending":
            ids = [int(i) for i in acc.index[acc["flagged"]] if int(i) not in dec]
        else:
            ids = list(dec)
        ids.sort(key=lambda i: -s.score[i])
        total = len(ids)
        sel = ids[(page - 1) * page_size: page * page_size]
        items = [{**s.node_brief(i), "display_name": acc.at[i, "display_name"], "flagged_neighbours": int(s.nb_flagged[i]),
                  "decision": dec.get(i, {}).get("decision"), "via": dec.get(i, {}).get("by")} for i in sel]
    else:
        rows = []
        for c in s.clusters:
            d = cluster_dec.get(c["id"])
            if (state == "pending") == (d is None):
                rows.append({k: c[k] for k in ("id", "size", "mean_score", "density", "kind", "peak_hour", "peak_hour_share")} | {"decision": d})
        total = len(rows)
        items = rows[(page - 1) * page_size: page * page_size]
    return {"summary": summary, "kind": kind, "state": state, "threshold": s.thr, "total": total, "page": page,
            "pages": max(1, -(-total // page_size)), "items": items}


@router.post("/queue/decisions", status_code=201)
def decide(body: DecisionIn, user: User = Depends(require_moderator), db: Session = Depends(get_db)):
    s = get_store()
    if body.target_type == "account":
        try:
            i = int(body.target_id)
        except ValueError:
            raise HTTPException(422, "Account ids are numbers.")
        if not 0 <= i < s.n:
            raise HTTPException(404, f"No account with id {i}.")
        members, score, tid = [i], float(s.score[i]), str(i)
    else:
        c = s.cluster_by_id.get(body.target_id)
        if not c:
            raise HTTPException(404, f"No cluster {body.target_id}. It may have changed after the model was retrained.")
        members, score, tid = list(c["members"]), float(c["mean_score"]), c["id"]
    rv = Review(target_type=body.target_type, target_id=tid, decision=body.decision, note=body.note.strip(),
                score=score, members=members, user_id=user.id)
    db.add(rv)
    db.commit()
    return {"id": rv.id, "target_type": rv.target_type, "target_id": rv.target_id, "decision": rv.decision,
            "affected_accounts": len(members), "at": rv.created_at.isoformat()}


@router.delete("/queue/decisions/{review_id}")
def undo(review_id: int, user: User = Depends(require_moderator), db: Session = Depends(get_db)):
    rv = db.get(Review, review_id)
    if not rv:
        raise HTTPException(404, "That decision no longer exists.")
    if rv.used_in_run is not None:
        raise HTTPException(409, "That decision was already used to train a model run and cannot be undone.")
    db.delete(rv)
    db.commit()
    return {"deleted": review_id}


@router.get("/decisions")
def decisions(limit: int = Query(100, ge=1, le=500), _: User = Depends(current_user), db: Session = Depends(get_db)):
    reviews = _reviews(db)[:limit]
    s = get_store()
    return {"items": [{
        "id": r.id, "target_type": r.target_type, "target_id": r.target_id, "decision": r.decision, "note": r.note,
        "score": r.score, "affected_accounts": len(r.members or []), "by": r.user.name, "at": r.created_at.isoformat(),
        "label": s.accounts.at[int(r.target_id), "handle"] if r.target_type == "account" and r.target_id.isdigit() and int(r.target_id) < s.n else r.target_id,
        "used_in_run": r.used_in_run,
    } for r in reviews]}
