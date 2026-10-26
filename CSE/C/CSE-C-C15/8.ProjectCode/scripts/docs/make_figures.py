"""Result charts (matplotlib, 150 dpi) -> docs/figures/, drawn from results/experiments/*.json and results/*.json.

    python -m scripts.docs.make_figures
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))
EXP = os.path.join(CODE, "results", "experiments")
OUT = os.path.join(CODE, "docs", "figures")
os.makedirs(OUT, exist_ok=True)
NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#8A97A8", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True})


def J(*p):
    return json.load(open(os.path.join(*p), encoding="utf-8"))


REAL = J(EXP, "real_cicids2017.json")
HYB = J(EXP, "hybrid_recipe.json")
WIN = J(EXP, "window_pipeline.json")
LAT = J(EXP, "latency.json")
API = J(EXP, "api_measurements.json")
SHIP = J(CODE, "results", "metrics.json")
CM = J(CODE, "results", "confusion_matrix.json")["matrix"]
IMP = J(CODE, "results", "feature_importance.json")


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", p)


def f01_domain_gap():
    fpr_ship = CM[0][1] / (CM[0][0] + CM[0][1])
    rows = [("Shipped model\non its own\nsynthetic test split", SHIP["accuracy"], SHIP["recall"], fpr_ship, ORANGE),
            ("Shipped model\non real CICIDS2017\nflows (225,745)", REAL["shipped_on_real_all"]["accuracy"], REAL["shipped_on_real_all"]["recall"], REAL["shipped_on_real_all"]["fpr"], RED),
            ("RF retrained on\nreal flows, 20 %\ntest (5-seed mean)", REAL["real_rf_accuracy_mean"], REAL["real_rf_recall_mean"], REAL["real_rf_fpr_mean"], TEAL),
            ("Block split:\ntrain first 70 %,\ntest last 30 %", REAL["real_rf_block_split"]["accuracy"], REAL["real_rf_block_split"]["recall"], REAL["real_rf_block_split"]["fpr"], BLUE)]
    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    x = np.arange(len(rows))
    w = 0.26
    for i, (lab, key) in enumerate((("Accuracy", 1), ("Recall (attack)", 2), ("False-positive rate", 3))):
        vals = [r[key] for r in rows]
        bars = ax.bar(x + (i - 1) * w, vals, w, label=lab, color=[NAVY, TEAL, ORANGE][i])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v * 100:.1f}" if v > 0.01 else f"{v * 100:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in rows], fontsize=7.6)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("share of windows / flows")
    ax.set_title("The 99.7 % on synthetic data does not carry over to real CICIDS2017 flows (values in %)", fontsize=9)
    ax.legend(fontsize=7.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.27), frameon=False)
    save(fig, "f01_domain_gap.png")


def f02_window_size():
    ws = ["window_2s", "window_5s", "window_10s"]
    lab = ["2 s", "5 s", "10 s"]
    ml_fpr = [WIN[w]["ml_only"]["fpr"] for w in ws]
    act_fpr = [WIN[w]["actionable_high_or_critical"]["fpr"] for w in ws]
    act_rec = [WIN[w]["actionable_high_or_critical"]["recall"] for w in ws]
    fig, ax = plt.subplots(1, 2, figsize=(8.4, 3.5))
    x = np.arange(3)
    b1 = ax[0].bar(x - 0.18, ml_fpr, 0.36, color=ORANGE, label="Random Forest label alone")
    b2 = ax[0].bar(x + 0.18, act_fpr, 0.36, color=TEAL, label="High/Critical severity (acts)")
    for bars in (b1, b2):
        for b in bars:
            ax[0].text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01, f"{b.get_height() * 100:.1f} %", ha="center", fontsize=7)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels(lab)
    ax[0].set_xlabel("monitoring-window length")
    ax[0].set_ylabel("false-positive rate on benign windows")
    ax[0].legend(fontsize=7, frameon=False)
    ax[0].set_title("False positives vs window length", fontsize=9)
    ax[1].bar(x, act_rec, 0.5, color=NAVY)
    for i, v in enumerate(act_rec):
        ax[1].text(i, v + 0.01, f"{v * 100:.1f} %", ha="center", fontsize=7.5)
    ax[1].set_ylim(0, 1.1)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(lab)
    ax[1].set_xlabel("monitoring-window length")
    ax[1].set_ylabel("attack windows reaching High/Critical")
    ax[1].set_title("Actionable recall", fontsize=9)
    fig.tight_layout()
    save(fig, "f02_window_size_effect.png")


def f03_baselines():
    b = REAL["baselines_seed42"]
    names = list(b)
    acc = [b[n]["accuracy"] for n in names]
    f1 = [b[n]["f1"] for n in names]
    fpr = [b[n]["fpr"] for n in names]
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.6), gridspec_kw={"width_ratios": [1.5, 1]})
    x = np.arange(len(names))
    ax[0].bar(x - 0.27, acc, 0.27, color=NAVY, label="Accuracy")
    ax[0].bar(x, f1, 0.27, color=TEAL, label="F1")
    ax[0].bar(x + 0.27, fpr, 0.27, color=ORANGE, label="False-positive rate")
    for i, (a, f, p) in enumerate(zip(acc, f1, fpr)):
        ax[0].text(i - 0.27, a + 0.015, f"{a * 100:.1f}", ha="center", fontsize=6.4)
        ax[0].text(i, f + 0.015, f"{f * 100:.1f}", ha="center", fontsize=6.4)
        ax[0].text(i + 0.27, p + 0.015, f"{p * 100:.1f}", ha="center", fontsize=6.4)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels([n.replace("(", "\n(") for n in names], fontsize=6.6)
    ax[0].set_ylim(0, 1.12)
    ax[0].legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.3))
    ax[0].set_title("Real CICIDS2017 Friday-DDoS flows, same split (values in %)", fontsize=8.6)
    tr = [b[n]["train_seconds"] for n in names]
    ax[1].barh(x, tr, color=PURPLE)
    for i, v in enumerate(tr):
        ax[1].text(v + 0.1, i, f"{v:.2f} s", va="center", fontsize=7)
    ax[1].set_yticks(x)
    ax[1].set_yticklabels([""] * len(names))
    ax[1].invert_yaxis()
    ax[1].set_xlabel("training time (s)")
    ax[1].set_title("Training time", fontsize=8.6)
    fig.tight_layout()
    save(fig, "f03_classifier_comparison.png")


def f04_importance():
    cols = list(IMP)
    real = REAL["real_rf_importance"]
    order = np.argsort([IMP[c] for c in cols])
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    y = np.arange(len(cols))
    ax.barh(y + 0.19, [IMP[cols[i]] for i in order], 0.38, color=ORANGE, label="Shipped model (synthetic data)")
    ax.barh(y - 0.19, [real[cols[i]] for i in order], 0.38, color=TEAL, label="RF retrained on real flows")
    ax.set_yticks(y)
    ax.set_yticklabels([cols[i] for i in order], fontsize=7.5)
    ax.set_xlabel("Gini importance")
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    ax.set_title("Which features each forest relies on", fontsize=9)
    save(fig, "f04_feature_importance_compare.png")


def f05_ablation():
    a = REAL["ablation_seed42"]
    names = list(a)
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    acc = [a[n]["accuracy"] for n in names]
    fpr = [a[n]["fpr"] for n in names]
    x = np.arange(len(names))
    ax.bar(x - 0.2, acc, 0.4, color=NAVY, label="Accuracy")
    ax.bar(x + 0.2, fpr, 0.4, color=ORANGE, label="False-positive rate")
    for i, (p, q) in enumerate(zip(acc, fpr)):
        ax.text(i - 0.2, p + 0.01, f"{p * 100:.2f}", ha="center", fontsize=6.6)
        ax.text(i + 0.2, q + 0.01, f"{q * 100:.2f}", ha="center", fontsize=6.6)
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=7.4)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=7.5, frameon=False)
    ax.set_title("Feature-group ablation, RF on real flows (values in %)", fontsize=9)
    save(fig, "f05_feature_ablation.png")


def f06_confusions():
    s = REAL["shipped_on_real_all"]
    r = REAL["real_rf_seed42"]
    fig, ax = plt.subplots(1, 3, figsize=(9.0, 3.1))
    mats = [("Shipped model, its own\nsynthetic test (4,800)", np.array(CM)), ("Shipped model, real\nflows (225,745)", np.array([[s["tn"], s["fp"]], [s["fn"], s["tp"]]])),
            ("RF retrained on real flows,\n20 % test (45,149)", np.array([[r["tn"], r["fp"]], [r["fn"], r["tp"]]]))]
    for a, (t, m) in zip(ax, mats):
        a.imshow(m / m.sum(axis=1, keepdims=True), cmap="Blues", vmin=0, vmax=1)
        for i in range(2):
            for j in range(2):
                a.text(j, i, f"{m[i, j]:,}", ha="center", va="center", fontsize=9, color="white" if m[i, j] / m[i].sum() > 0.5 else "black")
        a.set_xticks([0, 1])
        a.set_yticks([0, 1])
        a.set_xticklabels(["Benign", "Attack"], fontsize=8)
        a.set_yticklabels(["Benign", "Attack"], fontsize=8)
        a.set_xlabel("predicted", fontsize=8)
        a.set_ylabel("actual", fontsize=8)
        a.set_title(t, fontsize=8)
        a.grid(False)
    fig.tight_layout()
    save(fig, "f06_confusion_matrices.png")


def f07_severity_by_style():
    w = WIN["window_5s"]["by_style"]
    styles = ["benign", "flood", "carpet", "slow"]
    sev = ["Low", "Medium", "High", "Critical"]
    cols = [TEAL, "#E5B13A", ORANGE, RED]
    fig, ax = plt.subplots(figsize=(7.8, 3.5))
    bottom = np.zeros(4)
    for s, c in zip(sev, cols):
        v = np.array([w[st]["severity_counts"][s] / w[st]["n"] for st in styles])
        ax.bar(styles, v, bottom=bottom, color=c, label=s)
        for i, val in enumerate(v):
            if val > 0.06:
                ax.text(i, bottom[i] + val / 2, f"{val * 100:.0f} %", ha="center", va="center", fontsize=7, color="white")
        bottom += v
    ax.set_ylabel("share of windows")
    ax.set_title("Severity assigned per traffic style (5 s windows, 4,000 simulated windows)", fontsize=9)
    ax.legend(ncol=4, fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    save(fig, "f07_severity_by_style.png")


def f08_latency():
    comps = [("aggregate", "aggregate_ms"), ("RF predict", "predict_ms"), ("risk + severity", "risk_severity_ms"), ("mitigation decision\n(+ SQLite write)", "mitigate_ms"), ("store detection\n(SQLite)", "db_ms")]
    fig, ax = plt.subplots(1, 2, figsize=(8.8, 3.4), gridspec_kw={"width_ratios": [1.6, 1]})
    p50 = [LAT[k]["p50"] for _, k in comps]
    p95 = [LAT[k]["p95"] for _, k in comps]
    x = np.arange(len(comps))
    ax[0].bar(x - 0.2, p50, 0.4, color=TEAL, label="median")
    ax[0].bar(x + 0.2, p95, 0.4, color=ORANGE, label="95th percentile")
    for i, (a, b) in enumerate(zip(p50, p95)):
        ax[0].text(i - 0.2, a + 4, f"{a:.1f}", ha="center", fontsize=6.6)
        ax[0].text(i + 0.2, b + 4, f"{b:.0f}", ha="center", fontsize=6.6)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels([c for c, _ in comps], fontsize=6.6)
    ax[0].set_ylabel("ms per window (600 windows)")
    ax[0].legend(fontsize=7, frameon=False)
    ax[0].set_title("Where the time goes (host CPU at 100 % from other jobs)", fontsize=8.4)
    a1 = LAT["single_inference_ms_n_jobs_-1"]["p50"]
    a2 = LAT["single_inference_ms_n_jobs_1"]["p50"]
    ax[1].bar(["n_jobs=-1\n(as shipped)", "n_jobs=1"], [a1, a2], color=[ORANGE, TEAL], width=0.5)
    for i, v in enumerate([a1, a2]):
        ax[1].text(i, v + 5, f"{v:.0f} ms", ha="center", fontsize=8)
    ax[1].set_ylabel("single-window inference (ms)")
    ax[1].set_title("Cost of the saved n_jobs=-1", fontsize=8.4)
    fig.tight_layout()
    save(fig, "f08_latency_breakdown.png")


def f09_api():
    rows = [r for r in API["latency"] if r["method"] == "GET"][:9]
    names = [r["path"].replace("/api/", "").replace("/static/results/", "img/") for r in rows]
    fig, ax = plt.subplots(figsize=(8.0, 3.3))
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [r["p50_ms"] for r in rows], 0.4, color=TEAL, label="median")
    ax.bar(x + 0.2, [r["p95_ms"] for r in rows], 0.4, color=ORANGE, label="95th percentile")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=28, ha="right", fontsize=7)
    ax.set_ylabel("ms (127.0.0.1, 100 calls each)")
    ax.legend(fontsize=7.5, frameon=False)
    ax.set_title("REST API latency over real HTTP", fontsize=9)
    save(fig, "f09_api_latency.png")


def f10_real_windows():
    """Real-trained flow model vs windows, and hybrid recipe: how the flow/window scale matters."""
    cross = REAL["real_rf_on_sim_windows"]["window_10s"]
    hyb = HYB["hybrid_on_sim_windows"]["window_10s"]
    ship = WIN["window_10s"]["ml_only"]
    labs = ["Retrained on real\nflows only", "Shipped (synthetic\n+ window rows)", "Real flows + window\nrows (product recipe)"]
    rec = [cross["recall"], ship["recall"], hyb["recall"]]
    fp = [cross["fpr"], ship["fpr"], hyb["fpr"]]
    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    x = np.arange(3)
    ax.bar(x - 0.2, rec, 0.4, color=NAVY, label="attack recall on 10 s windows")
    ax.bar(x + 0.2, fp, 0.4, color=ORANGE, label="false-positive rate")
    for i, (a, b) in enumerate(zip(rec, fp)):
        ax.text(i - 0.2, a + 0.02, f"{a * 100:.1f}", ha="center", fontsize=7.5)
        ax.text(i + 0.2, b + 0.02, f"{b * 100:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=7.6)
    ax.set_ylim(0, 1.12)
    ax.legend(fontsize=7.5, frameon=False, loc="center right")
    ax.set_title("Flow-scale vs window-scale training rows (simulator windows, values in %)", fontsize=8.6)
    save(fig, "f10_flow_vs_window_scale.png")


if __name__ == "__main__":
    f01_domain_gap(); f02_window_size(); f03_baselines(); f04_importance(); f05_ablation(); f06_confusions()
    f07_severity_by_style(); f08_latency(); f09_api(); f10_real_windows()
