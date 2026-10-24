"""F5 - botnet clusters and the interactive graph view."""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Review, User, get_db
from ..services.store import get_store

router = APIRouter(prefix="/api/clusters")

SUMMARY_KEYS = ("id", "rank", "kind", "size", "mean_score", "flagged_share", "density", "internal_edges", "peak_hour",
                "peak_hour_share", "created_span_days", "median_posts_per_day", "median_account_age_days")


def _cluster_status(cid: str, reviews) -> str:
    for rv in reviews:                      # newest first
        if rv.target_type == "cluster" and rv.target_id == cid:
            return "confirmed" if rv.decision == "confirm" else "dismissed"
    return "pending"


@router.get("")
def list_clusters(_: User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_store()
    reviews = list(db.scalars(select(Review).order_by(Review.created_at.desc())))
    return {"threshold": s.thr, "items": [{**{k: c[k] for k in SUMMARY_KEYS}, "status": _cluster_status(c["id"], reviews)} for c in s.clusters]}


@router.get("/{cluster_id}")
def cluster_detail(cluster_id: str, _: User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_store()
    c = s.cluster_by_id.get(cluster_id)
    if not c:
        raise HTTPException(404, f"No cluster {cluster_id}. It may have changed after the model was retrained.")
    reviews = list(db.scalars(select(Review).order_by(Review.created_at.desc())))
    dec = s.decisions_map(reviews)
    members = c["members"]
    mset = set(members)
    # real accounts that members reach into - the audience a botnet is trying to influence
    targets = {}
    for m in members:
        nb, _k = s.neighbours(m)
        for v in nb:
            if int(v) not in mset:
                targets[int(v)] = targets.get(int(v), 0) + 1
    reach = sorted(targets.items(), key=lambda kv: -kv[1])
    items = []
    for m in members:
        b = s.node_brief(m)
        items.append({**b, "status": dec[m]["decision"] if m in dec else "pending",
                      "inside_ties": int(sum(1 for v in s.neighbours(m)[0] if int(v) in mset))})
    items.sort(key=lambda x: -x["score"])
    nodes = [{**s.node_brief(m), "ego": False} for m in members]
    links = [{"source": u, "target": v, "injected": bool(k)} for u, v, k in s.edge_set(mset)]
    detail = {k: v for k, v in c.items() if k != "members"}
    return {
        **detail, "status": _cluster_status(cluster_id, reviews), "threshold": s.thr, "members": items,
        "graph": {"nodes": nodes, "links": links},
        "reach": {"accounts": len(targets), "most_targeted": [{**s.node_brief(i), "ties_from_cluster": n} for i, n in reach[:5]]},
        "headline": _headline(c),
    }


def _headline(c: dict) -> str:
    if c["kind"] == "coordinated":
        return (f"{c['size']} accounts tied to each other ({c['density']:.0%} of possible ties), "
                f"{c['peak_hour_share']:.0%} most active around {c['peak_hour']:02d}:00, created within about {max(c['created_span_days'], 1)} days of each other.")
    return (f"{c['size']} suspicious accounts with similar profiles but almost no ties between them ({c['density']:.1%}) - "
            "look like independent spammers rather than one coordinated network.")
