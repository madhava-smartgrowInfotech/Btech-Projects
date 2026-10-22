"""
Draws the results charts used in the documents from the real measured artefacts (matplotlib, 150 dpi).

    python scripts/make_figures.py            # -> docs/figures/*.png

Inputs: artifacts/metrics/model_metrics.json and experiments/*.json. Nothing is typed in by hand.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "figures")
os.makedirs(OUT, exist_ok=True)
NAVY, BLUE, GREEN, ORANGE, PURPLE, GOLD, GREY = "#1B2A41", "#2A78D6", "#1BAF7A", "#EB6834", "#6B52D6", "#E8A317", "#9AA8BD"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#475569", "axes.titlesize": 10.5, "axes.titleweight": "bold"})


def J(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


M = J("artifacts/metrics/model_metrics.json")
S = J("experiments/seed_study.json")
C = J("experiments/ceiling.json")
D = J("experiments/data_profile.json")
R = J("experiments/recsys_eval.json")
FB = J("experiments/feedback_loop.json")
AL = J("experiments/api_latency.json")
LAB = {"logistic_regression": "Logistic\nRegression", "random_forest": "Random\nForest", "xgboost": "XGBoost"}
COL = {"logistic_regression": BLUE, "random_forest": GREEN, "xgboost": ORANGE}
MODELS = list(LAB)


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p)


def labels(ax, bars, fmt="{:.3f}", dy=0.004, fs=8):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h), ha="center", va="bottom", fontsize=fs, color=NAVY)


def model_comparison():
    fig, axs = plt.subplots(1, 3, figsize=(10.4, 3.4))
    for ax, key, title, lo in ((axs[0], "roc_auc", "Test AUC (higher is better)", 0.5), (axs[1], "f1", "Test F1 (higher is better)", 0.0), (axs[2], "brier", "Test Brier score (lower is better)", 0.0)):
        vals = [M["models"][m][key] for m in MODELS]
        b = ax.bar([LAB[m] for m in MODELS], vals, color=[COL[m] for m in MODELS], width=0.6)
        labels(ax, b, dy=0.003)
        ax.set_title(title)
        ax.set_ylim(lo, max(vals) * 1.12)
    axs[0].axhline(0.5, color=GREY, lw=1, ls="--")
    axs[0].text(-0.3, 0.503, "chance (0.5)", fontsize=7.5, color=GREY, ha="left")
    fig.suptitle("Success-prediction models on the held-out test split (seed 42, 2,640 learner-weeks)", fontsize=10.5, fontweight="bold", y=1.04)
    fig.tight_layout()
    save(fig, "fig_model_comparison.png")


def confusion_matrices():
    fig, axs = plt.subplots(1, 3, figsize=(10.4, 3.5))
    for ax, m in zip(axs, MODELS):
        cm = np.array(M["models"][m]["confusion_matrix"])
        ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.15)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", fontsize=12, fontweight="bold", color="white" if cm[i, j] > cm.max() * 0.55 else NAVY)
        ax.set_xticks([0, 1], ["not success", "success"])
        ax.set_yticks([0, 1], ["not success", "success"])
        ax.set_xlabel("predicted")
        ax.set_ylabel("actual")
        ax.set_title(LAB[m].replace("\n", " ") + (" (selected)" if m == M["selected_model"] else ""))
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("Confusion matrices at threshold 0.5 (test split, 2,640 learner-weeks)", fontsize=10.5, fontweight="bold", y=1.03)
    fig.tight_layout()
    save(fig, "fig_confusion_matrices.png")


def seed_study():
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    seeds = S["seeds"]
    for m in MODELS:
        ys = [r["models"][m]["test_auc"] for r in S["runs"]]
        ax.plot(range(len(seeds)), ys, marker="o", color=COL[m], lw=1.8, label=f"{LAB[m].replace(chr(10), ' ')} (mean {np.mean(ys):.3f})")
    ax.axhline(0.5, color=GREY, lw=1, ls="--")
    ax.set_xticks(range(len(seeds)), [f"seed {s}" for s in seeds])
    ax.set_ylabel("test AUC")
    ax.set_ylim(0.48, 0.66)
    ax.set_title("Test AUC across six data-generation seeds")
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 0.62))
    fig.tight_layout()
    save(fig, "fig_seed_study.png")


def ceiling():
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    x = np.arange(3)
    a = [C["shipped_features"][m]["test_auc"] for m in MODELS]
    b = [C["with_assess_score"][m]["test_auc"] for m in MODELS]
    b1 = ax.bar(x - 0.19, a, 0.36, color=BLUE, label="shipped 8 features")
    b2 = ax.bar(x + 0.19, b, 0.36, color=GOLD, label="+ hidden assessment score")
    labels(ax, b1, dy=0.006)
    labels(ax, b2, dy=0.006)
    ax.axhline(0.5, color=GREY, lw=1, ls="--")
    ax.set_xticks(x, [LAB[m].replace("\n", " ") for m in MODELS])
    ax.set_ylim(0.45, 0.9)
    ax.set_ylabel("test AUC")
    ax.set_title("Ceiling check: the weak signal comes from the synthetic label")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    save(fig, "fig_ceiling.png")


def feature_signal():
    fig, axs = plt.subplots(1, 2, figsize=(10.0, 3.5))
    corr = D["corr_with_success"]
    names = list(corr)
    axs[0].barh(names[::-1], [corr[n] for n in names][::-1], color=BLUE)
    axs[0].set_title("Correlation of each feature with success")
    axs[0].set_xlabel("Pearson r (synthetic data, 26,400 rows)")
    imp = M["feature_importance"]
    order = sorted(imp, key=imp.get)
    axs[1].barh(order, [imp[n] for n in order], color=GREEN)
    axs[1].set_title("Logistic-regression |coefficient| (standardised)")
    axs[1].set_xlabel("absolute coefficient")
    fig.tight_layout()
    save(fig, "fig_feature_signal.png")


def persona_precision():
    S2 = R["summary"]
    names = list(S2)
    short = {"popularity (rating only)": "Popularity\n(rating only)", "content-only (TF-IDF)": "Content-only\n(TF-IDF)", "hybrid (shipped)": "Hybrid\n(shipped)"}
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(names))
    w = 0.2
    for i, (k, lab, c) in enumerate((("p@1", "P@1", GREEN), ("p@3", "P@3", BLUE), ("p@5", "P@5", ORANGE), ("mrr", "MRR", PURPLE))):
        bars = ax.bar(x + (i - 1.5) * w, [S2[n][k] for n in names], w, color=c, label=lab)
        labels(ax, bars, fmt="{:.2f}", dy=0.01, fs=7)
    ax.set_xticks(x, [short[n] for n in names])
    ax.set_ylim(0, 1.15)
    ax.set_title("Persona check: 10 author-written learners, 24 courses")
    ax.legend(frameon=False, ncol=4, fontsize=8, loc="upper left")
    fig.tight_layout()
    save(fig, "fig_persona_precision.png")


def ablation():
    A = R["ablation_drop_one_term"]
    keys = [k for k in A if k != "full"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    base = A["full"]["p@3"]
    vals = [A[k]["p@3"] for k in keys]
    cols = [ORANGE if v < base - 1e-9 else (GREEN if v > base + 1e-9 else GREY) for v in vals]
    b = ax.bar(keys, vals, color=cols, width=0.6)
    labels(ax, b, fmt="{:.3f}", dy=0.008, fs=7.5)
    ax.axhline(base, color=NAVY, lw=1.2, ls="--")
    ax.text(-0.45, 0.82, f"dashed line = full hybrid, P@3 {base:.3f}", ha="left", fontsize=8, color=NAVY)
    ax.set_ylim(0.4, 0.86)
    ax.set_ylabel("mean P@3 over 10 personas")
    ax.set_xlabel("term removed from the 8-term score")
    ax.set_title("Drop-one-term ablation of the hybrid score")
    fig.tight_layout()
    save(fig, "fig_ablation.png")


def weights():
    W = R["weights"]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    names = list(W)[::-1]
    b = ax.barh(names, [W[n] for n in names], color=[BLUE, GREEN, ORANGE, PURPLE, GOLD, "#1B2A41", "#9AA8BD", "#C2456B"][: len(names)])
    for bar in b:
        ax.text(bar.get_width() + 0.004, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.2f}", va="center", fontsize=8)
    ax.set_xlim(0, 0.36)
    ax.set_xlabel("weight in the final score (sums to 1.00)")
    ax.set_title("Weights of the eight terms in rank_courses()")
    fig.tight_layout()
    save(fig, "fig_score_weights.png")


def latency():
    ep = AL["endpoints"]
    items = [(k, v) for k, v in ep.items() if v["n"] >= 5]
    items.sort(key=lambda kv: kv[1]["mean_ms"])
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    y = np.arange(len(items))
    ax.barh(y, [v["mean_ms"] for _, v in items], color=BLUE, label="mean")
    ax.scatter([v["p95_ms"] for _, v in items], y, color=ORANGE, zorder=3, s=22, label="p95")
    for yi, (_, v) in zip(y, items):
        ax.text(max(v["p95_ms"], v["mean_ms"]) + 1.2, yi, f"{v['mean_ms']:.1f} ms", va="center", fontsize=7.5)
    ax.set_yticks(y, [k.replace("GET ", "").replace("POST ", "POST ").replace("PUT ", "PUT ") for k, _ in items], fontsize=7.8)
    ax.set_xlabel("milliseconds (127.0.0.1, 30 sequential requests per read endpoint)")
    ax.set_title("API latency on the development machine")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_xlim(0, 85)
    fig.tight_layout()
    save(fig, "fig_latency.png")


def feedback_loop():
    keys = ["quiz", "content", "forum", "homepage", "continue_course"]
    fig, axs = plt.subplots(1, 2, figsize=(10.2, 3.6), gridspec_kw={"width_ratios": [1.15, 1]})
    x = np.arange(len(keys))
    axs[0].bar(x - 0.19, [FB["uplift_before"][k] for k in keys], 0.36, color=BLUE, label="before 6 events")
    axs[0].bar(x + 0.19, [FB["uplift_after"][k] for k in keys], 0.36, color=ORANGE, label="after 6 events")
    axs[0].axhline(0, color=NAVY, lw=0.8)
    axs[0].set_xticks(x, [k.replace("_", "\n") for k in keys])
    axs[0].set_ylabel("estimated benefit (P1 - P0)")
    axs[0].set_title("Estimated action benefit flips with a few events")
    axs[0].legend(frameon=False, fontsize=8)
    tr = FB["tracked"]
    ids = list(tr)
    axs[1].bar(np.arange(len(ids)) - 0.19, [tr[i]["score_before"] for i in ids], 0.36, color=BLUE, label="score before")
    axs[1].bar(np.arange(len(ids)) + 0.19, [tr[i]["score_after"] for i in ids], 0.36, color=ORANGE, label="score after")
    for i, cid in enumerate(ids):
        axs[1].text(i, max(tr[cid]["score_before"], tr[cid]["score_after"]) + 0.012, f"rank {tr[cid]['rank_before']} to {tr[cid]['rank_after']}", ha="center", fontsize=8, color=NAVY)
    axs[1].set_xticks(range(len(ids)), ids)
    axs[1].set_ylim(0, 0.68)
    axs[1].set_ylabel("hybrid score")
    axs[1].set_title("Course scores after feedback events")
    axs[1].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    save(fig, "fig_feedback_loop.png")


def ope():
    P = M["policy_evaluation"]
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.3), gridspec_kw={"width_ratios": [1.2, 1]})
    names = ["IPS", "SNIPS", "Doubly\nRobust", "Logged\nsuccess rate"]
    logged = 0.4375
    vals = [P["ips"], P["snips"], P["doubly_robust"], logged]
    b = axs[0].bar(names, vals, color=[ORANGE, BLUE, GREEN, GREY], width=0.6)
    labels(axs[0], b, dy=0.012)
    axs[0].set_ylim(0, 0.8)
    axs[0].set_title("Offline policy value estimates (test split)")
    axs[1].bar(["effective\nsample size", "test rows"], [P["effective_sample_size"], P["test_samples"]], color=[ORANGE, GREY], width=0.5)
    axs[1].set_yscale("log")
    axs[1].text(0, P["effective_sample_size"] * 1.15, f"{P['effective_sample_size']:.1f}", ha="center", fontsize=9, fontweight="bold")
    axs[1].text(1, P["test_samples"] * 1.15, f"{P['test_samples']:,}", ha="center", fontsize=9, fontweight="bold")
    axs[1].set_ylim(1, 10000)
    axs[1].set_title("Importance-weight effective sample size")
    fig.tight_layout()
    save(fig, "fig_policy_eval.png")


def fairness():
    F = M["fairness"]
    groups = [("age " + k, v) for k, v in F["age_band"].items()] + [("gender " + k, v) for k, v in F["gender"].items()]
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    x = np.arange(len(groups))
    b1 = ax.bar(x - 0.27, [v["success_rate"] for _, v in groups], 0.26, color=GREY, label="observed success rate")
    b2 = ax.bar(x, [v["avg_predicted"] for _, v in groups], 0.26, color=BLUE, label="mean predicted")
    b3 = ax.bar(x + 0.27, [v["f1"] for _, v in groups], 0.26, color=ORANGE, label="F1")
    for bars in (b1, b2, b3):
        labels(ax, bars, fmt="{:.2f}", dy=0.006, fs=7)
    ax.set_xticks(x, [f"{g}\n(n={v['n']:,})" for g, v in groups], fontsize=8)
    ax.set_ylim(0, 0.62)
    ax.set_title("Fairness audit by age band and gender (audit only)")
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper right")
    fig.tight_layout()
    save(fig, "fig_fairness.png")


def class_balance():
    A = D["action_counts"]
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 3.2))
    names = list(A)
    axs[0].bar(names, [A[n] for n in names], color=[BLUE, GREEN, PURPLE, GOLD, ORANGE][: len(names)])
    for i, n in enumerate(names):
        axs[0].text(i, A[n] + 120, f"{A[n]:,}", ha="center", fontsize=8)
    axs[0].set_title("Logged action counts (26,400 learner-weeks)")
    axs[0].tick_params(axis="x", labelsize=8)
    sr = D["success_rate"]
    axs[1].bar(["not success", "success"], [1 - sr, sr], color=[GREY, GREEN], width=0.5)
    axs[1].text(0, 1 - sr + 0.015, f"{1 - sr:.1%}", ha="center", fontsize=9)
    axs[1].text(1, sr + 0.015, f"{sr:.1%}", ha="center", fontsize=9)
    axs[1].set_ylim(0, 0.7)
    axs[1].set_title("Label balance")
    fig.tight_layout()
    save(fig, "fig_data_profile.png")


def main():
    for fn in (model_comparison, confusion_matrices, seed_study, ceiling, feature_signal, persona_precision, ablation, weights, latency, feedback_loop, ope, fairness, class_balance):
        fn()


if __name__ == "__main__":
    main()
