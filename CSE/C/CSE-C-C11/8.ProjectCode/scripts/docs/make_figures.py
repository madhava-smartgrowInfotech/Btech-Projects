"""Result charts for the documents, drawn from experiments/metrics.json and experiments/api_latency.json into docs/figures/ (matplotlib, 150 dpi).

    python -m scripts.docs.make_figures
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#5B6B7F", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.titlesize": 10, "axes.titleweight": "bold"})


def save(fig, name):
    os.makedirs(F.FIGS, exist_ok=True)
    fig.savefig(os.path.join(F.FIGS, name), dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def f01():
    tiers = ["A  seed-like", "B  statement strings", "C  unseen merchants"]
    series = [("TF-IDF + LR (shipped)", F.CLS["tfidf_lr"], NAVY), ("Keyword table", F.CLS["keyword_table"], ORANGE), ("Majority class", F.CLS["majority_class"], GREY)]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    for i, (name, d, c) in enumerate(series):
        v = [d["accuracy_by_tier"][t] * 100 for t in "ABC"]
        b = ax.bar(x + (i - 1) * 0.26, v, 0.26, label=f"{name} (overall {d['accuracy'] * 100:.1f} %)", color=c)
        for r, val in zip(b, v):
            ax.text(r.get_x() + r.get_width() / 2, val + 1.5, f"{val:.0f}", ha="center", fontsize=7.5)
    ax.set_xticks(x, tiers)
    ax.set_ylabel("accuracy on the probe tier (%)")
    ax.set_ylim(0, 112)
    ax.set_title("Expense categoriser on the 198-description probe set (66 per tier)")
    ax.legend(fontsize=7.5, frameon=False, loc="upper right")
    save(fig, "f01_classifier_tiers.png")


def f02():
    labels = F.CLS["confusion_labels"]
    cm = np.array(F.CLS["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(6.6, 5.6))
    ax.grid(False)
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j]:
                ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8, color="white" if cm[i, j] > cm.max() * 0.55 else "black")
    ax.set_xlabel("predicted category")
    ax.set_ylabel("true category")
    ax.set_title("Confusion matrix, probe set (rows = true, 18 per class)")
    fig.colorbar(im, fraction=0.046, pad=0.03)
    save(fig, "f02_confusion_matrix.png")


def f03():
    pc = F.CLS["per_category"]
    names = list(pc)
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8.2, 3.5))
    for i, (key, c) in enumerate((("precision", BLUE), ("recall", ORANGE), ("f1", TEAL))):
        ax.bar(x + (i - 1) * 0.27, [pc[n][key] for n in names], 0.27, label=key.capitalize() if key != "f1" else "F1", color=c)
    ax.set_xticks(x, names, rotation=30, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("score")
    ax.set_title("Per-category precision, recall and F1 (probe set) - Transport precision is the outlier")
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="lower right")
    save(fig, "f03_per_category_prf.png")


def f04():
    cc = [c for c in F.CLS["confidence_curve"] if c["accuracy_on_kept"] is not None]
    th = [c["threshold"] for c in cc]
    cov = [c["coverage"] * 100 for c in cc]
    acc = [c["accuracy_on_kept"] * 100 for c in cc]
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    ax.plot(th, acc, "-o", color=NAVY, label="accuracy on kept predictions", ms=4)
    ax.plot(th, cov, "-s", color=ORANGE, label="share of items kept (coverage)", ms=4)
    ax.set_xlabel("minimum top-class probability")
    ax.set_ylabel("%")
    ax.set_title("Abstaining below a confidence threshold (not applied in the app)")
    ax.legend(fontsize=8, frameon=False)
    save(fig, "f04_confidence_coverage.png")


def f05():
    lc = F.CLS["learning_from_corrections"]
    ks = [d["corrections"] for d in lc]
    m = np.array([d["tier_C_accuracy_mean"] for d in lc]) * 100
    s = np.array([d["tier_C_accuracy_sd"] for d in lc]) * 100
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4), gridspec_kw={"width_ratios": [1.5, 1]})
    ax[0].errorbar(ks, m, yerr=s, fmt="-o", color=NAVY, capsize=3, ms=4)
    ax[0].set_ylim(0, 50)
    ax[0].set_xlabel("user corrections added (random tier-C items)")
    ax[0].set_ylabel("accuracy on the rest of tier C (%)")
    ax[0].set_title("(a) New merchants: little gain")
    r = F.CLS["repeat_merchant_learning"]
    ax[1].bar(["before", "after one\ncorrection"], [r["accuracy_before_correction"] * 100, r["accuracy_after_one_correction"] * 100], color=[GREY, TEAL], width=0.55)
    for i, v in enumerate([r["accuracy_before_correction"] * 100, r["accuracy_after_one_correction"] * 100]):
        ax[1].text(i, v + 2, f"{v:.1f}", ha="center", fontsize=8.5)
    ax[1].set_ylim(0, 115)
    ax[1].set_title("(b) Same merchant, other wording")
    save(fig, "f05_learning_from_corrections.png")


def f06():
    bt = F.FC["demo_backtest"]
    months = bt["months"]
    actual = bt["actual"]
    steps = bt["steps"]
    fig, ax = plt.subplots(figsize=(7.4, 3.7))
    ax.plot(months, actual, "-o", color="black", lw=2, label="actual monthly expenses")
    xs = [s["predict_month"] for s in steps]
    for key, c, mk in (("linear_trend (app)", ORANGE, "D"), ("mean_of_all", BLUE, "s"), ("mean_of_last_3", TEAL, "^"), ("last_value", GREY, "v")):
        ax.plot(xs, [s[key] for s in steps], marker=mk, color=c, lw=1.4, ls="--", label=f"{key.replace('_', ' ')}  (MAPE {bt['mape_pct'][key]:.1f} %)")
    ax.set_ylabel("INR per month")
    ax.set_title("Demo account: one-step-ahead forecasts of months 4-6 (only three test points)")
    ax.legend(fontsize=7.5, frameon=False)
    save(fig, "f06_forecast_backtest.png")


def f07():
    rows = F.FC["sim_mape_by_noise_pct"]
    x = [r["noise_ratio"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    for key, c, mk in (("linear_trend (app)", ORANGE, "D"), ("mean_of_all", BLUE, "s"), ("mean_of_last_3", TEAL, "^"), ("last_value", GREY, "v")):
        ax.plot(x, [r[key] for r in rows], marker=mk, color=c, label=key.replace("_", " "), lw=1.6)
    ax.set_xlabel("noise (sd / level)")
    ax.set_ylabel("one-step-ahead MAPE (%)")
    ax.set_title("Synthetic simulation (2,000 users per point): MAPE against noise")
    ax.legend(fontsize=8, frameon=False)
    save(fig, "f07_sim_mape_noise.png")


def f08():
    rows = F.FC["sim_mape_by_history_pct_noise_0.10"]
    x = [r["history_months"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    for key, c, mk in (("linear_trend (app)", ORANGE, "D"), ("mean_of_all", BLUE, "s"), ("mean_of_last_3", TEAL, "^"), ("last_value", GREY, "v")):
        ax.plot(x, [r[key] for r in rows], marker=mk, color=c, label=key.replace("_", " "), lw=1.6)
    ax.axvline(3, color=RED, ls=":", lw=1)
    ax.text(3.1, ax.get_ylim()[1] * 0.93, "app minimum (3 months)", color=RED, fontsize=7.5)
    ax.set_xlabel("months of history")
    ax.set_ylabel("one-step-ahead MAPE (%)")
    ax.set_title("Synthetic simulation, noise 0.10: MAPE against history length")
    ax.legend(fontsize=8, frameon=False)
    save(fig, "f08_sim_mape_history.png")


def f09():
    sw = F.HL["sweeps"]
    spec = [("savings_rate", "savings rate (% of income)"), ("monthly_expenses", "monthly expenses (INR)"), ("total_balance", "balance (INR)"),
            ("goal_progress", "goal progress (%)"), ("asset_types", "distinct asset types")]
    fig, axes = plt.subplots(1, 5, figsize=(12.4, 2.9), sharey=True)
    for a, (k, lab) in zip(axes, spec):
        xs, ys = zip(*sw[k])
        a.plot(xs, ys, "-o", color=NAVY, ms=3.5)
        a.set_xlabel(lab, fontsize=8)
    axes[0].set_ylabel("health score")
    axes[0].set_ylim(45, 92)
    fig.suptitle(f"Health-score sensitivity from a baseline profile (score {F.HL['baseline_profile_score']})", fontsize=10.5, y=1.04)
    save(fig, "f09_health_sensitivity.png")


def f10():
    rc = F.HL["rating_counts"]
    order = ["Critical", "Needs Improvement", "Fair", "Good", "Excellent"]
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    cols = [RED, ORANGE, "#C9A227", TEAL, NAVY]
    b = ax.bar(order, [rc[o] for o in order], color=cols)
    for r, o in zip(b, order):
        ax.text(r.get_x() + r.get_width() / 2, rc[o] + 25, str(rc[o]), ha="center", fontsize=8.5)
    ax.set_ylabel("profiles (of 5,000)")
    ax.set_title("Ratings of 5,000 random profiles (mean score 60.3)")
    save(fig, "f10_health_distribution.png")


def f11():
    items = [(k, v) for k, v in F.LAT.items() if isinstance(v, dict) and "median_ms" in v]
    items.sort(key=lambda kv: kv[1]["median_ms"])
    names = [k for k, _ in items]
    med = [v["median_ms"] for _, v in items]
    p95 = [v["p95_ms"] for _, v in items]
    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    ax.barh(y + 0.2, p95, 0.4, color="#9DB7D5", label="p95")
    ax.barh(y - 0.2, med, 0.4, color=NAVY, label="median")
    ax.set_yticks(y, names, fontsize=7.5)
    ax.set_xlabel("milliseconds (127.0.0.1, single user, warm server)")
    ax.set_title("API latency per endpoint (30 repetitions; 10 for reports and import)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(axis="y", alpha=0)
    save(fig, "f11_api_latency.png")


def f12():
    a = F.AS
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    labels = ["answerable questions\nanswered from data", "answerable questions\nmissed (fixed help text)", "off-topic questions\ndeclined", "off-topic questions\nwrongly answered"]
    vals = [a["answerable_handled_by_analytics"], a["answerable"] - a["answerable_handled_by_analytics"], a["unanswerable_correctly_declined"], a["unanswerable_wrongly_answered"]]
    b = ax.bar(labels, vals, color=[TEAL, ORANGE, NAVY, RED])
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.3, str(v), ha="center", fontsize=9)
    ax.set_ylim(0, 17)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.set_title("Assistant rule layer on 26 team-written questions")
    save(fig, "f12_assistant_coverage.png")


def f13():
    pc = F.CLS["per_category"]
    seed = F.CLS["seed_per_category"]
    names = list(seed)
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.bar(names, [seed[n] for n in names], color=BLUE)
    for i, n in enumerate(names):
        ax.text(i, seed[n] + 0.1, str(seed[n]), ha="center", fontsize=8)
    ax.set_ylabel("seed examples")
    ax.set_title(f"The whole training set: {F.CLS['seed_examples']} descriptions in {F.CLS['seed_categories']} categories")
    ax.tick_params(axis="x", rotation=30)
    save(fig, "f13_seed_distribution.png")


ALL = [f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13]

if __name__ == "__main__":
    for f in ALL:
        f()
