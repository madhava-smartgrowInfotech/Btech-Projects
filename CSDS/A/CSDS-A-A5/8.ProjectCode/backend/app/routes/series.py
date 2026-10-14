"""Read-only monthly series for the whole ecosystem (feeds the dashboard sparklines)."""
from collections import defaultdict

from fastapi import APIRouter, Depends

from ..auth import current_user
from ..db import User
from .pipeline import state

router = APIRouter(prefix="/api", tags=["series"])
_cache = {}


@router.get("/overview/monthly")
def monthly(user: User = Depends(current_user)):
    s = state()
    if s["run_key"] in _cache:
        return _cache[s["run_key"]]
    months = s["stats"]["months"]
    thr = s["config"]["invoice_flag_threshold"]
    inv = defaultdict(lambda: {"invoices": 0, "value": 0.0, "flagged_invoices": 0})
    for r in s["invoices"]:
        m = inv[r["month"]]
        m["invoices"] += 1
        m["value"] += r["taxable_value"]
        m["flagged_invoices"] += r["anomaly"] >= thr
    ret = defaultdict(lambda: {"returns": 0, "itc_claimed": 0.0, "itc_available": 0.0, "flagged_claimed": 0.0,
                               "flagged_filers": 0})
    for t, d in zip(s["taxpayers"], s["details"]):
        for row in d["monthly"]:
            if not row.get("present"):
                continue
            m = ret[row["month"]]
            m["returns"] += 1
            m["itc_claimed"] += row.get("claimed") or 0
            m["itc_available"] += row.get("avail") or 0
            if t["flagged"]:
                m["flagged_claimed"] += row.get("claimed") or 0
                m["flagged_filers"] += 1
    out = {"run_key": s["run_key"], "months": [
        {"month": mo, **inv[mo], **ret[mo], "value": round(inv[mo]["value"]),
         "itc_claimed": round(ret[mo]["itc_claimed"]), "itc_available": round(ret[mo]["itc_available"]),
         "flagged_claimed": round(ret[mo]["flagged_claimed"])} for mo in months]}
    _cache.clear()
    _cache[s["run_key"]] = out
    return out
