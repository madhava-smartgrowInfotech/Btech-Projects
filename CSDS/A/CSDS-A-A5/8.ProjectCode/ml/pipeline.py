"""TaxSentinel pipeline: features -> JEPA deviation -> network analysis -> invoice anomalies ->
multi-layer risk -> evidence and invoice chains -> evaluation against the injected labels."""
import math
import os
import time
import warnings
from collections import Counter, defaultdict
from datetime import date

import numpy as np

from ml import jepa as J
from ml.baseline import RULES, rule_baseline
from ml.features import (FEATURE_GROUPS, FEATURE_LABELS, FEATURE_NAMES, GOODS_SECTORS, GROUP_INDEX,
                         RobustScaler, build_features, load_dataset)
from ml.graph import build_trade_graph, communities, detect_cycles, identity_clusters
from ml.metrics import prf, ranking_report

GROUPS = list(FEATURE_GROUPS)
VARIANTS = ["history"] + GROUPS
WINDOW = 3
INVOICE_FLAGS = {
    "unreported": (0.30, "not reported by the supplier in GSTR-1"),
    "no_eway": (0.30, "goods above ₹50,000 billed without an e-way bill"),
    "round_value": (0.15, "round-figure value"),
    "young_supplier": (0.20, "supplier registered less than 6 months before the invoice"),
    "shell_cluster": (0.35, "supplier belongs to a suspicious shared-identity cluster"),
    "supplier_vanished": (0.20, "supplier later stopped filing returns"),
    "ring_edge": (0.45, "part of a detected circular-trading loop"),
    "value_spike": (0.15, "far above the supplier's usual invoice value"),
}
INVOICE_FLAG_THRESHOLD = 0.5
# noisy-OR: one strong layer is enough to raise risk, agreeing layers raise it further
RISK_WEIGHTS = {"jepa": 0.75, "behaviour": 0.6, "network": 0.7, "invoice": 0.6}
FLAG_THRESHOLD = 0.5
CLUSTER_THRESHOLD = 0.4
PATTERN_LABELS = {"circular_trading": "Circular trading", "shell_entity": "Shell entity",
                  "fake_invoices": "Fake invoices / ITC from shells", "itc_spike": "ITC spike",
                  "behaviour_anomaly": "Unusual behaviour"}
ROLE_TO_PATTERN = {"circular_trading": "circular_trading", "shell_entity": "shell_entity",
                   "fake_invoice_buyer": "fake_invoices", "itc_spike": "itc_spike"}
SEV_RANK = {"high": 0, "medium": 1, "low": 2}


def inr(x):
    x = float(x)
    if abs(x) >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if abs(x) >= 1e5:
        return f"₹{x / 1e5:.2f} L"
    return f"₹{x:,.0f}"


def mlabel(m):
    return date.fromisoformat(m + "-01").strftime("%b %Y")


def fmt_feature(name, v):
    if name in ("purchase_invoices", "sales_invoices", "suppliers", "buyers"):
        return f"{math.expm1(v):.0f}"
    if name in ("outward_log", "itc_claimed_log"):
        return inr(math.expm1(v))
    if name == "itc_to_output":
        return f"{v:.2f}x"
    if name == "itc_mismatch":
        return f"{math.copysign(math.expm1(abs(v)), v) * 100:+.0f}%"
    if name == "filing_delay":
        return f"{v * 30:.0f} days"
    if name == "age_log":
        return f"{math.expm1(v):.0f} months"
    return f"{v * 100:.0f}%"


def _calibrate(log_values, centre=2.0):
    """Robust z-score against the population, squashed to 0-1 (0.5 at `centre` robust SDs)."""
    med = np.median(log_values)
    mad = np.median(np.abs(log_values - med)) * 1.4826 + 1e-9
    return 1 / (1 + np.exp(-1.5 * ((log_values - med) / mad - centre)))


def _progress(cb, stage, pct, msg=""):
    if cb:
        cb(stage, pct, msg)


def train_model(data_dir, model_path, epochs=100, seed=42, progress=None):
    ds = load_dataset(data_dir)
    F = build_features(ds)
    scaler = RobustScaler().fit(F["X"][F["present"]])
    Z = scaler.transform(F["X"])
    _, _, ctx, ctxp, cur = J.make_samples(Z, F["present"], WINDOW)
    model, info = J.train_jepa(ctx, ctxp, cur, [GROUP_INDEX[g] for g in GROUPS], WINDOW, epochs=epochs, seed=seed,
                               progress=(lambda e, n, l: e % 10 == 0 and _progress(progress, "train", 20 + 50 * e / n,
                                                                   f"epoch {e}/{n} loss {l:.4f}")))
    if model_path:
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        J.save_model(model, model_path, {"scaler": scaler.to_dict(), "feature_names": FEATURE_NAMES,
                                         "variants": VARIANTS, "train_info": info})
    info.update(features=len(FEATURE_NAMES), groups={g: FEATURE_GROUPS[g] for g in GROUPS}, seed=seed)
    return model, scaler, info


def run_pipeline(data_dir, model_path=None, train=True, epochs=100, seed=42, progress=None, save_model_to=None):
    t0 = time.time()
    _progress(progress, "features", 5, "loading data")
    ds = load_dataset(data_dir)
    tps, months, invoices = ds["taxpayers"], ds["months"], ds["invoices"]
    n, T = len(tps), len(months)
    F = build_features(ds)
    X, present = F["X"], F["present"]

    # ---------- JEPA behaviour encoder ----------
    if train:
        _progress(progress, "train", 20, "training JEPA encoder")
        model, scaler, train_info = train_model(data_dir, save_model_to, epochs, seed, progress)
    else:
        model, ck = J.load_model(model_path)
        scaler = RobustScaler.from_dict(ck["scaler"])
        train_info = ck.get("train_info", {})
    _progress(progress, "score", 72, "scoring deviations")
    Z = scaler.transform(X)
    ii, mm, ctx, ctxp, cur = J.make_samples(Z, present, WINDOW)
    errs = J.score(model, ctx, ctxp, cur)
    V = errs.shape[1]
    E = np.full((n, T, V), np.nan)
    E[ii, mm] = errs
    ratio = E / np.nanmedian(E, axis=0, keepdims=True)  # error relative to a typical taxpayer in that month
    with warnings.catch_warnings():  # months with no return are all-nan by design
        warnings.simplefilter("ignore", RuntimeWarning)
        month_ratio = np.exp(np.nanmean(np.log(ratio), axis=2))  # geometric mean over mask variants
    raw = np.array([np.mean(sorted(month_ratio[i][present[i]], reverse=True)[:2]) if present[i].any() else 1.0
                    for i in range(n)])
    logs = np.log(raw)
    j_score = _calibrate(logs)
    # behaviour-layer deviation: how badly the return figures disagree with what the
    # invoice/network layers and the taxpayer's history predict (catches one-month ITC spikes)
    b_raw = np.array([np.nanmax(ratio[i, :, 1 + GROUPS.index("behaviour")]) if present[i].any() else 1.0
                      for i in range(n)])
    b_score = _calibrate(np.log(b_raw))

    # ---------- returns as arrays ----------
    ret = {k: np.full((n, T), np.nan) for k in ("claimed", "avail", "out_tax", "cash", "outward", "delay")}
    for (i, m), r in F["returns"].items():
        ret["claimed"][i, m] = r["itc_claimed_3b"]
        ret["avail"][i, m] = r["itc_available_2b"]
        ret["out_tax"][i, m] = r["output_tax"]
        ret["cash"][i, m] = r["tax_paid_cash"]
        ret["outward"][i, m] = r["outward_taxable"]
        ret["delay"][i, m] = r["filing_delay_days"]
    reg = [date.fromisoformat(t["registration_date"]) for t in tps]
    month_dates = [date.fromisoformat(m + "-01") for m in months]
    reg_age = np.array([[(md - reg[i]).days for md in month_dates] for i in range(n)], dtype=float)
    last_present = np.array([np.nonzero(present[i])[0].max() if present[i].any() else -1 for i in range(n)])
    vanished = last_present < T - 1

    # ---------- network layer ----------
    _progress(progress, "graph", 78, "detecting rings and clusters")
    G = build_trade_graph(ds)
    purchases_total = F["purch_v"].sum(axis=1)
    cyc = detect_cycles(G, purchases_total)
    rings = cyc["rings"]
    ring_of = defaultdict(list)
    ring_edges = set()
    for r in rings:
        for v in r["nodes"]:
            ring_of[v].append(r)
        ring_edges.update(r["edges"])
    comm = communities(G, seed)
    period_start = month_dates[0]
    clusters = []
    for k, c in enumerate(identity_clusters(tps)):
        nodes = c["nodes"]
        ns = set(nodes)
        sales = sum(G[u][v]["value"] for u in nodes for v in G.successors(u))
        intra = sum(G[u][v]["value"] for u in nodes for v in G.successors(u) if v in ns)
        young = np.mean([(period_start - reg[i]).days < 365 for i in nodes])
        van = np.mean([vanished[i] for i in nodes])
        mj = float(np.mean(j_score[nodes]))
        intra_share = intra / sales if sales else 0.0
        score = 0.4 * mj + 0.2 * young + 0.2 * intra_share + 0.2 * van
        clusters.append(dict(id=f"S{k + 1:02d}", nodes=nodes, score=round(float(score), 3), mean_jepa=round(mj, 3),
                             young_share=round(float(young), 3), intra_trade_share=round(intra_share, 3),
                             vanished_share=round(float(van), 3), shared_address=c["shared_address"],
                             shared_contact=c["shared_contact"], suspicious=bool(score >= CLUSTER_THRESHOLD)))
    clusters.sort(key=lambda c: -c["score"])
    cluster_of = {v: c for c in clusters for v in c["nodes"]}
    susp_cluster_nodes = {v for c in clusters if c["suspicious"] for v in c["nodes"]}

    # ---------- invoice layer ----------
    _progress(progress, "invoices", 84, "scoring invoices")
    by_seller = defaultdict(list)
    for r in invoices:
        by_seller[r["_s"]].append(r["taxable_value"])
    seller_med = {s: float(np.median(v)) for s, v in by_seller.items()}
    goods = [t["sector"] in GOODS_SECTORS for t in tps]
    flagged_val = np.zeros((n, T))
    total_val = np.zeros((n, T))
    exposure_val = np.zeros((n, T))
    inbound, outbound = defaultdict(list), defaultdict(list)
    for r in invoices:
        s, b, m, v = r["_s"], r["_b"], r["_m"], r["taxable_value"]
        fl = []
        if not r["seller_reported"]:
            fl.append("unreported")
        if goods[s] and v >= 50000 and not r["eway_bill"]:
            fl.append("no_eway")
        if v % 10000 == 0:
            fl.append("round_value")
        if (date.fromisoformat(r["invoice_date"]) - reg[s]).days < 180:
            fl.append("young_supplier")
        if s in susp_cluster_nodes:
            fl.append("shell_cluster")
            exposure_val[b, m] += v
        if vanished[s]:
            fl.append("supplier_vanished")
        if (s, b) in ring_edges:
            fl.append("ring_edge")
        if v > 4 * seller_med[s] and v > 200000:
            fl.append("value_spike")
        sc = 1 - float(np.prod([1 - INVOICE_FLAGS[f][0] for f in fl])) if fl else 0.0
        r["anomaly"], r["flags"] = round(sc, 3), fl
        for who in (s, b):
            total_val[who, m] += v
            if sc >= INVOICE_FLAG_THRESHOLD:
                flagged_val[who, m] += v
        inbound[b].append(r["id"])
        outbound[s].append(r["id"])
    with np.errstate(invalid="ignore", divide="ignore"):
        flagged_share = np.nan_to_num(flagged_val / total_val)
        exposure = np.nan_to_num(exposure_val / F["purch_v"])
    i_score = np.minimum(1, 1.5 * flagged_share.max(axis=1))

    # ---------- combine layers ----------
    _progress(progress, "risk", 90, "combining layers")
    n_score = np.zeros(n)
    for v in range(n):
        parts = [min(1.0, 2 * exposure[v].max())]
        if ring_of[v]:
            parts.append(max(r["score"] for r in ring_of[v]))
        if v in cluster_of and cluster_of[v]["suspicious"]:
            parts.append(cluster_of[v]["score"])
        n_score[v] = max(parts)
    risk = 1 - ((1 - RISK_WEIGHTS["jepa"] * j_score) * (1 - RISK_WEIGHTS["behaviour"] * b_score)
                * (1 - RISK_WEIGHTS["network"] * n_score) * (1 - RISK_WEIGHTS["invoice"] * i_score))
    flagged = risk >= FLAG_THRESHOLD
    base_hits, base_score = rule_baseline(ret, reg_age, present)

    with np.errstate(invalid="ignore", divide="ignore"):
        year_cash_ratio = np.nansum(ret["cash"], 1) / np.maximum(np.nansum(ret["out_tax"], 1), 1)
    sector_cash = {s: float(np.median([year_cash_ratio[i] for i in range(n) if tps[i]["sector"] == s]))
                   for s in {t["sector"] for t in tps}}

    # ---------- per-taxpayer patterns and evidence ----------
    _progress(progress, "evidence", 94, "building evidence")
    names = [t["legal_name"] for t in tps]
    records, details = [], []
    for i, t in enumerate(tps):
        pm = np.nonzero(present[i])[0]
        claimed = ret["claimed"][i]
        med_claim = float(np.nanmedian(claimed)) if len(pm) else 0.0
        spike_months = [m for m in pm if claimed[m] >= 2.5 * max(med_claim, 1) and claimed[m] > 1e5
                        and claimed[m] >= 1.5 * ret["avail"][i, m]]
        in_flagged = [invoices[k] for k in inbound[i] if invoices[k]["anomaly"] >= INVOICE_FLAG_THRESHOLD]
        patterns = []
        if ring_of[i]:
            patterns.append("circular_trading")
        if i in susp_cluster_nodes and ((period_start - reg[i]).days < 365 or vanished[i]
                                        or year_cash_ratio[i] < 0.05):
            patterns.append("shell_entity")
        in_val = F["purch_v"][i].sum()
        in_flag_share = sum(r["taxable_value"] for r in in_flagged) / in_val if in_val else 0
        if "shell_entity" not in patterns and (exposure[i].max() >= 0.1 or in_flag_share >= 0.15):
            patterns.append("fake_invoices")
        if spike_months:
            patterns.append("itc_spike")
        if not patterns and j_score[i] >= 0.5:
            patterns.append("behaviour_anomaly")

        ev = []
        if len(pm):
            m = int(pm[np.nanargmax(month_ratio[i][pm])])
            gr = ratio[i, m]
            top_layer = GROUPS[int(np.nanargmax(gr[1:]))]
            others = [k for k in pm if k != m]
            own_z = np.median(Z[i, others], axis=0) if len(others) >= 2 else np.zeros(Z.shape[2])
            own_x = np.median(X[i, others], axis=0) if len(others) >= 2 else None
            diff = np.abs(Z[i, m] - own_z)
            shifts = []
            for f in np.argsort(-diff)[:3]:
                fname = FEATURE_NAMES[f]
                s = f"{FEATURE_LABELS[fname]} {fmt_feature(fname, float(X[i, m, f]))}"
                if own_x is not None:
                    s += f" (usually {fmt_feature(fname, float(own_x[f]))})"
                shifts.append(s)
            sev = "high" if j_score[i] >= 0.7 else "medium" if j_score[i] >= 0.4 else "low"
            ev.append(dict(layer="model", severity=sev, title="Deviates from learned normal behaviour",
                           detail=(f"The JEPA behaviour encoder's prediction error for {mlabel(months[m])} is "
                                   f"{month_ratio[i, m]:.1f}x a typical taxpayer-month (deviation score "
                                   f"{j_score[i]:.2f}). The {top_layer} layer is the least consistent with the rest "
                                   f"({gr[1 + GROUPS.index(top_layer)]:.1f}x); history-only prediction error "
                                   f"{gr[0]:.1f}x. Largest shifts: " + "; ".join(shifts) + "."),
                           facts=dict(month=months[m], error_ratio=round(float(month_ratio[i, m]), 2),
                                      jepa_score=round(float(j_score[i]), 3), layer=top_layer)))
        mism = [(m, claimed[m], ret["avail"][i, m]) for m in pm
                if claimed[m] > 1.2 * ret["avail"][i, m] and claimed[m] - ret["avail"][i, m] > 50000]
        if mism:
            excess = sum(c - a for _, c, a in mism)
            top = sorted(mism, key=lambda x: -(x[1] - x[2]))[:3]
            ev.append(dict(layer="behaviour", severity="high" if excess > 1e6 else "medium",
                           title="ITC claimed exceeds GSTR-2B",
                           detail=f"ITC claimed in GSTR-3B exceeded the credit available in GSTR-2B in {len(mism)} "
                                  f"month(s), by {inr(excess)} in total. " + "; ".join(
                               f"{mlabel(months[m])}: claimed {inr(c)} vs {inr(a)} available" for m, c, a in top) + ".",
                           facts=dict(months=[months[m] for m, _, _ in mism], excess=round(excess))))
        if spike_months:
            ev.append(dict(layer="behaviour", severity="high", title="Abnormal spike in ITC claimed",
                           detail="; ".join(f"{mlabel(months[m])}: {inr(claimed[m])} claimed, "
                                            f"{claimed[m] / max(med_claim, 1):.1f}x the taxpayer's median month "
                                            f"({inr(med_claim)})" for m in spike_months) + ".",
                           facts=dict(months=[months[m] for m in spike_months], median_claim=round(med_claim))))
        sc_med = sector_cash[t["sector"]]
        out_total = float(np.nansum(ret["out_tax"][i]))
        if out_total > 2e5 and year_cash_ratio[i] < 0.3 * sc_med:
            ev.append(dict(layer="behaviour", severity="high" if year_cash_ratio[i] < 0.02 else "medium",
                           title="Almost no tax paid in cash",
                           detail=f"Paid {year_cash_ratio[i] * 100:.1f}% of its {inr(out_total)} output tax in cash "
                                  f"over the period; the {t['sector'].replace('_', ' ')} median is "
                                  f"{sc_med * 100:.0f}%. The rest was set off with ITC.",
                           facts=dict(cash_ratio=round(float(year_cash_ratio[i]), 4), sector_median=round(sc_med, 4))))
        if in_flagged:
            reasons = Counter(f for r in in_flagged for f in r["flags"])
            sups = Counter(r["seller_gstin"] for r in in_flagged)
            itc = sum(r["tax_amount"] for r in in_flagged)
            ev.append(dict(layer="invoice", severity="high" if itc > 5e5 else "medium",
                           title="Suspicious purchase invoices",
                           detail=f"{len(in_flagged)} purchase invoices worth "
                                  f"{inr(sum(r['taxable_value'] for r in in_flagged))} carry ITC of {inr(itc)} "
                                  f"and score as anomalous. Most common signals: " + ", ".join(
                               f"{INVOICE_FLAGS[f][1]} ({c})" for f, c in reasons.most_common(3)) +
                                  f". From {len(sups)} supplier(s), chiefly " + ", ".join(
                               names[ds['idx'][g]] for g, _ in sups.most_common(2)) + ".",
                           facts=dict(count=len(in_flagged), itc=round(itc), invoice_ids=[r["id"] for r in in_flagged][:20])))
        out_flagged = [invoices[k] for k in outbound[i] if invoices[k]["anomaly"] >= INVOICE_FLAG_THRESHOLD]
        if out_flagged:
            buyers = Counter(r["buyer_gstin"] for r in out_flagged)
            ev.append(dict(layer="invoice", severity="high" if len(out_flagged) >= 5 else "medium",
                           title="Suspicious sales invoices issued",
                           detail=f"Issued {len(out_flagged)} anomalous invoices worth "
                                  f"{inr(sum(r['taxable_value'] for r in out_flagged))}, passing "
                                  f"{inr(sum(r['tax_amount'] for r in out_flagged))} of ITC to {len(buyers)} buyer(s).",
                           facts=dict(count=len(out_flagged))))
        for r in ring_of[i]:
            path = " -> ".join(names[v] for v in r["best_cycle"] + [r["best_cycle"][0]])
            ev.append(dict(layer="network", severity="high" if r["score"] >= 0.5 else "medium",
                           title=f"Member of circular-trading ring {r['id']}",
                           detail=f"Loop {path}: {inr(r['value'])} moved around the ring, the whole loop traded in "
                                  f"{len(r['common_months'])} common month(s) and edge values stay within "
                                  f"{(1 - r['balance']) * 100:.0f}% of each other (ring score {r['score']:.2f}).",
                           facts=dict(ring=r["id"], value=round(r["value"]), score=r["score"])))
        c = cluster_of.get(i)
        if c and (c["suspicious"] or len(c["nodes"]) >= 3):
            peers = [names[v] for v in c["nodes"] if v != i]
            link = " and ".join(x for x, ok in (("address", c["shared_address"]), ("contact number",
                                                                                   c["shared_contact"])) if ok)
            ev.append(dict(layer="network", severity="high" if c["suspicious"] else "low",
                           title=f"Shares {link} with {len(peers)} other registration(s)",
                           detail=f"Cluster {c['id']} ({', '.join(peers[:4])}{'...' if len(peers) > 4 else ''}): "
                                  f"{c['young_share'] * 100:.0f}% registered within the last year, "
                                  f"{c['vanished_share'] * 100:.0f}% stopped filing, "
                                  f"{c['intra_trade_share'] * 100:.0f}% of their sales are to each other "
                                  f"(cluster score {c['score']:.2f}).",
                           facts=dict(cluster=c["id"], score=c["score"])))
        if exposure[i].max() >= 0.05 and i not in susp_cluster_nodes:
            m = int(np.argmax(exposure[i]))
            ev.append(dict(layer="network", severity="high" if exposure[i].max() >= 0.2 else "medium",
                           title="Buys from a suspicious shell cluster",
                           detail=f"In {mlabel(months[m])}, {exposure[i, m] * 100:.0f}% of purchases came from "
                                  f"suppliers in a suspicious shared-identity cluster.",
                           facts=dict(month=months[m], share=round(float(exposure[i, m]), 3))))
        if vanished[i] and len(pm):
            ev.append(dict(layer="behaviour", severity="medium", title="Stopped filing returns",
                           detail=f"Last return filed for {mlabel(months[last_present[i]])}; no returns after that.",
                           facts=dict(last_month=months[last_present[i]])))
        young_big = [m for m in pm if reg_age[i, m] < 180 and ret["outward"][i, m] > 2e6]
        if young_big:
            ev.append(dict(layer="behaviour", severity="medium", title="High turnover soon after registration",
                           detail=f"Reported {inr(np.nansum(ret['outward'][i, young_big]))} of outward supplies in its "
                                  f"first six months after registering on {t['registration_date']}.",
                           facts=dict(months=[months[m] for m in young_big])))
        ev.sort(key=lambda e: SEV_RANK[e["severity"]])
        for k, e in enumerate(ev):
            e["id"] = f"E{k + 1}"

        rec = dict(idx=i, gstin=t["gstin"], legal_name=t["legal_name"], sector=t["sector"], state=t["state"],
                   constitution=t["constitution"], registration_date=t["registration_date"],
                   risk=round(float(risk[i]), 4), jepa=round(float(j_score[i]), 4),
                   behaviour=round(float(b_score[i]), 4),
                   network=round(float(n_score[i]), 4), invoice=round(float(i_score[i]), 4),
                   flagged=bool(flagged[i]), patterns=patterns, rules=base_hits[i],
                   rings=[r["id"] for r in ring_of[i]], cluster=c["id"] if c else None, community=int(comm[i]),
                   itc_claimed=round(float(np.nansum(claimed))), itc_at_risk=round(float(
                       sum(r["tax_amount"] for r in in_flagged) + sum(max(0, c_ - a) for _, c_, a in mism))),
                   label=dict(is_fraud=t["is_fraud"], roles=t["fraud_roles"]))
        records.append(rec)
        monthly = [dict(month=months[m], present=bool(present[i, m]),
                        **({k: (None if np.isnan(ret[k][i, m]) else round(float(ret[k][i, m]), 2))
                            for k in ("outward", "out_tax", "avail", "claimed", "cash", "delay")}),
                        deviation=None if np.isnan(month_ratio[i, m]) else round(float(month_ratio[i, m]), 3),
                        layers={VARIANTS[k]: None if np.isnan(ratio[i, m, k]) else round(float(ratio[i, m, k]), 3)
                                for k in range(V)}) for m in range(T)]
        details.append(dict(evidence=ev, monthly=monthly, address=t["address"], contact_id=t["contact_id"],
                            inbound=inbound[i], outbound=outbound[i]))

    order = np.argsort(-risk, kind="stable")
    rank = np.empty(n, dtype=int)
    rank[order] = np.arange(1, n + 1)
    for r in records:
        r["rank"] = int(rank[r["idx"]])

    # ---------- invoice chains ----------
    chains = []
    for r in rings:
        inv_ids = [k for u, v in r["edges"] for k in G[u][v]["invoices"]]
        mem_risk = float(np.mean(risk[r["nodes"]]))
        chains.append(dict(id=f"CH-{r['id']}", type="circular_trading", ring=r["id"], nodes=r["nodes"],
                           path=r["best_cycle"] + [r["best_cycle"][0]], invoice_ids=inv_ids,
                           value=round(r["value"]), itc=round(r["tax"]), months=[months[m] for m in r["common_months"]],
                           score=round(0.6 * r["score"] + 0.4 * mem_risk, 4),
                           summary=f"{len(r['nodes'])}-party loop, {len(inv_ids)} invoices, balance {r['balance']:.2f}"))
    for c in clusters:
        if not c["suspicious"]:
            continue
        inv_ids = [k for u in c["nodes"] for v in G.successors(u) for k in G[u][v]["invoices"]]
        if not inv_ids:
            continue
        vals = [invoices[k] for k in inv_ids]
        tot = sum(x["taxable_value"] for x in vals)
        fshare = sum(x["taxable_value"] for x in vals if x["anomaly"] >= INVOICE_FLAG_THRESHOLD) / tot
        buyers = sorted({x["_b"] for x in vals} - set(c["nodes"]))
        chains.append(dict(id=f"CH-{c['id']}", type="shell_supply", cluster=c["id"], nodes=c["nodes"] + buyers,
                           path=c["nodes"], beneficiaries=buyers, invoice_ids=inv_ids, value=round(tot),
                           itc=round(sum(x["tax_amount"] for x in vals)),
                           months=sorted({x["month"] for x in vals}), score=round(0.6 * c["score"] + 0.4 * fshare, 4),
                           summary=f"{len(c['nodes'])} linked registrations billing {len(buyers)} buyer(s), "
                                   f"{fshare * 100:.0f}% of invoice value anomalous"))
    chains.sort(key=lambda c: -c["score"])
    for k, c in enumerate(chains):
        c["rank"] = k + 1
        lab = [invoices[x]["is_fraud"] for x in c["invoice_ids"]]
        c["label_fraud_share"] = round(sum(lab) / len(lab), 3) if lab else 0

    # ---------- evaluation against injected labels ----------
    y = np.array([t["is_fraud"] for t in tps])
    evaluation = evaluate(y, risk, j_score, b_score, n_score, i_score, flagged, base_score, base_hits, tps, records, invoices,
                          rings, chains, ds["meta"], names_idx=ds["idx"])

    edges = [dict(source=u, target=v, value=round(d["value"]), tax=round(d["tax"]), count=d["count"],
                  months=len(d["months"]), unmatched=round(d["unmatched"]), ring=(u, v) in ring_edges)
             for u, v, d in G.edges(data=True)]
    stats = dict(taxpayers=n, invoices=len(invoices), returns=len(ds["returns"]), months=months,
                 flagged=int(flagged.sum()), rings=len(rings), suspicious_clusters=sum(c["suspicious"] for c in clusters),
                 chains=len(chains), flagged_invoices=sum(r["anomaly"] >= INVOICE_FLAG_THRESHOLD for r in invoices),
                 itc_claimed=round(float(np.nansum(ret["claimed"]))),
                 itc_at_risk=round(sum(r["itc_at_risk"] for r in records if r["flagged"])),
                 pattern_counts=dict(Counter(p for r in records if r["flagged"] for p in r["patterns"])),
                 cycles_scanned=cyc["n_cycles_scanned"], seconds=round(time.time() - t0, 1))
    _progress(progress, "done", 100, "complete")
    return dict(meta=ds["meta"], stats=stats, taxpayers=records, details=details, invoices=invoices, edges=edges,
                rings=rings, clusters=clusters, chains=chains, evaluation=evaluation, train_info=train_info,
                config=dict(risk_weights=RISK_WEIGHTS, flag_threshold=FLAG_THRESHOLD, window=WINDOW,
                            invoice_flags={k: v[0] for k, v in INVOICE_FLAGS.items()},
                            invoice_flag_threshold=INVOICE_FLAG_THRESHOLD, cluster_threshold=CLUSTER_THRESHOLD,
                            rules=RULES, pattern_labels=PATTERN_LABELS))


def _nor(j=0, bsc=0, nsc=0, isc=0):
    w = RISK_WEIGHTS
    return 1 - (1 - w["jepa"] * j) * (1 - w["behaviour"] * bsc) * (1 - w["network"] * nsc) * (1 - w["invoice"] * isc)


def evaluate(y, risk, j, bsc, nsc, isc, flagged, base_score, base_hits, tps, records, invoices, rings, chains, meta,
             names_idx):
    n_pos = int(y.sum())
    ks = sorted({10, 25, 50, n_pos})
    base_flag = np.array([bool(h) for h in base_hits])
    out = dict(n_taxpayers=len(y), n_fraud=n_pos, ks=ks)
    out["taxpayer"] = dict(
        model=dict(**ranking_report(y, risk, ks), at_threshold=prf(y, flagged)),
        rule_baseline=dict(**ranking_report(y, base_score, ks), at_threshold=prf(y, base_flag)),
        ablation={
            "jepa_only": dict(**ranking_report(y, _nor(j, bsc), ks), at_threshold=prf(y, _nor(j, bsc) >= 0.5)),
            "graph_and_invoice_only": dict(**ranking_report(y, _nor(nsc=nsc, isc=isc), ks),
                                           at_threshold=prf(y, _nor(nsc=nsc, isc=isc) >= 0.5)),
            "without_invoice_layer": dict(**ranking_report(y, _nor(j, bsc, nsc), ks)),
            "full_model": dict(**ranking_report(y, risk, ks)),
        })
    per = {}
    for role, pat in ROLE_TO_PATTERN.items():
        idx = [i for i, t in enumerate(tps) if role in t["fraud_roles"]]
        if not idx:
            continue
        per[role] = dict(count=len(idx), model_recall=round(float(np.mean(flagged[idx])), 4),
                         baseline_recall=round(float(np.mean(base_flag[idx])), 4),
                         pattern_named=round(float(np.mean([pat in records[i]["patterns"] for i in idx])), 4))
    out["per_pattern"] = per
    yi = np.array([r["is_fraud"] for r in invoices])
    si = np.array([r["anomaly"] for r in invoices])
    out["invoice"] = dict(
        n_invoices=len(yi), n_fraud=int(yi.sum()),
        model=dict(at_threshold=prf(yi, si >= INVOICE_FLAG_THRESHOLD),
                   **ranking_report(yi, si, sorted({100, 500, int(yi.sum())}))),
        rule_baseline=dict(at_threshold=prf(yi, np.array([not r["seller_reported"] for r in invoices])),
                           rule="invoice not reported by the supplier in GSTR-1 (2B mismatch)"))
    # rings: an injected ring is recovered when one detected ring covers at least 80% of its members
    detected = [set(r["nodes"]) for r in rings]
    rec = []
    for r in meta.get("rings", []):
        mem = {names_idx[g] for g in r["members"]}
        rec.append(any(len(mem & d) >= 0.8 * len(mem) for d in detected))
    fraud_nodes = {i for i, t in enumerate(tps) if t["is_fraud"]}
    out["rings"] = dict(injected=len(rec), recovered=int(sum(rec)),
                        recall=round(sum(rec) / len(rec), 4) if rec else None, detected=len(rings),
                        detected_with_fraud_members=sum(1 for d in detected if d & fraud_nodes),
                        detected_without_fraud_members=sum(1 for d in detected if not d & fraud_nodes))
    top = chains[:10]
    out["chains"] = dict(total=len(chains),
                         precision_top10=round(float(np.mean([c["label_fraud_share"] >= 0.5 for c in top])), 4)
                         if top else None)
    return out
