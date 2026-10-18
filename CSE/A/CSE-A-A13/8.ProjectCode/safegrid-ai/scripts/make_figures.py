"""
Result charts drawn from the real measurements (matplotlib, 150 dpi).

    python scripts/make_figures.py        # -> docs/figures/*.png

Inputs: docs/results/experiment_3seeds_24steps.json (63 simulation runs), docs/results/timeseries_seed42.json (single runs, seed 42),
and the live API latency table in scripts/docs/facts.py (copied from docs/REPORT_FACTS.md).
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from scripts.docs import facts as F  # noqa: E402

OUT = F.FIGS
os.makedirs(OUT, exist_ok=True)
NAVY, GREY, ORANGE, BLUE, GREEN, RED, GOLD = "#1B2A41", "#8A97AB", "#EB6834", "#2A78D6", "#1BAF7A", "#D6453A", "#E8A317"
COL = {"baseline_rule": GREY, "agents_unshielded": ORANGE, "safegrid_shielded": GREEN}
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#9AA8BD",
                     "axes.grid": True, "grid.color": "#E3E8EF", "grid.linewidth": 0.8, "axes.axisbelow": True, "font.size": 9})


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p)


def nice(sc):
    return sc.replace("_", " ")


def grouped(ax, key, ylabel, fmt="{:.1f}", scale=1.0):
    x = np.arange(len(F.SCENARIOS))
    w = 0.26
    for i, arm in enumerate(F.ARMS):
        raw = [F.BYSC[sc][arm].get(key) for sc in F.SCENARIOS]
        vals = [(r["mean"] * scale if r else 0.0) for r in raw]
        bars = ax.bar(x + (i - 1) * w, vals, w, color=COL[arm], label=F.ARM_LABEL[arm])
        for b, v, r in zip(bars, vals, raw):
            lab = fmt.format(v) if r else "n/a"
            ax.text(b.get_x() + b.get_width() / 2, max(b.get_height(), 0) + 0.15, lab, ha="center", va="bottom", fontsize=6.5, color="#334155")
    ax.set_xticks(x)
    ax.set_xticklabels([nice(s).replace(" ", "\n") for s in F.SCENARIOS], fontsize=8)
    ax.set_ylabel(ylabel)


def fig_violations():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    grouped(ax, "violation_steps_caused_by_actions", "steps with violations caused by actions\n(of 24, mean of 3 seeds)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_ylim(0, 14.5)
    save(fig, "fig_violations_by_scenario.png")


def fig_executed():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    grouped(ax, "violation_steps_executed", "steps with any violation after execution\n(of 24, mean of 3 seeds)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "fig_executed_violations.png")


def fig_decisions():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(F.SCENARIOS))
    ap = np.array([F.sc_mean(s, "safegrid_shielded", "approved") for s in F.SCENARIOS])
    pr = np.array([F.sc_mean(s, "safegrid_shielded", "projected") for s in F.SCENARIOS])
    rj = np.array([F.sc_mean(s, "safegrid_shielded", "rejected") for s in F.SCENARIOS])
    ax.bar(x, ap, color=GREEN, label="approved")
    ax.bar(x, pr, bottom=ap, color=GOLD, label="projected (scaled down)")
    ax.bar(x, rj, bottom=ap + pr, color=RED, label="rejected")
    for i in range(len(x)):
        ax.text(x[i], ap[i] / 2, f"{ap[i]:.1f}", ha="center", va="center", fontsize=7, color="white")
        ax.text(x[i], ap[i] + pr[i] / 2, f"{pr[i]:.1f}", ha="center", va="center", fontsize=7, color=NAVY)
        ax.text(x[i], ap[i] + pr[i] + rj[i] / 2, f"{rj[i]:.1f}", ha="center", va="center", fontsize=7, color="white")
    ax.set_xticks(x)
    ax.set_xticklabels([nice(s).replace(" ", "\n") for s in F.SCENARIOS], fontsize=8)
    ax.set_ylabel("proposals per run (72 = 3 agents x 24 steps)")
    ax.set_ylim(0, 84)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center")
    save(fig, "fig_shield_decisions.png")


def fig_overall():
    fig, axes = plt.subplots(1, 4, figsize=(8.4, 2.9))
    spec = [("violation_steps_executed", "steps with any violation\nafter execution (of 24)", "{:.2f}", 1),
            ("total_cost", "energy cost per run\n(INR, illustrative tariff)", "{:.0f}", 1),
            ("renewable_utilization", "renewable utilisation", "{:.2f}", 1),
            ("avg_step_time_ms", "mean step time (ms)", "{:.0f}", 1)]
    for ax, (k, t, fmt, sc) in zip(axes, spec):
        vals = [F.mean(a, k) * sc for a in F.ARMS]
        bars = ax.bar(range(3), vals, color=[COL[a] for a in F.ARMS])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), fmt.format(v), ha="center", va="bottom", fontsize=8, color="#334155")
        ax.set_xticks(range(3))
        ax.set_xticklabels(["rule", "agents\nno shield", "SafeGrid\nAI"], fontsize=7.5)
        ax.set_title(t, fontsize=8.5)
        ax.margins(y=0.18)
    save(fig, "fig_overall_metrics.png")


def fig_cost_util():
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.1))
    grouped(axes[0], "total_cost", "energy cost per run (INR)", "{:.0f}")
    axes[0].set_title("Energy cost by scenario", fontsize=9)
    axes[0].tick_params(axis="x", labelsize=6.5)
    grouped(axes[1], "renewable_utilization", "renewable utilisation", "{:.2f}")
    axes[1].set_title("Renewable utilisation by scenario", fontsize=9)
    axes[1].set_ylim(0, 1.2)
    axes[1].tick_params(axis="x", labelsize=6.5)
    axes[1].legend(frameon=False, fontsize=7, loc="lower left")
    save(fig, "fig_cost_utilisation.png")


def fig_latency():
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    rows = F.API_LAT[::-1]
    y = np.arange(len(rows))
    ax.barh(y + 0.18, [r[2] for r in rows], 0.34, color=BLUE, label="median")
    ax.barh(y - 0.18, [r[3] for r in rows], 0.34, color=GOLD, label="95th percentile")
    for yi, r in zip(y, rows):
        ax.text(r[3] + 6, yi - 0.18, f"{r[3]:.0f}", va="center", fontsize=7)
        ax.text(r[2] + 6, yi + 0.18, f"{r[2]:.1f}", va="center", fontsize=7)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0].replace(" (agent proposal, dry run)", " (dry run)").replace("POST dry run, ", "dry run: ") for r in rows], fontsize=7.5)
    ax.set_xlabel("latency (ms), live API on localhost")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_xlim(0, 590)
    save(fig, "fig_api_latency.png")


def fig_stress():
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    x = np.arange(len(F.SCENARIOS))
    pre = [F.sc_mean(s, "safegrid_shielded", "violation_steps_no_action") for s in F.SCENARIOS]
    ex = [F.sc_mean(s, "safegrid_shielded", "violation_steps_executed") for s in F.SCENARIOS]
    ax.bar(x - 0.2, pre, 0.38, color=GREY, label="grid stress with every agent idle")
    ax.bar(x + 0.2, ex, 0.38, color=GREEN, label="violation after SafeGrid-AI actions")
    for xi, a, b in zip(x, pre, ex):
        ax.text(xi - 0.2, a + 0.2, f"{a:.1f}", ha="center", fontsize=7)
        ax.text(xi + 0.2, b + 0.2, f"{b:.1f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([nice(s).replace(" ", "\n") for s in F.SCENARIOS], fontsize=8)
    ax.set_ylabel("steps (of 24, mean of 3 seeds)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_ylim(0, 26)
    save(fig, "fig_preexisting_stress.png")


def fig_timeseries():
    p = os.path.join(F.DOCS, "results", "timeseries_seed42.json")
    if not os.path.exists(p):
        print("no timeseries file; skipped")
        return
    d = json.load(open(p, encoding="utf-8"))
    specs = [("line_congestion", "max_line_loading_pct", "worst line loading (%)", 100.0, "Line congestion"),
             ("voltage_violation", "max_voltage_pu", "highest bus voltage (pu)", 1.05, "Voltage violation"),
             ("peak_demand", "min_voltage_pu", "lowest bus voltage (pu)", 0.95, "Peak demand")]
    fig, axes = plt.subplots(1, 3, figsize=(9.4, 2.9))
    fig.subplots_adjust(wspace=0.42)
    for ax, (sc, key, yl, lim, title) in zip(axes, specs):
        for tag, col, lab in (("noshield", ORANGE, "agents, no shield"), ("shield", GREEN, "SafeGrid-AI")):
            ser = d[f"{sc}_{tag}"]["series"]
            ys = [s.get(key) for s in ser]
            ax.plot(range(len(ys)), ys, color=col, lw=1.6, label=lab)
        ax.axhline(lim, color=RED, lw=1, ls="--")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("step (15 min)")
        ax.set_ylabel(yl, fontsize=8)
    axes[0].legend(frameon=False, fontsize=7.5, loc="center right")
    save(fig, "fig_timeseries.png")


if __name__ == "__main__":
    for fn in (fig_violations, fig_executed, fig_decisions, fig_overall, fig_cost_util, fig_latency, fig_stress, fig_timeseries):
        fn()
