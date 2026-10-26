"""Charts of the measured results (PNG, 150 dpi) into docs/charts/. Reads experiments/*/metrics.json only."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_common import CHARTS, metrics  # noqa: E402

INDIGO, MINT, ROSE, AMBER, SKY, INK, GREY = "#5b5bd6", "#2f9e77", "#d6455d", "#e0a030", "#3b8ed0", "#1b2238", "#9aa5ba"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK,
                     "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e3e7ef", "grid.linewidth": 0.7, "axes.axisbelow": True})
CHARTS.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    fig.savefig(CHARTS / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


sweep = metrics("noise_sweep")["rows"]
sig = np.array([r["noise_multiplier"] for r in sweep])
eps = np.array([r["epsilon"] for r in sweep])
ppl = np.array([r["perplexity"]["mean"] for r in sweep])
ppl_sd = np.array([r["perplexity"]["sd"] for r in sweep])
acc = np.array([r["accuracy"]["mean"] for r in sweep]) * 100
aucb = np.array([r["membership_auc_before"]["mean"] for r in sweep])
auca = np.array([r["membership_auc_after"]["mean"] for r in sweep])
aucb_sd = np.array([r["membership_auc_before"]["sd"] for r in sweep])
auca_sd = np.array([r["membership_auc_after"]["sd"] for r in sweep])


def c01():
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.3))
    ax[0].errorbar(sig, ppl, yerr=ppl_sd, color=INDIGO, marker="o", ms=4, capsize=2, lw=1.4, label="perplexity (mean +/- sd)")
    ax[0].axhline(32, color=ROSE, ls="--", lw=1, label="uniform model (32)")
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel("noise multiplier sigma"); ax[0].set_ylabel("perplexity (lower is better)")
    ax[0].axvline(3, color=GREY, ls=":", lw=1); ax[0].text(3.1, 11, "default\nsigma = 3", fontsize=7.5, color=INK)
    ax[0].axvline(4.85, color=MINT, ls=":", lw=1); ax[0].text(5.0, 300, "epsilon < 1\nabove here", fontsize=7.5, color=MINT)
    ax[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    ax[0].set_title("Language-model quality vs noise", fontsize=9.5, fontweight="bold")
    ax[1].plot(sig, acc, color=MINT, marker="s", ms=4, lw=1.4)
    ax[1].set_xscale("log"); ax[1].set_xlabel("noise multiplier sigma"); ax[1].set_ylabel("next-character accuracy (%)")
    ax[1].axvline(3, color=GREY, ls=":", lw=1); ax[1].axvline(4.85, color=MINT, ls=":", lw=1)
    ax[1].set_title("Next-character accuracy vs noise", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c01_noise_vs_quality.png")


def c02():
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    ax.errorbar(sig, aucb, yerr=aucb_sd / np.sqrt(100), color=INDIGO, marker="o", ms=4, capsize=2, lw=1.4, label="before unlearning")
    ax.errorbar(sig, auca, yerr=auca_sd / np.sqrt(100), color=MINT, marker="s", ms=4, capsize=2, lw=1.4, label="after unlearning")
    ax.axhline(0.5, color=ROSE, ls="--", lw=1, label="chance (0.5)")
    ax.set_xscale("log"); ax.set_xlabel("noise multiplier sigma"); ax.set_ylabel("membership-inference AUC")
    ax.set_ylim(0.4, 1.02)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Leakage the attack can see, and what unlearning removes", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c02_noise_vs_auc.png")


def c03():
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    ax.plot(eps, ppl, color=INDIGO, marker="o", ms=4, lw=1.4)
    for s_, e_, p_ in zip(sig, eps, ppl):
        if s_ in (0.1, 1.0, 3.0, 4.85, 10.0):
            ax.annotate(f"sigma={s_:g}", (e_, p_), textcoords="offset points", xytext=(5, 4), fontsize=7.5)
    ax.axvline(1, color=MINT, ls="--", lw=1); ax.text(1.08, 60, "epsilon = 1\n(classical bound\nvalid left of here)", fontsize=7.5, color=MINT)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("reported epsilon (delta = 1e-5)"); ax.set_ylabel("perplexity")
    ax.set_title("Privacy-utility trade-off", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c03_privacy_utility.png")


def c04():
    b = metrics("baseline")["unlearning_per_client"]
    names = [c["client_name"].split(" (")[1].rstrip(")") for c in b]
    x = np.arange(len(b))
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.2))
    ax[0].bar(x - 0.2, [c["membership_auc_before"] for c in b], 0.4, color=INDIGO, label="before")
    ax[0].bar(x + 0.2, [c["membership_auc_after"] for c in b], 0.4, color=MINT, label="after")
    ax[0].axhline(0.5, color=ROSE, ls="--", lw=1)
    ax[0].set_xticks(x); ax[0].set_xticklabels(names, fontsize=8); ax[0].set_ylabel("membership AUC"); ax[0].legend(frameon=False, fontsize=8)
    ax[0].set_title("Membership AUC, default run", fontsize=9.5, fontweight="bold")
    ax[1].bar(x, [c["utility_retention_percent"] for c in b], 0.55, color=SKY)
    ax[1].axhline(70, color=ROSE, ls="--", lw=1); ax[1].text(4.45, 71.5, "70 % floor", fontsize=7.5, color=ROSE, ha="right")
    for i, c in enumerate(b):
        ax[1].text(i, c["utility_retention_percent"] + 1, f"{c['utility_retention_percent']:.1f}", ha="center", fontsize=8)
    ax[1].set_xticks(x); ax[1].set_xticklabels(names, fontsize=8); ax[1].set_ylim(0, 108); ax[1].set_ylabel("utility retention (%)")
    ax[1].set_title("Utility retained after removal", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c04_baseline_clients.png")


def c05():
    g = metrics("gold_retrain")["results"]
    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2))
    for a_, r in zip(ax, g):
        a = r["l2_unlearned_vs_fresh_retrain"]; b = r["l2_fresh_retrain_vs_fresh_retrain"]
        a_.bar([0, 1], [a["mean"], b["mean"]], yerr=[a["sd"], b["sd"]], color=[INDIGO, AMBER], capsize=4, width=0.55)
        a_.set_xticks([0, 1]); a_.set_xticklabels(["unlearned vs\nfresh retrain", "fresh retrain vs\nfresh retrain"], fontsize=8)
        a_.set_ylabel("L2 distance between models")
        a_.set_title(f"sigma = {r['noise_multiplier']:g}  (n = {r['pairs']} pairs)", fontsize=9.5, fontweight="bold")
        for i, v in enumerate([a["mean"], b["mean"]]):
            a_.text(i, v * 0.5, f"{v:.1f}", ha="center", color="white", fontsize=9, fontweight="bold")
    fig.tight_layout()
    save(fig, "c05_gold_retrain.png")


def c06():
    nf = metrics("noise_free_leakage")["rows"]
    names = [r["client_id"].replace("client_", "").title() for r in nf]
    x = np.arange(len(nf))
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.bar(x - 0.2, [r["auc_before"] for r in nf], 0.4, color=INDIGO, label="before removal")
    ax.bar(x + 0.2, [r["auc_after"] for r in nf], 0.4, color=MINT, label="after removal")
    ax.axhline(0.5, color=ROSE, ls="--", lw=1, label="chance")
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8); ax.set_ylabel("membership AUC"); ax.set_ylim(0, 1.12)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center")
    ax.set_title("Without noise (sigma = 1e-6): removal is visible", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c06_noise_free_auc.png")


def c07():
    st = metrics("sequential")["steps"]
    n = [s["active_clients"] for s in st]
    fig, ax = plt.subplots(1, 2, figsize=(7.8, 3.1))
    ax[0].plot(n, [s["perplexity"] for s in st], color=INDIGO, marker="o", lw=1.4)
    ax[0].axhline(32, color=ROSE, ls="--", lw=1); ax[0].text(4.9, 36, "uniform = 32", color=ROSE, fontsize=7.5, ha="right")
    ax[0].invert_xaxis(); ax[0].set_xlabel("active clients"); ax[0].set_ylabel("perplexity"); ax[0].set_title("Perplexity as clients are removed", fontsize=9.5, fontweight="bold")
    ax[1].plot(n, [s["next_character_accuracy"] * 100 for s in st], color=MINT, marker="s", lw=1.4)
    ax[1].invert_xaxis(); ax[1].set_xlabel("active clients"); ax[1].set_ylabel("next-character accuracy (%)"); ax[1].set_ylim(0, 8)
    ax[1].set_title("Accuracy as clients are removed", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c07_sequential_removal.png")


def c08():
    r = metrics("scaling")["rows"]
    n = [x["clients"] for x in r]
    fig, ax = plt.subplots(figsize=(5.6, 3.3))
    ax.plot(n, [x["unlearn_ms_median"] for x in r], color=INDIGO, marker="o", lw=1.4, label="unlearn() on the trained model")
    ax.plot(n, [x["full_retrain_ms_median"] for x in r], color=AMBER, marker="s", lw=1.4, label="retrain on retained clients")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("federated clients (5 to 500)"); ax.set_ylabel("median wall time (ms)")
    for x in r:
        ax.annotate(f"{x['speedup_retrain_over_unlearn']:.1f}x", (x["clients"], x["unlearn_ms_median"]), textcoords="offset points", xytext=(0, -12), fontsize=7.5, ha="center", color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Cost of unlearning vs retraining the proxy (labels: retrain / unlearn)", fontsize=8.8, fontweight="bold")
    fig.tight_layout()
    save(fig, "c08_scaling.png")


def c09():
    lat = {k: v for k, v in metrics("api")["latency"].items() if "p95_ms" in v and "grown" not in k}
    keys = list(lat)
    y = np.arange(len(keys))
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ax.barh(y + 0.2, [lat[k]["p50_ms"] for k in keys], 0.4, color=INDIGO, label="median")
    ax.barh(y - 0.2, [lat[k]["p95_ms"] for k in keys], 0.4, color=AMBER, label="95th percentile")
    ax.set_yticks(y); ax.set_yticklabels(keys, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("response time on 127.0.0.1 (ms)"); ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("API latency (single client, local server)", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c09_api_latency.png")


def c10():
    cases = metrics("audit_tamper")["cases"][1:]
    y = np.arange(len(cases))
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    ax.barh(y, [1] * len(cases), color=[MINT if c["detected"] else ROSE for c in cases], height=0.6)
    for i, c in enumerate(cases):
        ax.text(0.02, i, "detected" if c["detected"] else "NOT detected", va="center", color="white", fontsize=8.5, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels([c["case"] for c in cases], fontsize=8); ax.invert_yaxis(); ax.set_xticks([]); ax.grid(False)
    ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False)
    ax.set_title("Audit-ledger tamper detection (7 attacks)", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c10_audit_tamper.png")


def c11():
    s = metrics("seeds")
    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.1))
    labels = ["AUC before", "AUC after"]
    vals = [s["membership_auc_before"], s["membership_auc_after"]]
    ax[0].bar([0, 1], [v["mean"] for v in vals], yerr=[v["sd"] for v in vals], color=[INDIGO, MINT], capsize=4, width=0.55)
    ax[0].axhline(0.5, color=ROSE, ls="--", lw=1)
    ax[0].set_xticks([0, 1]); ax[0].set_xticklabels(labels); ax[0].set_ylim(0, 1); ax[0].set_ylabel("membership AUC (mean +/- sd)")
    ax[0].set_title("250 requests, default noise", fontsize=9.5, fontweight="bold")
    pp = [s["pre_unlearning_perplexity"], s["perplexity_after_unlearning"]]
    ax[1].bar([0, 1], [v["mean"] for v in pp], yerr=[v["sd"] for v in pp], color=[INDIGO, MINT], capsize=4, width=0.55)
    ax[1].axhline(32, color=ROSE, ls="--", lw=1)
    ax[1].set_xticks([0, 1]); ax[1].set_xticklabels(["perplexity before", "perplexity after"]); ax[1].set_ylabel("perplexity (mean +/- sd)")
    ax[1].set_title("Public-set perplexity", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c11_seed_study.png")


def c12():
    sc = metrics("scaling")["ledger_append_ms_at_length"]
    xs = [int(k) for k in sc]
    fig, ax = plt.subplots(figsize=(5.0, 3.1))
    ax.plot(xs, list(sc.values()), color=INDIGO, marker="o", lw=1.4)
    ax.set_xlabel("records already in the ledger"); ax.set_ylabel("time to append one record (ms)")
    ax.set_title("Ledger append re-reads the whole file", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "c12_ledger_append.png")


if __name__ == "__main__":
    for f in (c01, c02, c03, c04, c05, c06, c07, c08, c09, c10, c11, c12):
        f()


def t01():
    sc = metrics("load_test")["scenarios"]
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.3))
    cols = [INDIGO, MINT, AMBER, ROSE]
    for (name, v), c in zip(sc.items(), cols):
        lv = v["levels"]
        x = [l["concurrency"] for l in lv]
        ax[0].plot(x, [l["requests_per_s"] for l in lv], marker="o", ms=4, lw=1.4, color=c, label=name)
        ax[1].plot(x, [l["p95_ms"] for l in lv], marker="o", ms=4, lw=1.4, color=c, label=name)
    for a_ in ax:
        a_.set_xscale("log", base=2); a_.set_xlabel("concurrent clients")
    ax[0].set_yscale("log"); ax[1].set_yscale("log")
    ax[0].set_ylabel("requests per second"); ax[1].set_ylabel("95th-percentile latency (ms)")
    ax[0].legend(frameon=False, fontsize=7.5)
    ax[0].set_title("Throughput vs concurrency", fontsize=9.5, fontweight="bold")
    ax[1].set_title("Tail latency vs concurrency", fontsize=9.5, fontweight="bold")
    fig.tight_layout()
    save(fig, "t01_load.png")


if __name__ == "__main__":
    t01()
