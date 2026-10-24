"""F4 - account scoring: ranked list, per-account detail with top features, neighbourhood graph."""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Review, User, get_db
from ..services.store import C, D, get_store

router = APIRouter(prefix="/api/accounts")


def _status(row_flagged: bool, d: dict | None) -> str:
    if d:
        return "confirmed" if d["decision"] == "confirm" else "dismissed"
    return "pending" if row_flagged else "clear"


@router.get("")
def list_accounts(
    q: str = "", status: str = Query("all", pattern="^(all|pending|confirmed|dismissed|clear)$"),
    flagged_only: bool = False, cluster: str = "", sort: str = Query("score", pattern="^(score|followers|degree|age|neighbours)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    _: User = Depends(current_user), db: Session = Depends(get_db),
):
    s = get_store()
    acc = s.accounts
    dec = s.decisions_map(list(db.scalars(select(Review))))
    status_col = np.array([_status(bool(f), dec.get(int(i))) for i, f in zip(acc["id"], acc["flagged"])])
    mask = np.ones(len(acc), dtype=bool)
    if q.strip():
        mask &= acc["handle"].str.contains(q.strip().lower(), case=False, regex=False).to_numpy() | acc["display_name"].str.contains(q.strip(), case=False, regex=False).to_numpy()
    if flagged_only:
        mask &= acc["flagged"].to_numpy()
    if status != "all":
        mask &= status_col == status
    if cluster == "any":
        mask &= acc["cluster_id"].notna().to_numpy()
    elif cluster == "none":
        mask &= acc["cluster_id"].isna().to_numpy()
    elif cluster:
        mask &= (acc["cluster_id"] == cluster).to_numpy()
    idx = np.where(mask)[0]
    key = {"score": acc["score"].to_numpy(), "followers": acc["followers"].to_numpy(), "degree": s.deg,
           "age": acc["account_age_days"].to_numpy(), "neighbours": s.nb_flagged}[sort]
    idx = idx[np.argsort(key[idx], kind="stable")]
    if order == "desc":
        idx = idx[::-1]
    total = len(idx)
    page_idx = idx[(page - 1) * page_size: page * page_size]
    items = []
    for i in page_idx:
        r = acc.iloc[int(i)]
        items.append({
            "id": int(i), "handle": r["handle"], "display_name": r["display_name"], "score": float(r["score"]),
            "flagged": bool(r["flagged"]), "status": str(status_col[i]),
            "cluster_id": r["cluster_id"] if isinstance(r["cluster_id"], str) else None,
            "followers": int(r["followers"]), "following": int(r["following"]), "account_age_days": int(r["account_age_days"]),
            "degree": int(s.deg[i]), "flagged_neighbours": int(s.nb_flagged[i]),
        })
    return {"total": total, "page": page, "page_size": page_size, "pages": max(1, -(-total // page_size)),
            "threshold": s.thr, "items": items}


@router.get("/{account_id}")
def account_detail(account_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_store()
    if not 0 <= account_id < s.n:
        raise HTTPException(404, f"No account with id {account_id}.")
    r = s.accounts.iloc[account_id]
    reviews = list(db.scalars(select(Review).order_by(Review.created_at.desc())))
    dec = s.decisions_map(reviews)
    nb, kinds = s.neighbours(account_id)
    nb_scores = s.score[nb] if len(nb) else np.array([])
    ex = s.explain(account_id)
    history = [
        {"id": rv.id, "decision": rv.decision, "target_type": rv.target_type, "note": rv.note, "by": rv.user.name,
         "at": rv.created_at.isoformat()}
        for rv in reviews if account_id in (rv.members or [])
    ]
    cid = r["cluster_id"] if isinstance(r["cluster_id"], str) else None
    return {
        "id": account_id, "handle": r["handle"], "display_name": r["display_name"], "score": float(r["score"]),
        "flagged": bool(r["flagged"]), "threshold": s.thr, "status": _status(bool(r["flagged"]), dec.get(account_id)),
        "model": C.MODEL_LABELS[s.best],
        "model_scores": [{"model": m, "label": C.MODEL_LABELS[m], "score": float(s.probs[m][account_id]),
                          "flagged": bool(s.probs[m][account_id] >= (s.metrics["models"][m]["threshold"] if s.metrics else 0.5)),
                          "uses_graph": m != C.BASELINE} for m in C.ALL_MODELS],
        "profile": {
            "followers": int(r["followers"]), "following": int(r["following"]), "posts": int(r["posts"]),
            "bio_length": int(r["bio_length"]), "has_profile_pic": bool(r["has_profile_pic"]),
            "account_age_days": int(r["account_age_days"]), "peak_hour": int(r["peak_hour"]),
            "posts_per_day": float(r["posts_per_day"]), "interactions_per_week": float(r["interactions_per_week"]),
        },
        "dataset_label": "fake" if int(r["label"]) == 1 else "genuine",
        "origin": r["origin"],
        "cluster_id": cid, "cluster_size": s.cluster_by_id[cid]["size"] if cid else None,
        "explanation": ex,
        "neighbourhood": {
            "degree": int(len(nb)), "flagged": int((nb_scores >= s.thr).sum()) if len(nb) else 0,
            "mean_score": float(nb_scores.mean()) if len(nb) else 0.0,
            "injected_ties": int((kinds == 1).sum()) if len(nb) else 0,
        },
        "history": history,
    }


@router.get("/{account_id}/neighbourhood")
def neighbourhood(account_id: int, limit: int = Query(40, ge=5, le=120), _: User = Depends(current_user)):
    s = get_store()
    if not 0 <= account_id < s.n:
        raise HTTPException(404, f"No account with id {account_id}.")
    nb, _k = s.neighbours(account_id)
    order = np.argsort(-s.score[nb], kind="stable")[:limit]
    keep = {account_id, *[int(v) for v in nb[order]]}
    nodes = [{**s.node_brief(i), "ego": i == account_id} for i in sorted(keep)]
    links = [{"source": u, "target": v, "injected": bool(k)} for u, v, k in s.edge_set(keep)]
    return {"nodes": nodes, "links": links, "shown": len(keep) - 1, "total_neighbours": int(len(nb)),
            "note": "Showing the highest-scoring neighbours first." if len(nb) > limit else ""}
