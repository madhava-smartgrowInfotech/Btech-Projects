"""Results charts from the real metric files (experiments/*.json, latency measurements) -> docs/charts/*.png."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "charts")
os.makedirs(OUT, exist_ok=True)
G, GR, BL, AM, RD, PU = "#15803d", "#64748b", "#0369a1", "#b45309", "#b91c1c", "#6d28d9"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True, "font.family": "DejaVu Sans"})

ev = json.load(open(os.path.join(ROOT, "experiments", "eval", "metrics.json")))
tr = json.load(open(os.path.join(ROOT, "experiments", "metrics.json")))
det = ev["detection"]
tp_ = det["taxpayer"]
LAT = json.load(open(os.path.join(ROOT, "experiments", "latency.json")))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def precision_at_k():
    ks = ["10", "25", "50", "79"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    x = np.arange(len(ks)); w = 0.2
    series = [("TaxSentinel (all layers)", tp_["model"], G), ("Graph + invoice only", tp_["ablation"]["graph_and_invoice_only"], BL),
              ("JEPA + behaviour only", tp_["ablation"]["jepa_only"], PU), ("Rule baseline R1-R5", tp_["rule_baseline"], GR)]
    for i, (n, d, c) in enumerate(series):
        v = [d["precision_at_k"][k] for k in ks]
        b = ax.bar(x + (i - 1.5) * w, v, w, label=n, color=c)
        for r, val in zip(b, v):
            ax.text(r.get_x() + r.get_width() / 2, val + 0.01, f"{val:.2f}", ha="center", fontsize=6.5, rotation=90, va="bottom")
    ax.set_xticks(x); ax.set_xticklabels([f"Top {k}" for k in ks]); ax.set_ylim(0, 1.3); ax.set_yticks([0, .25, .5, .75, 1])
    ax.set_ylabel("Precision@k"); ax.legend(fontsize=7.5, ncol=2, loc="upper center", frameon=False)
    save(fig, "c01_precision_at_k.png")


def method_comparison():
    names = ["TaxSentinel", "Graph +\ninvoice only", "JEPA +\nbehaviour only", "Rule baseline"]
    ds = [tp_["model"], tp_["ablation"]["graph_and_invoice_only"], tp_["ablation"]["jepa_only"], tp_["rule_baseline"]]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    x = np.arange(4); w = 0.26
    for i, (key, lab, c) in enumerate([("f1", "F1 at threshold", G), ("roc_auc", "ROC-AUC", BL), ("average_precision", "Average precision", AM)]):
        v = [d["at_threshold"]["f1"] if key == "f1" else d[key] for d in ds]
        b = ax.bar(x + (i - 1) * w, v, w, label=lab, color=c)
        for r, val in zip(b, v):
            ax.text(r.get_x() + r.get_width() / 2, val + 0.01, f"{val:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8.5); ax.set_ylim(0, 1.15); ax.set_ylabel("Score")
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="upper center")
    save(fig, "c02_method_comparison.png")


def per_pattern():
    pats = ["circular_trading", "shell_entity", "fake_invoice_buyer", "itc_spike"]
    labs = ["Circular\ntrading (21)", "Shell\nentity (27)", "Fake-invoice\nbuyer (19)", "ITC\nspike (12)"]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = np.arange(4); w = 0.36
    m = [det["per_pattern"][p]["model_recall"] for p in pats]; b = [det["per_pattern"][p]["baseline_recall"] for p in pats]
    r1 = ax.bar(x - w / 2, m, w, label="TaxSentinel", color=G); r2 = ax.bar(x + w / 2, b, w, label="Rule baseline", color=GR)
    for rs in (r1, r2):
        for r in rs:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.01, f"{r.get_height():.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8.5); ax.set_ylim(0, 1.2); ax.set_ylabel("Recall at flag threshold")
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=2)
    save(fig, "c03_recall_by_pattern.png")


def training_loss():
    h = tr["loss_history"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.plot(range(1, len(h) + 1), h, color=G, lw=1.8)
    ax.axhline(h[-1], color=GR, lw=0.8, ls="--")
    ax.annotate(f"final loss {h[-1]:.4f}", (len(h), h[-1]), (62, h[-1] + 0.06), fontsize=8.5, color=GR)
    pk = int(np.argmax(h))
    ax.annotate(f"peak {h[pk]:.3f} (epoch {pk + 1})", (pk + 1, h[pk]), (pk + 18, h[pk] - 0.01), fontsize=8.5, color=RD, arrowprops=dict(arrowstyle="-", color=RD, lw=0.8))
    ax.set_xlabel("Epoch"); ax.set_ylabel("Prediction loss (MSE in embedding space)")
    save(fig, "c04_jepa_training_loss.png")


def latency():
    if not LAT:
        return
    items = sorted(LAT.items(), key=lambda kv: kv[1][0])
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    y = np.arange(len(items))
    ax.barh(y, [v[0] for _, v in items], color=BL, label="median")
    ax.scatter([v[1] for _, v in items], y, color=RD, zorder=3, s=14, label="maximum of 20 calls")
    for yi, (k, v) in zip(y, items):
        ax.text(v[0] + 0.4, yi, f"{v[0]:.1f} ms", va="center", fontsize=7.5)
    ax.set_yticks(y); ax.set_yticklabels([k for k, _ in items], fontsize=8)
    ax.set_xlabel("Response time (ms), 20 sequential calls each"); ax.legend(frameon=False, fontsize=8, loc="lower right")
    save(fig, "c05_api_latency.png")


def paysim():
    p = det and ev["paysim"]
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.4))
    axs[0].bar(["JEPA\n(unlabelled)", "Amount\nranking"], [p["roc_auc"], p["amount_baseline"]["roc_auc"]], color=[G, GR])
    for i, v in enumerate([p["roc_auc"], p["amount_baseline"]["roc_auc"]]):
        axs[0].text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=9)
    axs[0].set_ylim(0, 1.1); axs[0].set_title("ROC-AUC", fontsize=10)
    v2 = [p["precision_at_k"]["100"], p["amount_baseline"]["precision_at_k"]["100"]]
    axs[1].bar(["JEPA\n(unlabelled)", "Amount\nranking"], v2, color=[G, GR])
    for i, v in enumerate(v2):
        axs[1].text(i, v + 0.008, f"{v:.2f}", ha="center", fontsize=9)
    axs[1].set_ylim(0, 0.4); axs[1].set_title("Precision@100", fontsize=10)
    fig.suptitle("PaySim transfer check (100,000 transactions, 134 fraud)", fontsize=10)
    save(fig, "c06_paysim_transfer.png")


def invoice_level():
    m = det["invoice"]["model"]["at_threshold"]; b = det["invoice"]["rule_baseline"]["at_threshold"]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = np.arange(3); w = 0.36
    r1 = ax.bar(x - w / 2, [m["precision"], m["recall"], m["f1"]], w, label="TaxSentinel invoice score >= 0.5", color=G)
    r2 = ax.bar(x + w / 2, [b["precision"], b["recall"], b["f1"]], w, label="Not reported in supplier's GSTR-1", color=GR)
    for rs in (r1, r2):
        for r in rs:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.01, f"{r.get_height():.2f}", ha="center", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(["Precision", "Recall", "F1"]); ax.set_ylim(0, 1.25)
    ax.legend(frameon=False, fontsize=8, loc="upper center")
    save(fig, "c07_invoice_level.png")


def confusion():
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.4))
    for ax, name, d in [(axs[0], "TaxSentinel", tp_["model"]["at_threshold"]), (axs[1], "Rule baseline R1-R5", tp_["rule_baseline"]["at_threshold"])]:
        tn = 600 - 79 - d["fp"]
        cm = np.array([[tn, d["fp"]], [d["fn"], d["tp"]]])
        ax.imshow(np.log1p(cm), cmap="Greens", vmin=0, vmax=7)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]}", ha="center", va="center", fontsize=14, fontweight="bold", color="white" if np.log1p(cm[i, j]) > 4.5 else "#0f172a")
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1]); ax.set_xticklabels(["pred. legit", "pred. fraud"], fontsize=8.5); ax.set_yticklabels(["legit", "fraud"], fontsize=8.5)
        ax.set_title(name, fontsize=10); ax.grid(False)
    fig.suptitle("Taxpayer-level confusion matrices (600 taxpayers, 79 fraud)", fontsize=10)
    save(fig, "c08_confusion_matrices.png")


def seed_and_threshold():
    p = os.path.join(ROOT, "experiments", "seed_study.json")
    if not os.path.exists(p):
        return
    s = json.load(open(p))
    sw = s["threshold_sweep_seed42"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    th = [r["threshold"] for r in sw]
    for key, c, lab in [("precision", BL, "Precision"), ("recall", AM, "Recall"), ("f1", G, "F1")]:
        ax.plot(th, [r[key] for r in sw], marker="o", color=c, lw=2, label=lab)
    ax.axvline(0.5, color=GR, ls="--", lw=1); ax.text(0.505, 0.06, "chosen flag\nthreshold 0.5", fontsize=8, color=GR)
    ax.set_xlabel("Risk threshold"); ax.set_ylabel("Score"); ax.set_ylim(0, 1.05); ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    save(fig, "c09_threshold_sweep.png")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    bins = np.linspace(0, 1, 21)
    ax.hist(s["risk_scores_seed42"]["legit"], bins=bins, color=GR, alpha=0.85, label="legitimate (521)")
    ax.hist(s["risk_scores_seed42"]["fraud"], bins=bins, color=RD, alpha=0.85, label="injected fraud (79)")
    ax.set_yscale("log"); ax.axvline(0.5, color="black", ls="--", lw=1)
    ax.set_xlabel("Combined risk score"); ax.set_ylabel("Taxpayers (log scale)"); ax.legend(frameon=False, fontsize=8.5)
    save(fig, "c10_risk_distribution.png")
    seeds = list(s["seeds"].keys())
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = np.arange(len(seeds)); w = 0.38
    ax.bar(x - w / 2, [s["seeds"][k]["f1"] for k in seeds], w, color=G, label="TaxSentinel F1")
    ax.bar(x + w / 2, [s["seeds"][k]["base_f1"] for k in seeds], w, color=GR, label="Rule baseline F1")
    for i, k in enumerate(seeds):
        ax.text(i - w / 2, s["seeds"][k]["f1"] + 0.01, f"{s['seeds'][k]['f1']:.2f}", ha="center", fontsize=8)
        ax.text(i + w / 2, s["seeds"][k]["base_f1"] + 0.01, f"{s['seeds'][k]['base_f1']:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([f"seed {k}" for k in seeds]); ax.set_ylim(0, 1.2); ax.set_ylabel("F1 at flag threshold")
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper center")
    save(fig, "c11_seed_study.png")
    lm = s["layer_means_seed42"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    layers = ["jepa", "behaviour", "network", "invoice"]
    x = np.arange(4)
    ax.bar(x - 0.19, [lm[l]["fraud"] for l in layers], 0.38, color=RD, label="injected fraud")
    ax.bar(x + 0.19, [lm[l]["legit"] for l in layers], 0.38, color=GR, label="legitimate")
    for i, l in enumerate(layers):
        ax.text(i - 0.19, lm[l]["fraud"] + 0.01, f"{lm[l]['fraud']:.2f}", ha="center", fontsize=8)
        ax.text(i + 0.19, lm[l]["legit"] + 0.01, f"{lm[l]['legit']:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(["JEPA\ndeviation", "Behaviour\nlayer", "Network\nlayer", "Invoice\nlayer"]); ax.set_ylabel("Mean layer score (0-1)"); ax.set_ylim(0, 1.1)
    ax.legend(frameon=False, fontsize=8.5)
    save(fig, "c12_layer_scores.png")


if __name__ == "__main__":
    for f in (precision_at_k, method_comparison, per_pattern, training_loss, latency, paysim, invoice_level, confusion, seed_and_threshold):
        f()
