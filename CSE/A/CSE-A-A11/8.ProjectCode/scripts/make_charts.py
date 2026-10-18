"""Result charts for the reports, drawn from autosecai/artifacts/report.json, docs/measured_facts.json and
docs/measured_api_latency.json (no number is typed by hand).   Output: docs/charts/*.png (150 dpi)

    python scripts/make_charts.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "charts"
REP = json.loads((ROOT / "autosecai/artifacts/report.json").read_text())
MF = json.loads((ROOT / "docs/measured_facts.json").read_text())
API = json.loads((ROOT / "docs/measured_api_latency.json").read_text())
COL = ["#6d5bd0", "#2f9e6d", "#e08a2c", "#d1495b", "#3b82c4", "#8c8c9a"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150, facecolor="white")
    plt.close(fig)


def model_bars():
    res = REP["results"]
    names = list(res)
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    for i, (m, c) in enumerate((("precision", COL[0]), ("recall", COL[1]), ("f1", COL[2]))):
        vals = [res[n][m] for n in names]
        ax.bar(x + (i - 1) * 0.27, vals, 0.27, label=m.capitalize() if m != "f1" else "F1", color=c)
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace(" (RBF)", "").replace(" ", "\n", 1) for n in names], fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("score on 1,500 held-out functions")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13), frameon=False)
    ax.set_title("Nine classifiers on the generated Python corpus", pad=22, fontsize=10, fontweight="bold")
    save(fig, "models_prf.png")


def roc():
    fig, ax = plt.subplots(figsize=(4.8, 4.0))
    for (n, r), c in zip(REP["roc"].items(), COL + COL):
        ax.plot(r["fpr"], r["tpr"], lw=1.6 if n in ("XGBoost", "Random Forest") else 0.9, label=f"{n} (AUC {REP['results'][n]['auc']:.3f})")
    ax.plot([0, 1], [0, 1], "--", color="#aaaaaa", lw=0.8)
    ax.set_xlabel("false-positive rate")
    ax.set_ylabel("true-positive rate")
    ax.legend(fontsize=6.5, loc="lower right", frameon=False)
    ax.set_title("ROC curves", fontsize=10, fontweight="bold")
    save(fig, "roc.png")


def confusion():
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.0))
    for ax, n in zip(axes, ("XGBoost", "Random Forest")):
        cm = np.array(REP["confusion"][n])
        ax.imshow(cm, cmap="Purples")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", color="white" if cm[i, j] > 700 else "#1b2238", fontsize=11, fontweight="bold")
        ax.set_xticks([0, 1], ["safe", "vulnerable"])
        ax.set_yticks([0, 1], ["safe", "vulnerable"])
        ax.set_xlabel("predicted")
        ax.set_ylabel("actual")
        ax.set_title(n, fontsize=10, fontweight="bold")
        for s in ax.spines.values():
            s.set_visible(False)
    save(fig, "confusion.png")


def importance():
    imp = REP["importance"]
    names, vals = list(imp)[::-1], list(imp.values())[::-1]
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.barh(names, vals, color=COL[0])
    ax.set_xlabel("Random Forest importance")
    ax.set_title("Which metrics drive the score", fontsize=10, fontweight="bold")
    save(fig, "importance.png")


def ksweep():
    k = REP["k_scores"]
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.plot([int(a) for a in k], list(k.values()), "o-", color=COL[0])
    best = REP["best_k"]
    ax.plot([best], [k[str(best)]], "o", ms=10, color=COL[3], label=f"chosen k = {best}")
    ax.set_xlabel("number of metrics kept (k)")
    ax.set_ylabel("validation F1")
    ax.legend(frameon=False)
    ax.set_title("Feature-count sweep", fontsize=10, fontweight="bold")
    save(fig, "k_sweep.png")


def ablation():
    ab = REP["ablation"]
    labels = ["all 14 metrics,\nno balancing", "top-5 + SMOTE-Tomek\n(paper setting)", f"top-{REP['best_k']} + SMOTE-Tomek\n(this system)"]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for i, (m, c, lab) in enumerate((("precision", COL[0], "Precision"), ("recall", COL[1], "Recall"), ("f1", COL[2], "F1"))):
        ax.bar(x + (i - 1) * 0.27, [v[m] for v in ab.values()], 0.27, color=c, label=lab)
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12))
    ax.set_title("Random Forest ablation", pad=20, fontsize=10, fontweight="bold")
    save(fig, "ablation.png")


def type_f1():
    tr = {k: v for k, v in REP["type_report"].items() if k not in ("macro avg", "weighted avg")}
    names = sorted(tr, key=lambda k: tr[k]["f1-score"])
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.barh([n.replace("_", " ") for n in names], [tr[n]["f1-score"] for n in names], color=COL[4])
    ax.set_xlim(0, 1)
    ax.set_xlabel(f"F1 (type accuracy {REP['type_accuracy']:.3f}, 126 test functions)")
    ax.set_title("Vulnerability-type classifier", fontsize=10, fontweight="bold")
    save(fig, "type_f1.png")


def engine_vs_ml():
    ev = MF["engine_vs_ml"]
    rows = [("Rule engine", "rule_engine"), (f"ML ({ev['best_model']})", "ml_model"), ("Either (OR)", "combined_or"), ("Both (AND)", "combined_and")]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for i, (m, c, lab) in enumerate((("precision", COL[0], "Precision"), ("recall", COL[1], "Recall"), ("f1", COL[2], "F1"))):
        vals = [ev[k][m] for _, k in rows]
        bars = ax.bar(x + (i - 1) * 0.27, vals, 0.27, color=c, label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=6.5)
    ax.set_xticks(x, [r[0] for r in rows])
    ax.set_ylim(0, 1.12)
    ax.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    ax.set_title("Rule engine and ML model on the same 1,500 functions", pad=20, fontsize=10, fontweight="bold")
    save(fig, "engine_vs_ml.png")


def seeds():
    runs = MF["seeds"]["runs"]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    xs = [r["seed"] for r in runs]
    ax.plot(range(len(xs)), [r["XGBoost"]["f1"] for r in runs], "o-", color=COL[0], label="XGBoost")
    ax.plot(range(len(xs)), [r["Random Forest"]["f1"] for r in runs], "s-", color=COL[1], label="Random Forest")
    ax.set_xticks(range(len(xs)), [f"seed {s}" for s in xs])
    ax.set_ylim(0.7, 0.95)
    ax.set_ylabel("F1")
    ax.legend(frameon=False)
    ax.set_title("Five independently generated corpora", fontsize=10, fontweight="bold")
    save(fig, "seeds.png")


def latency():
    pa = MF["latency"]["per_agent_median_s"]
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    names = list(pa)
    ax.barh(names[::-1], [pa[n] * 1000 for n in names[::-1]], color=COL[4])
    ax.set_xlabel(f"median milliseconds per agent (demo PR, {MF['latency']['runs']} runs; whole review {MF['latency']['median_s'] * 1000:.0f} ms)")
    ax.set_title("Where the review time goes", fontsize=10, fontweight="bold")
    save(fig, "latency_agents.png")


def severity():
    st = MF["latency"]["demo"]["stats"]["by_severity"]
    order = ["critical", "high", "medium", "low", "info"]
    vals = [st[k] for k in order]
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.bar(order, vals, color=["#7c3aed", "#e11d48", "#f59e0b", "#06b6d4", "#94a3b8"])
    for i, v in enumerate(vals):
        ax.text(i, v + 0.2, str(v), ha="center", fontsize=9)
    ax.set_ylabel("findings")
    ax.set_title("Findings on the demo pull request by severity", fontsize=10, fontweight="bold")
    save(fig, "demo_severity.png")


def api_latency():
    items = [(k, v.get("median_ms", v.get("ms"))) for k, v in API.items() if k != "POST /api/auth/login (bcrypt)"]
    names = [k.replace(" -> done (polled 50 ms)", "\n(job to done, polled)") for k, _ in items][::-1]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.barh(names, [v for _, v in items][::-1], color=COL[0])
    ax.set_xscale("log")
    ax.set_xlabel("median milliseconds (log scale)")
    ax.set_title("HTTP latency on localhost", fontsize=10, fontweight="bold")
    ax.tick_params(axis="y", labelsize=7)
    save(fig, "api_latency.png")


if __name__ == "__main__":
    for fn in (model_bars, roc, confusion, importance, ksweep, ablation, type_f1, engine_vs_ml, seeds, latency, severity, api_latency):
        fn()
    print("charts ->", OUT)
