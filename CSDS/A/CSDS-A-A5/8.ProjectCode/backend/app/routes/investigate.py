"""Risk ranking, taxpayer profiles, invoice chains and the fraud-ring graph."""
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Explanation, User, get_db
from .pipeline import _brief, _chain_brief, state

router = APIRouter(prefix="/api", tags=["investigate"])
INV_FIELDS = ("id", "invoice_no", "invoice_date", "seller_gstin", "buyer_gstin", "taxable_value", "tax_amount",
              "gst_rate", "eway_bill", "seller_reported", "anomaly", "flags")


def _tp(s, gstin):
    i = s["_index"].get(gstin)
    if i is None:
        raise HTTPException(404, f"No taxpayer with GSTIN {gstin} in the current ecosystem")
    return i


def _inv(s, r):
    tps, idx = s["taxpayers"], s["_index"]
    return {k: r[k] for k in INV_FIELDS} | {"seller_name": tps[idx[r["seller_gstin"]]]["legal_name"],
                                            "buyer_name": tps[idx[r["buyer_gstin"]]]["legal_name"],
                                            "label_fraud": r["is_fraud"]}


def _names(s, nodes, risk=False):
    tps = s["taxpayers"]
    return [{"gstin": tps[v]["gstin"], "legal_name": tps[v]["legal_name"]} |
            ({"risk": tps[v]["risk"]} if risk else {}) for v in nodes]


@router.get("/taxpayers")
def taxpayers(q: str = "", pattern: str = "", flagged: bool | None = None, sector: str = "",
              sort: str = "risk", limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
              user: User = Depends(current_user)):
    s = state()
    rows = s["taxpayers"]
    ql = q.lower().strip()
    if ql:
        rows = [t for t in rows if ql in t["legal_name"].lower() or ql in t["gstin"].lower()]
    if pattern:
        rows = [t for t in rows if pattern in t["patterns"]]
    if flagged is not None:
        rows = [t for t in rows if t["flagged"] == flagged]
    if sector:
        rows = [t for t in rows if t["sector"] == sector]
    key = {"risk": lambda t: -t["risk"], "jepa": lambda t: -t["jepa"], "network": lambda t: -t["network"],
           "invoice": lambda t: -t["invoice"], "itc": lambda t: -t["itc_at_risk"], "name": lambda t: t["legal_name"]}
    rows = sorted(rows, key=key.get(sort, key["risk"]))
    return {"total": len(rows), "items": [_brief(t) | {"rules": t["rules"], "rings": t["rings"]}
                                          for t in rows[offset:offset + limit]]}


@router.get("/taxpayers/{gstin}")
def taxpayer(gstin: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    s = state()
    i = _tp(s, gstin)
    t, d = s["taxpayers"][i], s["details"][i]
    tps, inv = s["taxpayers"], s["invoices"]
    partners = defaultdict(lambda: {"bought": 0.0, "sold": 0.0})
    for k in d["inbound"]:
        partners[inv[k]["_s"]]["bought"] += inv[k]["taxable_value"]
    for k in d["outbound"]:
        partners[inv[k]["_b"]]["sold"] += inv[k]["taxable_value"]
    top_partners = sorted(partners.items(), key=lambda kv: -(kv[1]["bought"] + kv[1]["sold"]))[:12]
    flagged_inv = sorted((inv[k] for k in d["inbound"] + d["outbound"]), key=lambda r: -r["anomaly"])
    flagged_inv = [_inv(s, r) for r in flagged_inv if r["anomaly"] >= s["config"]["invoice_flag_threshold"]][:40]
    rings = [{k: r[k] for k in ("id", "score", "balance", "value", "tax", "n_cycles")} |
             {"members": _names(s, r["nodes"]), "loop": _names(s, r["best_cycle"])}
             for r in s["rings"] if r["id"] in t["rings"]]
    cluster = next((c for c in s["clusters"] if c["id"] == t["cluster"]), None)
    if cluster:
        cluster = {k: v for k, v in cluster.items() if k != "nodes"} | {"members": _names(s, cluster["nodes"], True)}
    expl = db.scalar(select(Explanation).where(Explanation.run_key == s["run_key"], Explanation.gstin == gstin)
                     .order_by(Explanation.id.desc()))
    return {
        "taxpayer": t | {"address": d["address"], "contact_id": d["contact_id"]},
        "evidence": d["evidence"], "monthly": d["monthly"], "rules": {r: s["config"]["rules"][r] for r in t["rules"]},
        "partners": [{"gstin": tps[v]["gstin"], "legal_name": tps[v]["legal_name"], "risk": tps[v]["risk"],
                      "bought_from": round(p["bought"]), "sold_to": round(p["sold"])} for v, p in top_partners],
        "flagged_invoices": flagged_inv, "rings": rings, "cluster": cluster,
        "invoice_counts": {"inbound": len(d["inbound"]), "outbound": len(d["outbound"])},
        "pattern_labels": s["config"]["pattern_labels"], "explanation": expl_out(expl),
    }


def expl_out(e):
    if not e:
        return None
    return {"text": e.text, "model": e.model, "quality": e.quality, "created_at": e.created_at}


@router.get("/chains")
def chains(user: User = Depends(current_user)):
    s = state()
    return [_chain_brief(s, c) | {"label_fraud_share": c["label_fraud_share"]} for c in s["chains"]]


@router.get("/chains/{chain_id}")
def chain(chain_id: str, user: User = Depends(current_user)):
    s = state()
    c = next((c for c in s["chains"] if c["id"] == chain_id), None)
    if not c:
        raise HTTPException(404, "Chain not found")
    tps = s["taxpayers"]
    invs = sorted((s["invoices"][k] for k in c["invoice_ids"]), key=lambda r: r["invoice_date"])
    return _chain_brief(s, c) | {
        "label_fraud_share": c["label_fraud_share"],
        "parties": [_brief(tps[v]) for v in c["nodes"]],
        "invoices": [_inv(s, r) for r in invs[:150]], "invoices_total": len(invs)}


@router.get("/structures")
def structures(user: User = Depends(current_user)):
    s = state()
    return {"rings": [{k: r[k] for k in ("id", "score", "balance", "value", "tax", "n_cycles")} |
                      {"months": len(r["common_months"]), "members": _names(s, r["nodes"])} for r in s["rings"]],
            "clusters": [{k: c[k] for k in ("id", "score", "suspicious", "young_share", "vanished_share",
                                            "intra_trade_share", "shared_address", "shared_contact")} |
                         {"members": _names(s, c["nodes"])} for c in s["clusters"]
                         if c["suspicious"] or len(c["nodes"]) > 2]}


@router.get("/graph")
def graph(focus: str = "", ring: str = "", cluster: str = "", chain: str = "", user: User = Depends(current_user)):
    s = state()
    tps, edges = s["taxpayers"], s["edges"]
    highlight = set()
    if focus:
        i = _tp(s, focus)
        weight = defaultdict(float)
        for e in edges:
            if e["source"] == i:
                weight[e["target"]] += e["value"]
            elif e["target"] == i:
                weight[e["source"]] += e["value"]
        nodes = {i} | {v for v, _ in sorted(weight.items(), key=lambda kv: -kv[1])[:14]}
        for r in s["rings"]:
            if i in r["nodes"]:
                nodes |= set(r["nodes"])
                highlight |= set(map(tuple, r["edges"]))
        for c in s["clusters"]:
            if i in c["nodes"]:
                nodes |= set(c["nodes"])
    elif ring:
        r = next((r for r in s["rings"] if r["id"] == ring), None)
        if not r:
            raise HTTPException(404, "Ring not found")
        nodes, highlight = set(r["nodes"]), set(map(tuple, r["edges"]))
    elif cluster:
        c = next((c for c in s["clusters"] if c["id"] == cluster), None)
        if not c:
            raise HTTPException(404, "Cluster not found")
        nodes = set(c["nodes"]) | {e["target"] for e in edges if e["source"] in c["nodes"]}
    elif chain:
        c = next((c for c in s["chains"] if c["id"] == chain), None)
        if not c:
            raise HTTPException(404, "Chain not found")
        nodes = set(c["nodes"])
        if c["type"] == "circular_trading":
            highlight = set(map(tuple, next(r for r in s["rings"] if r["id"] == c["ring"])["edges"]))
    else:  # fraud network overview: every ring, suspicious cluster and flagged taxpayer
        nodes = {v for r in s["rings"] for v in r["nodes"]}
        nodes |= {v for c in s["clusters"] if c["suspicious"] for v in c["nodes"]}
        nodes |= {t["idx"] for t in tps if t["flagged"]}
        highlight = {tuple(e) for r in s["rings"] for e in r["edges"]}
    member_of = defaultdict(list)
    for r in s["rings"]:
        for v in r["nodes"]:
            member_of[v].append(r["id"])
    cl = {v: c["id"] for c in s["clusters"] if c["suspicious"] for v in c["nodes"]}
    return {
        "nodes": [{"id": tps[v]["gstin"], "name": tps[v]["legal_name"], "risk": tps[v]["risk"],
                   "flagged": tps[v]["flagged"], "sector": tps[v]["sector"], "patterns": tps[v]["patterns"],
                   "community": tps[v]["community"], "rings": member_of[v], "cluster": cl.get(v),
                   "focus": tps[v]["gstin"] == focus} for v in sorted(nodes)],
        "links": [{"source": tps[e["source"]]["gstin"], "target": tps[e["target"]]["gstin"], "value": e["value"],
                   "count": e["count"], "months": e["months"],
                   "ring": (e["source"], e["target"]) in highlight} for e in edges
                  if e["source"] in nodes and e["target"] in nodes]}
