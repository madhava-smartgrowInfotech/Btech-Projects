"""Result figures for the PeerScope documents, drawn from docs/metrics/metrics.json (+ latency.json when present).

    <venv>\\Scripts\\python scripts\\docs_build\\make_figures.py
Writes PNGs (150 dpi) to docs/figures/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
M = json.loads((ROOT / "docs" / "metrics" / "metrics.json").read_text(encoding="utf-8"))
LAT_PATH = ROOT / "docs" / "metrics" / "latency.json"
LAT = json.loads(LAT_PATH.read_text(encoding="utf-8")) if LAT_PATH.exists() else None
DM = M["decision_model"]

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#5B6B7F", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.titleweight": "bold", "axes.titlesize": 11, "axes.labelsize": 10})


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def bar_labels(ax, bars, fmt="{:.2f}", dy=0.012, fs=8):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy, fmt.format(b.get_height()), ha="center", va="bottom", fontsize=fs)


def confusion():
    cm = np.array(DM["shipped"]["confusion_matrix"])
    labels = DM["labels"]
    norm = cm / cm.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(4.6, 3.9))
    ax.grid(False)
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{cm[i, j]}\n({norm[i, j] * 100:.0f}%)", ha="center", va="center", fontsize=10,
                    color="white" if norm[i, j] > 0.55 else "#14213D")
    ax.set_xticks(range(3)); ax.set_xticklabels(labels); ax.set_yticks(range(3)); ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("Confusion matrix, 280 held-out papers")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Share of true class")
    save(fig, "f01_confusion_matrix.png")


def per_class():
    labels = DM["labels"]
    pc = DM["per_class"]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for k, (m, c) in enumerate((("precision", BLUE), ("recall", TEAL), ("f1", ORANGE))):
        bars = ax.bar(x + (k - 1) * 0.26, [pc[l][m] for l in labels], 0.26, label=m.upper() if m == "f1" else m.capitalize(), color=c)
        bar_labels(ax, bars)
    ax.set_xticks(x); ax.set_xticklabels([f"{l}\n(n={pc[l]['support']})" for l in labels])
    ax.set_ylim(0, 1.12); ax.set_ylabel("Score"); ax.set_title("Per-class precision, recall and F1 (shipped model)")
    ax.legend(ncol=3, loc="upper center", frameon=False)
    save(fig, "f02_per_class.png")


def baselines():
    b = DM["baselines"]
    rows = [("Majority\nclass", b["majority_class"]), ("Naive Bayes\n(word TF-IDF)", b["naive_bayes_word_tfidf"]),
            ("LogReg\nunweighted", b["logreg_unweighted_word_char"]), ("LogReg balanced\nword only", b["logreg_balanced_word_only"]),
            ("PeerScope\n(LogReg balanced,\nword+char)", DM["shipped"])]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    b1 = ax.bar(x - 0.2, [r["accuracy"] for _, r in rows], 0.4, label="Accuracy", color=BLUE)
    b2 = ax.bar(x + 0.2, [r["f1_macro"] for _, r in rows], 0.4, label="Macro F1", color=ORANGE)
    bar_labels(ax, b1); bar_labels(ax, b2)
    ceiling = DM["generator_structure"]["best_possible_accuracy_from_phrases"]
    ax.axhline(ceiling, color=RED, ls="--", lw=1.2)
    ax.text(-0.45, ceiling + 0.035, f"ceiling for accuracy set by the label construction (~{ceiling:.2f})", ha="left", color=RED, fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([n for n, _ in rows], fontsize=8.5)
    ax.set_ylim(0, 0.8); ax.set_ylabel("Score on 280 held-out papers"); ax.set_title("Decision model against simple baselines (same split)")
    ax.legend(frameon=False, loc="upper right", ncol=2)
    save(fig, "f03_baselines.png")


def seeds():
    runs = DM["seed_study"]["runs"]
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    x = np.arange(len(runs))
    for k, (m, c, n) in enumerate((("accuracy", BLUE, "Accuracy"), ("f1_macro", ORANGE, "Macro F1"), ("roc_auc", TEAL, "ROC-AUC"))):
        bars = ax.bar(x + (k - 1) * 0.26, [r[m] for r in runs], 0.26, label=n, color=c)
        bar_labels(ax, bars, "{:.2f}", fs=7)
    ax.set_xticks(x); ax.set_xticklabels([f"split seed {r['seed']}" for r in runs])
    ax.set_ylim(0, 0.95); ax.set_title("Five different train/test splits: accuracy {:.3f} +/- {:.3f}".format(DM["seed_study"]["accuracy"]["mean"], DM["seed_study"]["accuracy"]["sd"]))
    ax.legend(ncol=3, frameon=False, loc="upper center")
    save(fig, "f04_seed_study.png")


def threshold():
    t = [r for r in DM["threshold_analysis"] if r["accuracy_on_kept"] is not None and r["threshold"] >= 0.4]
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    xs = [r["threshold"] for r in t]
    ax.plot(xs, [r["coverage"] for r in t], "o-", color=BLUE, label="Share of papers kept")
    ax.plot(xs, [r["accuracy_on_kept"] for r in t], "s-", color=ORANGE, label="Accuracy on kept papers")
    for r in t:
        ax.annotate(f"n={r['n']}", (r["threshold"], r["accuracy_on_kept"]), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7.5)
    ax.set_xlabel("Minimum confidence (max class probability)")
    ax.set_title("Confidence threshold: coverage against accuracy"); ax.set_ylim(0, 1.18); ax.legend(frameon=False, loc="upper center", ncol=2)
    save(fig, "f05_threshold.png")


def dataset_structure():
    g = DM["generator_structure"]
    fig, ax = plt.subplots(1, 2, figsize=(8.2, 3.3), gridspec_kw={"width_ratios": [1, 1.25]})
    cc = DM["class_counts"]
    order = ["accept", "borderline", "reject"]
    bars = ax[0].bar(order, [cc[k] for k in order], color=[TEAL, GREY, RED])
    for b in bars:
        ax[0].text(b.get_x() + b.get_width() / 2, b.get_height() + 8, int(b.get_height()), ha="center", fontsize=8.5)
    ax[0].set_title("Class counts (1,400 synthetic rows)"); ax[0].set_ylim(0, 720)
    sp, wp = g["strong_phrase_papers"], g["weak_phrase_papers"]
    cols = {"accept": TEAL, "borderline": GREY, "reject": RED}
    for xi, (name, d) in enumerate((("strength phrases\nin text", sp), ("weakness phrases\nin text", wp))):
        bottom = 0
        for lab in order:
            v = d["label_counts"].get(lab, 0)
            if v:
                ax[1].bar(xi, v, bottom=bottom, color=cols[lab], label=lab if xi == 0 or lab == "reject" else None)
                ax[1].text(xi, bottom + v / 2, f"{lab}\n{v}", ha="center", va="center", color="white", fontsize=8)
                bottom += v
    ax[1].set_xticks([0, 1]); ax[1].set_xticklabels(["strength phrases\nin text", "weakness phrases\nin text"])
    ax[1].set_title("Label made from the same text signal")
    save(fig, "f06_dataset_structure.png")


def matching_configs():
    names = [("full_hybrid_shipped_weights", "Hybrid\n(shipped)"), ("semantic_similarity_only", "Semantic\nonly"),
             ("lexical_only_keyword_and_method", "Lexical\nonly"), ("hybrid_without_availability", "Hybrid, no\navailability")]
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for a, key, title in ((ax[0], "sentence_transformer_minilm", "MiniLM sentence embeddings"), (ax[1], "tfidf_fallback", "TF-IDF fallback (offline)")):
        d = M["matching"][key]
        x = np.arange(len(names))
        for k, (m, c, n) in enumerate((("top1", BLUE, "Top-1"), ("top3", TEAL, "Top-3"), ("mrr", ORANGE, "MRR"))):
            bars = a.bar(x + (k - 1) * 0.26, [d[c_][m] for c_, _ in names], 0.26, label=n, color=c)
            bar_labels(a, bars, "{:.2f}", fs=7)
        a.axhline(d["random_expectation_top1"], color=RED, ls=":", lw=1.2)
        a.set_xticks(x); a.set_xticklabels([n for _, n in names], fontsize=8); a.set_title(title); a.set_ylim(0, 1.3)
    ax[0].set_ylabel("Score on 40 probe papers"); ax[0].legend(ncol=3, frameon=False, loc="upper center", fontsize=8)
    ax[1].text(3.45, M["matching"]["tfidf_fallback"]["random_expectation_top1"] + 0.02, "random top-1", color=RED, ha="right", fontsize=7.5)
    save(fig, "f07_matching_configs.png")


def conflict():
    d = M["matching"]["sentence_transformer_minilm"]["conflict"]["detected_by_kind"]
    kinds = list(d.keys())
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    det = [d[k]["detected"] for k in kinds]; n = [d[k]["n"] for k in kinds]
    ax.barh(kinds, n, color="#E6EBF2", label="cases injected")
    ax.barh(kinds, det, color=[TEAL if a == b else RED for a, b in zip(det, n)], label="flagged as conflict")
    for i, (a, b) in enumerate(zip(det, n)):
        ax.text(b + 0.1, i, f"{a}/{b}", va="center", fontsize=9)
    ax.invert_yaxis(); ax.set_xlim(0, max(n) + 1.2)
    ax.set_title("Conflict-of-interest detection by kind of link (15 injected cases)")
    ax.set_xlabel("Cases")
    save(fig, "f08_conflict_detection.png")


def scaling():
    a = M["matching"]["sentence_transformer_minilm"]["scaling_ms"]
    b = M["matching"]["tfidf_fallback"]["scaling_ms"]
    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    ax.plot([r["pool"] for r in a], [r["median_ms"] for r in a], "o-", color=BLUE, label="MiniLM embeddings")
    ax.plot([r["pool"] for r in b], [r["median_ms"] for r in b], "s-", color=ORANGE, label="TF-IDF fallback")
    for r in a:
        ax.annotate(f"{r['median_ms'] / 1000:.1f} s" if r["median_ms"] > 999 else f"{r['median_ms']:.0f} ms", (r["pool"], r["median_ms"]), textcoords="offset points", xytext=(-4, 7), ha="right", fontsize=8)
    ax.set_xlabel("Reviewers in the directory"); ax.set_ylabel("Median ranking time (ms)")
    ax.set_title("Ranking time grows linearly with the reviewer pool"); ax.legend(frameon=False)
    save(fig, "f09_matching_scaling.png")


def real_papers():
    rows = M["real_pdfs"]
    names = ["Demo\nfixture", "Survey\n(2604.27924)", "ReViewGraph\n(2511.08317)", "IEEE Access\nbase paper"]
    keys = [("structure_completeness", "Structure completeness", BLUE), ("evidence_coverage", "Evidence coverage", TEAL), ("method_clarity", "Method clarity", ORANGE),
            ("presentation", "Presentation", PURPLE), ("structural_score", "Overall structural", NAVY)]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(8.2, 3.5))
    for k, (key, label, c) in enumerate(keys):
        bars = ax.bar(x + (k - 2) * 0.16, [r[key] for r in rows], 0.16, label=label, color=c)
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8.5); ax.set_ylim(0, 118); ax.set_ylabel("Signal (0-100)")
    ax.set_title("Structural signals on four real PDFs"); ax.legend(ncol=5, frameon=False, fontsize=7.5, loc="upper center")
    save(fig, "f10_real_papers_signals.png")


def timings():
    if not LAT:
        return
    st = LAT["pipeline_stage_ms_demo"]
    labels = list(st.keys()); vals = [st[k] / 1000 for k in labels]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.barh(labels, vals, color=[BLUE, BLUE, BLUE, TEAL, ORANGE, PURPLE, NAVY][: len(labels)])
    for b, v in zip(bars, vals):
        ax.text(b.get_width() + max(vals) * 0.01, b.get_y() + b.get_height() / 2, f"{v:.1f} s" if v >= 0.1 else f"{v * 1000:.0f} ms", va="center", fontsize=8.5)
    ax.invert_yaxis(); ax.set_xlabel("Seconds"); ax.set_xlim(0, max(vals) * 1.15)
    ax.set_title("Where the time goes in one analysis (demo paper, CPU)")
    save(fig, "f11_pipeline_timings.png")


def score_breakdown():
    from types import SimpleNamespace  # noqa: F401
    sys.path.insert(0, str(ROOT / "scripts"))
    import measure_metrics as mm
    from app.services import matching as m
    from app.config import MATCH_WEIGHTS
    revs = mm.reviewers_ns()
    prof, text = mm.paper_profile_from("Efficient Retrieval-Grounded Text Classification with Lightweight Transformers",
                                       "This paper studies efficient text classification with lightweight transformer models augmented by retrieval grounding.")
    ranked = m.match_reviewers(prof, revs, text)[:5]
    labels = [r["display_name"].replace("Reviewer ", "") for r in ranked]
    comps = [("expertise_similarity", "Expertise similarity", BLUE), ("keyword_score", "Keyword overlap", TEAL), ("method_score", "Method / topic overlap", ORANGE), ("availability_score", "Availability", PURPLE)]
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    left = np.zeros(len(ranked))
    for key, label, c in comps:
        v = np.array([MATCH_WEIGHTS[key] * r["breakdown"][key] * 100 for r in ranked])
        ax.barh(labels, v, left=left, color=c, label=label)
        left += v
    for i, r in enumerate(ranked):
        ax.text(left[i] + 0.8, i, f"{r['score']:.1f}", va="center", fontsize=9, fontweight="bold")
    ax.invert_yaxis(); ax.set_xlabel("Weighted contribution to the 0-100 match score"); ax.set_xlim(0, max(left) * 1.15)
    ax.set_title("Auditable score breakdown for the demo paper"); ax.legend(frameon=False, fontsize=8, loc="lower right")
    save(fig, "f12_score_breakdown.png")


if __name__ == "__main__":
    for fn in (confusion, per_class, baselines, seeds, threshold, dataset_structure, matching_configs, conflict, scaling, real_papers, timings, score_breakdown):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print("FAILED", fn.__name__, exc)
