"""Dataset insights computed from actual loaded data."""
from __future__ import annotations

import numpy as np


def compute_insights(df) -> dict:
    total = int(len(df))
    s = int((df["label"] == 1).sum())
    f = total - s
    ind = df.groupby("industry_type")["label"].agg(["mean", "count"]).sort_values("count", ascending=False).head(12)
    industries = [{"industry": str(i), "success_rate": round(float(r["mean"]), 4), "count": int(r["count"])}
                  for i, r in ind.iterrows()]
    states = df.groupby("state")["label"].agg(["mean", "count"]).sort_values("count", ascending=False).head(10)
    states_l = [{"state": str(i), "success_rate": round(float(r["mean"]), 4), "count": int(r["count"])}
                for i, r in states.iterrows()]
    fund_s = float(np.median(df.loc[df["label"] == 1, "funding_total_usd"].fillna(0))) if s else 0.0
    fund_f = float(np.median(df.loc[df["label"] == 0, "funding_total_usd"].fillna(0))) if f else 0.0
    corr = {}
    for c in ["relationships", "funding_rounds", "funding_total_usd", "milestones", "avg_participants"]:
        try:
            corr[c] = round(float(df[c].fillna(0).corr(df["label"])), 4)
        except Exception:
            corr[c] = 0.0
    return {
        "total": total, "success": s, "failure": f,
        "success_rate": round(s / total, 4) if total else 0,
        "industries": industries, "states": states_l,
        "median_funding_success": fund_s, "median_funding_failure": fund_f,
        "correlations": corr,
    }
