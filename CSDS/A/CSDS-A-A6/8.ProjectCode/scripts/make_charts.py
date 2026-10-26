"""Result charts for the documents (PNG, 150 dpi) into docs/charts/, drawn only from experiments/**/metrics.json and the cached embeddings.

    venv\\Scripts\\python.exe scripts\\make_charts.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments"
OUT = ROOT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

INDIGO, BLUE, GREEN, AMBER, ROSE, GREY, INK = "#4a4ad0", "#3b82c4", "#2f9e6e", "#e0a030", "#d9576b", "#9aa5ba", "#1b2238"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#44506b", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})


def load(p):
    return json.loads((EXP / p).read_text(encoding="utf-8"))


cls = load("classification/metrics.json")
rules = load("rules/metrics.json")
corpus = load("corpus/metrics.json")
api = load("api/metrics.json")
parity = load("parity/metrics.json")


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def per_category():
    items = sorted(cls["per_category"].items(), key=lambda kv: kv[1]["recall"])
    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    names = [k for k, _ in items]
    rec = [v["recall"] for _, v in items]
    ax.barh(names, rec, color=[ROSE if r < 0.7 else AMBER if r < 0.9 else GREEN for r in rec])
    for i, r in enumerate(rec):
        ax.text(r + 0.01, i, f"{r:.2f}", va="center", fontsize=7.5)
    ax.axvline(cls["centroid"]["top1"], color=INK, ls="--", lw=1)
    ax.text(cls["centroid"]["top1"] + 0.005, -0.9, f"overall top-1 {cls['centroid']['top1']:.3f}", fontsize=7.5, color=INK)
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("Recall on 12 held-out CUAD spans per category")
    ax.set_title("Clause classification: recall by category (240 spans, 20 categories)", fontsize=9.5, color=INK)
    save(fig, "01_classification_per_category.png")


def baselines():
    b = cls["baselines_top1"]
    order = ["chance (20 categories)", "Gemini embedding 1-NN", "TF-IDF nearest centroid", "TF-IDF + logistic regression", "Gemini embedding 5-NN",
             "Gemini embedding nearest centroid (shipped)", "Gemini embedding + logistic regression"]
    names = [o.replace("Gemini embedding", "Embedding").replace(" (shipped)", "\n(shipped)") for o in order]
    vals = [b[o] for o in order]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    cols = [GREY, BLUE, BLUE, BLUE, INDIGO, GREEN, INDIGO]
    bars = ax.bar(range(len(vals)), vals, color=cols)
    for r, v in zip(bars, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(names, fontsize=7, rotation=18, ha="right")
    ax.set_ylim(0, 0.95)
    ax.set_ylabel("Top-1 accuracy (240 held-out spans)")
    ax.set_title("Shipped classifier against simple baselines on the same split", fontsize=9.5, color=INK)
    save(fig, "02_classification_baselines.png")


def rules_compare():
    a, b = rules["shipped_set"]["overall"], rules["probe_set"]["overall"]
    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    x = np.arange(3)
    w = 0.36
    v1 = [a["precision"], a["recall"], a["f1"]]
    v2 = [b["precision"], b["recall"], b["f1"]]
    r1 = ax.bar(x - w / 2, v1, w, color=INDIGO, label="Shipped 40-clause set (written with the rules)")
    r2 = ax.bar(x + w / 2, v2, w, color=AMBER, label="Independent probe set (24 positive + 16 benign)")
    for rr in (r1, r2):
        for r in rr:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.012, f"{r.get_height():.2f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Precision", "Recall", "F1"])
    ax.set_ylim(0, 1.25)
    ax.legend(fontsize=7, loc="upper right", frameon=False)
    ax.set_title("Predatory-clause rules: two test sets", fontsize=9.5, color=INK)
    save(fig, "03_rules_two_test_sets.png")


def rule_recall():
    names = list(rules["probe_set"]["per_rule"].keys())
    rec = [rules["probe_set"]["per_rule"][n]["recall"] for n in names]
    sh = rules["shipped_set"]["per_rule"]
    rec0 = [sh.get(n, {}).get("recall", 0) for n in names]
    order = np.argsort(rec)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    y = np.arange(len(names))
    ax.barh(y + 0.19, [rec0[i] for i in order], 0.38, color=INDIGO, label="Shipped set")
    ax.barh(y - 0.19, [rec[i] for i in order], 0.38, color=AMBER, label="Probe set (3 per rule)")
    ax.set_yticks(y)
    ax.set_yticklabels([names[i].replace("_", " ") for i in order], fontsize=8)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Recall per rule")
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    ax.set_title("Recall of each rule on the two test sets", fontsize=9.5, color=INK)
    save(fig, "04_rule_recall.png")


def confusion():
    cats = [r[0] for r in csv.reader(open(EXP / "classification" / "confusion.csv", encoding="utf-8"))][1:]
    mat = np.array([[int(v) for v in r[1:]] for r in list(csv.reader(open(EXP / "classification" / "confusion.csv", encoding="utf-8")))[1:]])
    fig, ax = plt.subplots(figsize=(6.8, 6.0))
    im = ax.imshow(mat, cmap="Blues")
    ax.set_xticks(range(20)); ax.set_yticks(range(20))
    short = [c.replace("Termination For Convenience", "Term. for conv.").replace("Ip Ownership Assignment", "IP assignment").replace("Post-Termination Services", "Post-term. svcs")
             .replace("Revenue/Profit Sharing", "Revenue share").replace("No-Solicit Of Customers", "No-solicit cust.").replace("No-Solicit Of Employees", "No-solicit empl.")
             .replace("Liquidated Damages", "Liquid. damages").replace("Minimum Commitment", "Min. commitment").replace("Warranty Duration", "Warranty dur.")
             .replace("Non-Disparagement", "Non-disparag.").replace("Change Of Control", "Change of ctrl") for c in cats]
    ax.set_xticklabels(short, rotation=70, ha="right", fontsize=6.5)
    ax.set_yticklabels(short, fontsize=6.5)
    for i in range(20):
        for j in range(20):
            if mat[i, j]:
                ax.text(j, i, mat[i, j], ha="center", va="center", fontsize=6.3, color="white" if mat[i, j] > 7 else INK)
    ax.set_xlabel("Predicted category")
    ax.set_ylabel("True category")
    ax.set_title("Confusion matrix, 240 held-out CUAD spans (rows sum to 12)", fontsize=9.5, color=INK)
    save(fig, "05_confusion_matrix.png")


def complexity_hist():
    rows = list(csv.DictReader(open(EXP / "corpus" / "contracts.csv", encoding="utf-8")))
    sc = np.array([float(r["score"]) for r in rows])
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    ax.hist(sc, bins=np.arange(0, 91, 4), color=BLUE, edgecolor="white")
    for t, g in [(20, "A|B"), (40, "B|C"), (60, "C|D"), (80, "D|F")]:
        ax.axvline(t, color=ROSE, ls="--", lw=1)
        ax.text(t + 0.6, ax.get_ylim()[1] * 0.93, g, fontsize=7.5, color=ROSE)
    g = corpus["grades"]
    ax.set_xlabel("Complexity score (0-100)")
    ax.set_ylabel("Contracts")
    ax.set_title("Complexity of all 510 CUAD contracts: A %d, B %d, C %d, D %d, F %d" % tuple(g.get(k, 0) for k in "ABCDF"), fontsize=9.5, color=INK)
    save(fig, "06_complexity_distribution.png")


def cuad_proxy():
    rp = rules["cuad_spans"]["recall_proxy"]
    names = list(rp.keys())
    rates = [rp[n]["rate"] for n in names]
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    bars = ax.bar(range(len(names)), rates, color=[GREEN if r > 0.4 else AMBER if r > 0.1 else ROSE for r in rates])
    for r, n in zip(bars, names):
        ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.012, f"{r.get_height() * 100:.1f}%\n({rp[n]['rule_fires']}/{rp[n]['n_spans']})", ha="center", fontsize=7)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([f"{n}\n-> {rp[n]['rule'].replace('_', ' ')}" for n in names], fontsize=6.5)
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("Share of CUAD spans where the rule fires")
    ax.set_title("Rules against the closest CUAD categories (a proxy, not a recall)", fontsize=9.5, color=INK)
    save(fig, "07_cuad_rule_hits.png")


def latency():
    ep = api["endpoints"]
    keep = [(k, v) for k, v in ep.items() if v["status"] == 200]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6), gridspec_kw={"width_ratios": [1.4, 1]})
    names = [k.replace("GET /api", "GET").replace("POST /api/auth", "POST").replace(" (report)", "").replace(" (bcrypt check)", " (bcrypt)").replace(" (bcrypt hash)", " (bcrypt)") for k, _ in keep]
    med = [v["median_ms"] for _, v in keep]
    p95 = [v["p95_ms"] for _, v in keep]
    y = np.arange(len(keep))
    a1.barh(y, med, color=INDIGO, label="median")
    a1.barh(y, [p - m for p, m in zip(p95, med)], left=med, color="#b8b8f0", label="to p95")
    a1.set_yticks(y); a1.set_yticklabels(names, fontsize=6.8); a1.invert_yaxis()
    a1.set_xscale("log"); a1.set_xlabel("ms (log scale)")
    a1.legend(fontsize=7, frameon=False)
    a1.set_title("Endpoints without Gemini (30 repeats)", fontsize=9, color=INK)
    up = api["uploads"]
    labs = {"balanced": "Fair DOCX\n8 clauses, 0 flags", "cuad_pdf": "CUAD PDF\n11 clauses, 1 flag", "freelance": "One-sided DOCX\n11 clauses, 8 flags"}
    order = ["balanced", "cuad_pdf", "freelance"]
    a2.bar(range(3), [up[k]["seconds"] for k in order], color=[GREEN, AMBER, ROSE])
    for i, k in enumerate(order):
        a2.text(i, up[k]["seconds"] + 2, f"{up[k]['seconds']:.1f} s", ha="center", fontsize=8)
    a2.axhline(180, color=INK, ls="--", lw=1)
    a2.text(2.45, 183, "UI timeout 180 s", fontsize=7, ha="right")
    a2.set_xticks(range(3)); a2.set_xticklabels([labs[k] for k in order], fontsize=6.3)
    a2.set_ylim(0, 205); a2.set_ylabel("seconds")
    a2.set_title("Upload to report (real Gemini calls)", fontsize=9, color=INK)
    fig.tight_layout()
    save(fig, "08_latency.png")


def confidence_hist():
    z = np.load(EXP / "classification" / "embeddings.npz")
    tr, ev = z["train"], z["eval"]
    items = json.loads((ROOT / "data/sample/cuad_train_examples.json").read_text(encoding="utf-8"))
    cats = items["categories"]
    lab = np.array([i for i, c in enumerate(cats) for _ in items["examples"][c]])
    cen = np.vstack([tr[lab == k].mean(axis=0) for k in range(20)])
    u = lambda a: a / np.linalg.norm(a, axis=-1, keepdims=True)  # noqa: E731
    s = u(ev) @ u(cen).T
    top1 = np.sort(s, axis=1)[:, -1]
    top2 = np.sort(s, axis=1)[:, -2]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.3))
    a1.hist(top1, bins=np.arange(0.3, 0.9, 0.025), color=BLUE, edgecolor="white")
    a1.axvline(0.60, color=ROSE, ls="--"); a1.axvline(0.35, color=AMBER, ls="--")
    a1.text(0.605, a1.get_ylim()[1] * 0.9, "tie-break needs\ntop1 < 0.60", fontsize=7, color=ROSE)
    a1.text(0.352, a1.get_ylim()[1] * 0.6, "Unclassified\n< 0.35", fontsize=7, color=AMBER)
    a1.set_xlabel("top-1 cosine similarity"); a1.set_ylabel("held-out spans")
    a1.set_title("Where the thresholds sit", fontsize=9, color=INK)
    a2.hist(top1 - top2, bins=np.arange(0, 0.2, 0.01), color=INDIGO, edgecolor="white")
    a2.axvline(0.03, color=ROSE, ls="--"); a2.text(0.032, a2.get_ylim()[1] * 0.9, "margin 0.03", fontsize=7, color=ROSE)
    a2.set_xlabel("top-1 minus top-2 similarity"); a2.set_title("Margin between the best two categories", fontsize=9, color=INK)
    fig.tight_layout()
    save(fig, "09_confidence_thresholds.png")


def parity_chart():
    keys = [("freelance_services_agreement.docx", "DOCX"), ("freelance_services_agreement.pdf", "PDF (same text)")]
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    vals = [parity[k]["as_uploaded"]["n_rules"] for k, _ in keys] + [parity["freelance_services_agreement.pdf"]["whitespace_collapsed"]["n_rules"]]
    labels = ["DOCX\n(as uploaded)", "PDF\n(as uploaded)", "PDF, whitespace\ncollapsed first"]
    bars = ax.bar(range(3), vals, color=[GREEN, ROSE, INDIGO])
    for r, v in zip(bars, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.15, f"{v} of 8", ha="center", fontsize=8.5)
    ax.set_xticks(range(3)); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 9.5); ax.set_ylabel("rules that fire")
    ax.set_title("One contract, three input forms", fontsize=9.5, color=INK)
    save(fig, "10_format_parity.png")


if __name__ == "__main__":
    for f in (per_category, baselines, rules_compare, rule_recall, confusion, complexity_hist, cuad_proxy, latency, confidence_hist, parity_chart):
        f()
