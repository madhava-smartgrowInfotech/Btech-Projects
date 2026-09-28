"""Traditional rule-based GST checks, used as the comparison baseline.

These are the threshold checks a return-scrutiny desk typically runs; they look at one
taxpayer's own returns and have no notion of learned behaviour or of the trade network.
"""
import numpy as np

RULES = {
    "R1": "ITC claimed in GSTR-3B exceeds GSTR-2B by more than 20% (and ₹50,000)",
    "R2": "Registered under 6 months with monthly turnover above ₹50 lakh",
    "R3": "Output tax above ₹1 lakh but under 1% paid in cash for 3+ months",
    "R4": "ITC claimed jumps more than 3x month over month (above ₹1 lakh)",
    "R5": "Stopped filing returns before the end of the period",
}


def rule_baseline(ret, reg_age_days, present):
    """ret: dict of (n, T) arrays with nan where no return. Returns hits (list of rule ids) and a rank score."""
    claimed, avail, out_tax, cash, outward = (ret[k] for k in ("claimed", "avail", "out_tax", "cash", "outward"))
    n, T = claimed.shape
    hits, score = [], np.zeros(n)
    with np.errstate(invalid="ignore", divide="ignore"):
        r1 = (claimed > 1.2 * avail) & (claimed - avail > 50000)
        r2 = (reg_age_days < 180) & (outward > 5e6)
        low_cash = (out_tax > 1e5) & (cash < 0.01 * out_tax)
        prev = np.concatenate([np.full((n, 1), np.nan), claimed[:, :-1]], axis=1)
        r4 = (claimed > 3 * prev) & (claimed > 1e5)
        excess = np.nan_to_num((claimed - avail) / (avail + 1e4), nan=0)
    for i in range(n):
        h = []
        if r1[i].any():
            h.append("R1")
        if r2[i].any():
            h.append("R2")
        if low_cash[i].sum() >= 3:
            h.append("R3")
        if r4[i].any():
            h.append("R4")
        pm = np.nonzero(present[i])[0]
        if len(pm) and pm.max() < T - 1:
            h.append("R5")
        hits.append(h)
        # rank by number of rules hit, ties broken by the largest ITC excess ratio
        score[i] = len(h) + min(float(np.max(excess[i])), 50) / 100
    return hits, score
