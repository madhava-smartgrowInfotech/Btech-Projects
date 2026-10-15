"""Result charts for the documents, drawn from models/forecast_metrics.json, results/*.json and data/*.csv.

    python scripts/make_result_charts.py        ->  docs/charts/*.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
FM = json.loads((ROOT / "models" / "forecast_metrics.json").read_text())
CMP = json.loads((ROOT / "results" / "comparison.json").read_text())
ROL = json.loads((ROOT / "results" / "rolling.json").read_text())
SCAL = json.loads((ROOT / "results" / "scalability.json").read_text())
DEM = pd.read_csv(ROOT / "data" / "demand_history.csv")

INDIGO, GREEN, AMBER, ROSE, BLUE, GREY, INK = "#4b46c8", "#2f9e6d", "#e0a030", "#d9534f", "#4a90d9", "#8a93a8", "#1b2238"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#6b7385", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "axes.titleweight": "bold"})
SHORT = {"proposed": "RF + matheuristic\n(proposed)", "exact_mip": "RF + exact MIP", "greedy": "RF + greedy", "kmeans": "RF + k-means",
         "largest": "Largest-markets\nrule", "fixed_avg": "Historical avg\n+ matheuristic"}
METH = CMP["methods"]


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def forecast_comparison():
    names = ["Random Forest\n(proposed)", "Last month's\nvalue", "3-month moving\naverage"]
    keys = ["random_forest", "baseline_last_value", "baseline_moving_avg_3"]
    fig, ax = plt.subplots(1, 3, figsize=(8.2, 3.0))
    for a, (metric, title, fmt) in zip(ax, [("mape", "MAPE (%) - lower is better", "{:.2f}"), ("rmse", "RMSE (orders) - lower is better", "{:,.0f}"), ("r2", "R-squared - higher is better", "{:.4f}")]):
        vals = [FM[k][metric] for k in keys]
        bars = a.bar(range(3), vals, color=[INDIGO, GREY, GREY], width=0.62)
        a.set_xticks(range(3)); a.set_xticklabels(names, fontsize=7.5)
        a.set_title(title, fontsize=8.5)
        for b, v in zip(bars, vals):
            a.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", fontsize=8)
        if metric == "r2":
            a.set_ylim(0.85, 1.0)
        else:
            a.set_ylim(0, max(vals) * 1.18)
    fig.suptitle("Held-out forecast accuracy, 2025-07 to 2025-12 (540 region-months)", fontsize=10, fontweight="bold", y=1.03)
    fig.tight_layout()
    save(fig, "forecast_comparison.png")


def feature_importance():
    top = FM["feature_importance"][:10][::-1]
    fig, ax = plt.subplots(figsize=(5.8, 3.3))
    ax.barh([t["feature"] for t in top], [t["importance"] for t in top], color=INDIGO, height=0.65)
    for i, t in enumerate(top):
        ax.text(t["importance"] + 0.004, i, f"{t['importance']:.4f}", va="center", fontsize=8)
    ax.set_xlabel("importance (mean decrease in impurity)")
    ax.set_title("Top 10 Random Forest feature importances", fontsize=10)
    ax.set_xlim(0, 0.45)
    save(fig, "feature_importance.png")


def monthly_volume():
    m = DEM.groupby("period").orders.sum() / 1e6
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    ax.plot(range(len(m)), m.values, color=INDIGO, lw=2, marker="o", ms=3)
    ax.axvspan(len(m) - 6.5, len(m) - 0.5, color=AMBER, alpha=0.18, label="held-out test months")
    ax.set_xticks(range(0, len(m), 3)); ax.set_xticklabels([m.index[i] for i in range(0, len(m), 3)], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("orders per month (millions)")
    ax.set_title("Synthetic network demand, 2023-01 to 2025-12 (festival peaks in Oct-Nov)", fontsize=10)
    ax.annotate(f"peak {m.max():.2f} M\n({m.idxmax()})", (list(m.index).index(m.idxmax()), m.max()), xytext=(-70, -4), textcoords="offset points", fontsize=8, arrowprops=dict(arrowstyle="->", color=GREY))
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "monthly_volume.png")


def forecast_scatter():
    d = pd.DataFrame(FM["last_period_detail"])
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.scatter(d.actual, d.predicted, s=22, color=INDIGO, alpha=0.75, edgecolor="white", lw=0.4)
    lo, hi = d[["actual", "predicted"]].min().min() * 0.8, d[["actual", "predicted"]].max().max() * 1.2
    ax.plot([lo, hi], [lo, hi], color=GREY, ls="--", lw=1, label="perfect forecast")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("actual orders, Dec 2025"); ax.set_ylabel("predicted orders")
    ax.set_title("Per-region forecast vs actual (90 regions)", fontsize=10)
    for _, r in d.sort_values("error_pct", ascending=False).head(3).iterrows():
        ax.annotate(r.region_id, (r.actual, r.predicted), xytext=(4, -9), textcoords="offset points", fontsize=7, color=ROSE)
    ax.legend(frameon=False, fontsize=8)
    save(fig, "forecast_scatter.png")


def error_hist():
    e = pd.DataFrame(FM["last_period_detail"]).error_pct
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.hist(e, bins=np.arange(0, 45, 5), color=INDIGO, edgecolor="white")
    ax.axvline(e.median(), color=AMBER, lw=2, label=f"median {e.median():.1f}%")
    ax.set_xlabel("absolute percentage error per region, Dec 2025"); ax.set_ylabel("regions")
    ax.set_title("Distribution of per-region forecast error", fontsize=10)
    ax.legend(frameon=False)
    save(fig, "error_histogram.png")


def cost_chart():
    keys = list(METH)
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    vals = [METH[k]["total_cost"] / 1e6 for k in keys]
    cols = [INDIGO if k == "proposed" else (GREEN if k == "exact_mip" else GREY) for k in keys]
    bars = ax.bar(range(len(keys)), vals, color=cols, width=0.62)
    ax.set_xticks(range(len(keys))); ax.set_xticklabels([SHORT[k] for k in keys], fontsize=7.6)
    ax.set_ylabel("operating cost, INR million per month")
    ax.set_ylim(0, max(vals) * 1.18)
    for b, k, v in zip(bars, keys, vals):
        pct = METH[k]["cost_vs_proposed_pct"]
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}\n({pct:+.1f}%)" if k != "proposed" else f"{v:.1f}\n(reference)", ha="center", va="bottom", fontsize=8)
    ax.set_title("Operating cost by method, planned for Oct 2025, scored on realised demand (p = 6)", fontsize=9.5)
    save(fig, "cost_by_method.png")


def fulfilment_chart():
    keys = list(METH)
    fig, ax = plt.subplots(figsize=(7.6, 3.2))
    vals = [METH[k]["fulfilment_rate"] * 100 for k in keys]
    cols = [INDIGO if k == "proposed" else (GREEN if k == "exact_mip" else GREY) for k in keys]
    bars = ax.bar(range(len(keys)), vals, color=cols, width=0.62)
    ax.set_xticks(range(len(keys))); ax.set_xticklabels([SHORT[k] for k in keys], fontsize=7.6)
    ax.set_ylabel("fulfilment of realised orders (%)")
    ax.set_ylim(0, 108)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=8)
    ax.set_title("Simulated fulfilment rate by method (Oct 2025 peak)", fontsize=10)
    save(fig, "fulfilment_by_method.png")


def cost_breakdown():
    keys = list(METH)
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    fixed = np.array([METH[k]["fixed_cost"] for k in keys]) / 1e6
    tr = np.array([METH[k]["transport_cost"] for k in keys]) / 1e6
    tm = np.array([METH[k]["time_cost"] for k in keys]) / 1e6
    x = range(len(keys))
    ax.bar(x, fixed, color=INDIGO, label="fixed hub cost", width=0.62)
    ax.bar(x, tr, bottom=fixed, color=BLUE, label="transport", width=0.62)
    ax.bar(x, tm, bottom=fixed + tr, color=AMBER, label="delivery-time penalty", width=0.62)
    ax.set_xticks(list(x)); ax.set_xticklabels([SHORT[k] for k in keys], fontsize=7.6)
    ax.set_ylabel("INR million per month"); ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0))
    ax.set_ylim(0, 88)
    ax.set_title("Cost components by method (Oct 2025)", fontsize=10, pad=14)
    save(fig, "cost_breakdown.png")


def utilisation():
    m = METH["proposed"]
    hubs = m["hub_cities"]
    util = [m["utilisation"][str(h)] * 100 for h in m["hubs"]]
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    bars = ax.bar(hubs, util, color=[ROSE if u > 100 else GREEN for u in util], width=0.6)
    ax.axhline(100, color=INK, ls="--", lw=1)
    ax.text(5.45, 101.5, "capacity", ha="right", fontsize=8)
    for b, u in zip(bars, util):
        ax.text(b.get_x() + b.get_width() / 2, u + 1.5, f"{u:.0f}%", ha="center", fontsize=8)
    ax.set_ylabel("load / capacity on realised demand (%)"); ax.set_ylim(0, 140)
    ax.set_title("Hub utilisation of the proposed plan, Oct 2025", fontsize=10)
    plt.setp(ax.get_xticklabels(), fontsize=7.5, rotation=18, ha="right")
    save(fig, "hub_utilisation.png")


def rolling_fulfilment():
    t = ROL["timeline"]
    x = [e["period"] for e in t]
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    ax.plot(x, [e["adaptive"]["fulfilment_rate"] * 100 for e in t], color=INDIGO, marker="o", lw=2.2, label="adaptive: re-forecast and re-plan monthly")
    ax.plot(x, [e["static"]["fulfilment_rate"] * 100 for e in t], color=ROSE, marker="s", lw=2.2, label="static plan fixed on the historical average")
    ax.set_ylabel("fulfilment (%)"); ax.set_ylim(55, 104)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.set_title("Rolling re-optimisation, Jul-Dec 2025 (p = 6)", fontsize=10)
    for e, p in zip(t, x):
        ax.text(p, e["adaptive"]["fulfilment_rate"] * 100 + 1.6, f"{e['adaptive']['fulfilment_rate']*100:.1f}", ha="center", fontsize=7.5, color=INDIGO)
        ax.text(p, e["static"]["fulfilment_rate"] * 100 - 4.2, f"{e['static']['fulfilment_rate']*100:.1f}", ha="center", fontsize=7.5, color=ROSE)
    save(fig, "rolling_fulfilment.png")


def rolling_demand():
    t = ROL["timeline"]
    x = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    ax.bar(x - 0.19, [e["forecast_total"] / 1e6 for e in t], 0.38, color=INDIGO, label="forecast")
    ax.bar(x + 0.19, [e["realized_total"] / 1e6 for e in t], 0.38, color=AMBER, label="realised")
    ax.set_xticks(x); ax.set_xticklabels([e["period"] for e in t])
    for i, e in enumerate(t):
        ax.text(i, max(e["forecast_total"], e["realized_total"]) / 1e6 + 0.04, f"{e['forecast_error_pct']:.1f}%", ha="center", fontsize=8)
    ax.set_ylabel("network orders (millions)"); ax.set_ylim(0, 2.8)
    ax.legend(frameon=False, ncol=2, loc="upper left", fontsize=8)
    ax.set_title("Network forecast vs realised demand (error labelled)", fontsize=10)
    save(fig, "rolling_demand.png")


def scalability():
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    n = [str(r["nodes"]) for r in SCAL]
    x = np.arange(len(n))
    ax.bar(x - 0.19, [r["matheuristic_seconds"] for r in SCAL], 0.38, color=INDIGO, label="matheuristic")
    ax.bar(x + 0.19, [r["exact_seconds"] for r in SCAL], 0.38, color=AMBER, label="exact MIP (CBC)")
    for i, r in enumerate(SCAL):
        ax.text(i - 0.19, r["matheuristic_seconds"] + 1, f"{r['matheuristic_seconds']:.1f}", ha="center", fontsize=8)
        ax.text(i + 0.19, r["exact_seconds"] + 1, f"{r['exact_seconds']:.1f}" + ("*" if r["exact_status"] != "Optimal" else ""), ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([f"{a} nodes\n({r['binary_vars']:,} binary vars)" for a, r in zip(n, SCAL)], fontsize=8)
    ax.set_ylabel("solve time (s)"); ax.set_ylim(0, 80)
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    ax.text(2.45, 76, "* not solved to optimality within its limit", ha="right", fontsize=7.5, color=GREY)
    ax.set_title("Scalability: exact MIP vs matheuristic", fontsize=10)
    save(fig, "scalability_time.png")


def paper_results():
    """Compact two-panel figure for the IEEE paper (one column wide)."""
    keys = ["proposed", "greedy", "kmeans", "largest", "fixed_avg"]
    lab = {"proposed": "Proposed", "greedy": "Greedy", "kmeans": "k-means", "largest": "Largest", "fixed_avg": "No forecast"}
    fig, (a, b) = plt.subplots(1, 2, figsize=(3.4, 1.95))
    c = [INDIGO if k == "proposed" else GREY for k in keys]
    a.bar(range(len(keys)), [METH[k]["total_cost"] / 1e6 for k in keys], color=c, width=0.7)
    a.set_xticks(range(len(keys))); a.set_xticklabels([lab[k] for k in keys], rotation=45, ha="right", fontsize=5.6)
    a.set_title("Cost (INR M)", fontsize=6.6); a.tick_params(labelsize=5.6); a.set_ylim(0, 80)
    for i, k in enumerate(keys):
        a.text(i, METH[k]["total_cost"] / 1e6 + 0.5, f"{METH[k]['total_cost']/1e6:.1f}", ha="center", fontsize=5.0)
    b.bar(range(len(keys)), [METH[k]["fulfilment_rate"] * 100 for k in keys], color=c, width=0.7)
    b.set_xticks(range(len(keys))); b.set_xticklabels([lab[k] for k in keys], rotation=45, ha="right", fontsize=5.6)
    b.set_title("Fulfilment (%)", fontsize=6.6); b.tick_params(labelsize=5.6); b.set_ylim(0, 108)
    for i, k in enumerate(keys):
        b.text(i, METH[k]["fulfilment_rate"] * 100 + 0.8, f"{METH[k]['fulfilment_rate']*100:.1f}", ha="center", fontsize=5.0)
    fig.tight_layout(pad=0.4)
    fig.savefig(ROOT / "docs" / "paper" / "fig3_results.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved paper fig3_results.png")


def paper_rolling():
    t = ROL["timeline"]
    x = [e["period"][2:] for e in t]
    fig, ax = plt.subplots(figsize=(3.4, 1.7))
    ax.plot(x, [e["adaptive"]["fulfilment_rate"] * 100 for e in t], color=INDIGO, marker="o", ms=3, lw=1.5, label="adaptive (monthly re-plan)")
    ax.plot(x, [e["static"]["fulfilment_rate"] * 100 for e in t], color=ROSE, marker="s", ms=3, lw=1.5, label="static plan")
    ax.set_ylim(55, 105); ax.set_ylabel("fulfilment (%)", fontsize=6); ax.tick_params(labelsize=6)
    ax.legend(frameon=False, fontsize=5.8, loc="lower left")
    for e, p in zip(t, x):
        ax.text(p, e["adaptive"]["fulfilment_rate"] * 100 + 1.8, f"{e['adaptive']['fulfilment_rate']*100:.0f}", ha="center", fontsize=5, color=INDIGO)
        ax.text(p, e["static"]["fulfilment_rate"] * 100 - 5, f"{e['static']['fulfilment_rate']*100:.0f}", ha="center", fontsize=5, color=ROSE)
    fig.tight_layout(pad=0.4)
    fig.savefig(ROOT / "docs" / "paper" / "fig6_rolling.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved paper fig6_rolling.png")


if __name__ == "__main__":
    (ROOT / "docs" / "paper").mkdir(parents=True, exist_ok=True)
    for f in (forecast_comparison, feature_importance, monthly_volume, forecast_scatter, error_hist, cost_chart, fulfilment_chart,
              cost_breakdown, utilisation, rolling_fulfilment, rolling_demand, scalability, paper_results, paper_rolling):
        f()
