"""Result figures for the SymptoTrackAI (CareLens AI) documents, drawn from docs/metrics/*.json.

    .venv\\Scripts\\python scripts\\docs_build\\make_figures.py
Writes PNGs (150 dpi) to docs/figures/.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
MD = ROOT / "docs" / "metrics"
M = json.loads((MD / "metrics.json").read_text(encoding="utf-8"))
LFB = json.loads((MD / "latency_fallback.json").read_text(encoding="utf-8"))
LT5 = json.loads((MD / "latency_flan-t5.json").read_text(encoding="utf-8"))
R = M["retrieval"]

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#5B6B7F", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.titleweight": "bold", "axes.titlesize": 10.5, "axes.labelsize": 9.5})


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def bar_labels(ax, bars, fmt="{:.2f}", dy=0.012, fs=7.5):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy, fmt.format(b.get_height()), ha="center", va="bottom", fontsize=fs)


def errbars(top1, ci):
    lo = [t - c[0] for t, c in zip(top1, ci)]
    hi = [c[1] - t for t, c in zip(top1, ci)]
    return [lo, hi]


# ---------------------------------------------------------------------------------------------
def f01():
    lab = M["lay_confusion"]["labels"]
    cm = np.array(M["lay_confusion"]["matrix"])
    n = len(lab)
    fig, ax = plt.subplots(figsize=(7.4, 6.6))
    ax.grid(False)
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=2)
    for i in range(n):
        for j in range(n):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7.5, color="white" if cm[i, j] >= 2 else "#14213D")
    ax.set_xticks(range(n)); ax.set_xticklabels(lab, rotation=90, fontsize=7)
    ax.set_yticks(range(n)); ax.set_yticklabels(lab, fontsize=7)
    ax.set_xlabel("Predicted condition (top-1)"); ax.set_ylabel("True condition")
    s4 = R["hybrid_rerank"]["S4_lay_language_60"]
    ax.set_title(f"Shipped configuration on 60 author-written lay-language probes\n(top-1 {s4['top1'] * 100:.1f}%, {s4['n_misses']} misses; synthetic knowledge base)")
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02, ticks=[0, 1, 2])
    cb.set_label("Queries (2 per condition)")
    save(fig, "f01_lay_confusion.png")


def f02():
    sets = [("S2_verbatim_leave_one_out_176", "S2 verbatim\n(176, leave-one-out)"), ("S3_two_symptoms_leave_one_out_176", "S3 two symptoms\n(176, leave-one-out)"),
            ("S4_lay_language_60", "S4 lay language\n(60 probes)")]
    cfgs = [("bm25", "BM25 only", GREY), ("dense", "Dense (MiniLM)", BLUE), ("hybrid", "Hybrid fusion", TEAL), ("hybrid_rerank", "Hybrid + rerank (shipped)", ORANGE),
            ("hybrid_rerank_nohyde", "Shipped, no HyDE", PURPLE), ("hybrid_tfidf", "Offline TF-IDF hybrid", RED)]
    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    w = 0.13
    x = np.arange(len(sets))
    for k, (c, lab, col) in enumerate(cfgs):
        vals = [R[c][s]["top1"] for s, _ in sets]
        ci = [R[c][s]["top1_ci"] for s, _ in sets]
        bars = ax.bar(x + (k - 2.5) * w, vals, w, label=lab, color=col, yerr=errbars(vals, ci), error_kw=dict(lw=0.8, capsize=1.5, ecolor="#333"))
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, 0.52, f"{v:.2f}", ha="center", va="bottom", fontsize=6, rotation=90, color="white")
    ax.set_xticks(x); ax.set_xticklabels([l for _, l in sets])
    ax.set_ylim(0.5, 1.06); ax.set_ylabel("Top-1 condition accuracy")
    ax.set_title("Retrieval ablation (synthetic 176-record knowledge base; bars show Wilson 95% intervals)")
    ax.legend(ncol=3, fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    save(fig, "f02_ablation.png")


def f03():
    s = [("S1_shipped_protocol_30", "S1 shipped\nprotocol\n(n=30,\nrecord indexed)"), ("S1_leave_one_out_30", "S1\nleave-one-out\n(n=30)"),
         ("S2_verbatim_leave_one_out_176", "S2 verbatim\nleave-one-out\n(n=176)"), ("S3_two_symptoms_leave_one_out_176", "S3 two\nsymptoms\n(n=176)"),
         ("S4_lay_language_60", "S4 lay\nlanguage\n(n=60)")]
    d = R["hybrid_rerank"]
    vals = [d[k]["top1"] for k, _ in s]
    ci = [d[k]["top1_ci"] for k, _ in s]
    cols = [RED, ORANGE, BLUE, BLUE, TEAL]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    bars = ax.bar(range(5), vals, 0.6, color=cols, yerr=errbars(vals, ci), error_kw=dict(lw=1, capsize=3, ecolor="#333"))
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, 0.52, f"{v:.3f}", ha="center", va="bottom", fontsize=8, color="white", fontweight="bold")
    ax.set_xticks(range(5)); ax.set_xticklabels([l for _, l in s], fontsize=7.8)
    ax.set_ylim(0.5, 1.06); ax.set_ylabel("Top-1 accuracy (shipped configuration)")
    ax.set_title("The shipped 1.0 is an upper bound; other protocols give 0.88 to 0.97")
    save(fig, "f03_protocol_comparison.png")


def f04():
    st = M["latency"]["stages_ms"]
    order = ["expand", "embed", "faiss", "bm25", "fuse", "rerank", "safety"]
    names = ["HyDE\nexp.", "MiniLM\nembed", "FAISS", "BM25", "Fusion", "Cross-\nencoder", "Safety\nrules"]
    means = [st[k]["mean"] for k in order]
    p95 = [st[k]["p95"] for k in order]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.5), gridspec_kw=dict(width_ratios=[1.6, 1]))
    x = np.arange(len(order))
    b1 = a1.bar(x - 0.18, means, 0.36, color=BLUE, label="mean")
    b2 = a1.bar(x + 0.18, p95, 0.36, color=ORANGE, label="95th percentile")
    for b in list(b1) + list(b2):
        a1.text(b.get_x() + b.get_width() / 2, b.get_height() + 8, f"{b.get_height():.1f}", ha="center", va="bottom", fontsize=6.5)
    a1.set_xticks(x); a1.set_xticklabels(names, fontsize=7); a1.set_ylabel("Milliseconds per query")
    a1.set_title(f"Pipeline stages, timed alone (n={M['latency']['n']}, CPU)"); a1.legend(frameon=False, fontsize=8)
    a1.set_ylim(0, max(p95) * 1.15)
    tot = [("Evidence fallback\nonly", M["latency"]["pipeline_answer_fallback_only_ms"]), ("With Flan-T5\ngenerator", M["latency"]["pipeline_answer_with_local_generator_ms"])]
    xs = np.arange(2)
    c1 = a2.bar(xs - 0.18, [t[1]["mean"] for t in tot], 0.36, color=TEAL, label="mean")
    c2 = a2.bar(xs + 0.18, [t[1]["p95"] for t in tot], 0.36, color=PURPLE, label="95th percentile")
    for b in list(c1) + list(c2):
        a2.text(b.get_x() + b.get_width() / 2, b.get_height() + 15, f"{b.get_height():.0f}", ha="center", va="bottom", fontsize=7)
    a2.set_xticks(xs); a2.set_xticklabels([t[0] for t in tot], fontsize=7.5)
    a2.set_title("pipeline.answer() in process"); a2.legend(frameon=False, fontsize=8); a2.set_ylim(0, 1700)
    save(fig, "f04_latency_stages.png")


def f05():
    rel = M["relevance"]
    a = rel["raw_rerank_in_kb_values"]
    b = rel["raw_rerank_out_kb_values"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 3.6), gridspec_kw=dict(width_ratios=[1.5, 1]))
    rng = np.random.default_rng(3)
    a1.scatter(a, 1 + rng.uniform(-0.12, 0.12, len(a)), s=22, color=TEAL, alpha=0.85, label=f"in knowledge base (n={len(a)})")
    a1.scatter(b, 0 + rng.uniform(-0.12, 0.12, len(b)), s=22, color=RED, alpha=0.85, label=f"out of knowledge base (n={len(b)})")
    a1.set_yticks([0, 1]); a1.set_yticklabels(["out-of-KB\ncomplaints", "in-KB lay\nprobes"]); a1.set_ylim(-0.6, 1.6)
    a1.set_xlabel("Raw cross-encoder score of the top record")
    a1.set_title(f"What the model knows (AUROC {rel['auroc_in_vs_out_by_raw_rerank_score']:.2f})")
    a1.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, 1.0))
    a2.bar([0, 1], [1.0, 1.0], 0.5, color=[TEAL, RED])
    for x_, v in ((0, "100%\n60 of 60\n'Strong\nmatch'"), (1, "100%\n15 of 15\n'Strong\nmatch'")):
        a2.text(x_, 0.5, v, ha="center", va="center", color="white", fontsize=8, fontweight="bold")
    a2.set_xticks([0, 1]); a2.set_xticklabels(["in-KB", "out-of-KB"]); a2.set_ylim(0, 1.15); a2.set_ylabel("Displayed relevance of top record")
    a2.set_title("What the user is shown")
    fig.suptitle("Min-max normalisation hides the score difference (author-written probes)", fontsize=10.5, fontweight="bold", y=1.02)
    save(fig, "f05_relevance_display.png")


def f06():
    s = M["safety"]
    gp, gn = s["by_group_pos"], s["by_group_neg"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.5))
    labs = ["Literal wording\n(28)", "Paraphrased\nwording (12)", "All emergency\n(40)"]
    vals = [gp["literal"]["detected"] / gp["literal"]["n"], gp["paraphrase"]["detected"] / gp["paraphrase"]["n"], s["emergency_recall"]]
    bars = a1.bar(range(3), vals, 0.55, color=[TEAL, RED, BLUE])
    cnt = [f"{gp['literal']['detected']}/{gp['literal']['n']}", f"{gp['paraphrase']['detected']}/{gp['paraphrase']['n']}", f"{s['true_emergency']}/{s['n_pos']}"]
    for b, v, c in zip(bars, vals, cnt):
        a1.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}\n({c})", ha="center", va="bottom", fontsize=8)
    a1.set_xticks(range(3)); a1.set_xticklabels(labs, fontsize=8); a1.set_ylim(0, 1.25); a1.set_ylabel("Emergency recall")
    a1.set_title("Emergencies flagged")
    ordn, hard = gn["ordinary"], gn["hard"]
    cats = ["Ordinary (20)", "Hard negatives (10)"]
    fe = [len(ordn["false_emergency"]), len(hard["false_emergency"])]
    ca = [len(ordn["caution"]), len(hard["caution"])]
    ro = [ordn["routine"], hard["routine"]]
    x = np.arange(2)
    a2.bar(x, fe, 0.5, color=RED, label="false emergency")
    a2.bar(x, ca, 0.5, bottom=fe, color="#E8A317", label="caution")
    a2.bar(x, ro, 0.5, bottom=[f + c for f, c in zip(fe, ca)], color=TEAL, label="routine")
    for i in range(2):
        for v, base, col in ((fe[i], 0, "white"), (ca[i], fe[i], "black"), (ro[i], fe[i] + ca[i], "white")):
            if v:
                a2.text(i, base + v / 2, str(v), ha="center", va="center", color=col, fontsize=9, fontweight="bold")
    a2.set_xticks(x); a2.set_xticklabels(cats, fontsize=8); a2.set_ylabel("Texts (non-emergency)"); a2.set_ylim(0, 24)
    a2.set_title("Non-emergency texts: flag given"); a2.legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.suptitle("Rule-based safety layer on 70 author-written texts (not clinical validation)", fontsize=10.5, fontweight="bold", y=1.03)
    save(fig, "f06_safety_rules.png")


def f07():
    kb = M["kb"]
    items = sorted(kb["records_per_condition"].items(), key=lambda t: (-t[1], t[0]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 4.6), gridspec_kw=dict(width_ratios=[2.2, 1]))
    names = [i[0] for i in items][::-1]
    vals = [i[1] for i in items][::-1]
    a1.barh(names, vals, color=BLUE)
    for i, v in enumerate(vals):
        a1.text(v + 0.08, i, str(v), va="center", fontsize=7)
    a1.set_yticks(range(len(names))); a1.set_yticklabels(names, fontsize=7); a1.set_xlabel("Records"); a1.set_xlim(0, 7.2)
    a1.set_title(f"{kb['records']} records over {kb['conditions']} conditions")
    sv = kb["severity"]
    order = ["low", "moderate", "high", "emergency"]
    cols = [TEAL, BLUE, ORANGE, RED]
    b = a2.bar(["low", "mod.", "high", "emerg."], [sv[o] for o in order], color=cols)
    bar_labels(a2, b, "{:.0f}", dy=1.0, fs=8)
    a2.set_ylabel("Records"); a2.set_title("Severity label"); a2.set_ylim(0, 105)
    fig.suptitle(f"Synthetic knowledge base: {kb['distinct_description_guidance_pairs']} distinct description/guidance pairs, {kb['symptom_vocabulary']} symptom phrases", fontsize=10, fontweight="bold", y=1.0)
    save(fig, "f07_kb_composition.png")


def f08():
    rows = [("Health check", "health_ms"), ("Login (bcrypt)", "login_ms"), ("History list", "history_list_ms"), ("Chat (full pipeline)", "chat_ms")]
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    y = np.arange(len(rows))
    h = 0.34
    f = [LFB[k]["mean"] for _, k in rows]
    t = [LT5[k]["mean"] for _, k in rows]
    b1 = ax.barh(y + h / 2, f, h, color=TEAL, label="Evidence-fallback generator")
    b2 = ax.barh(y - h / 2, t, h, color=ORANGE, label="Flan-T5-small generator")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_width() + 6, b.get_y() + b.get_height() / 2, f"{b.get_width():.0f} ms", va="center", fontsize=7.5)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis(); ax.set_xlim(0, 950)
    ax.set_xlabel("Mean HTTP latency on 127.0.0.1 (ms)")
    ax.set_title(f"API latency, CPU only (chat: n={LFB['chat_ms']['n']} lay probes; p95 {LFB['chat_ms']['p95']:.0f} / {LT5['chat_ms']['p95']:.0f} ms)")
    ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 0.55))
    save(fig, "f08_api_latency.png")


def f09():
    s = [("S1_leave_one_out_30", "S1 LOO\n(30)"), ("S2_verbatim_leave_one_out_176", "S2 verbatim\nLOO (176)"), ("S3_two_symptoms_leave_one_out_176", "S3 two symptoms\n(176)"),
         ("S4_lay_language_60", "S4 lay\nlanguage (60)")]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    x = np.arange(len(s))
    for k, (c, lab, col) in enumerate((("hybrid_rerank", "Shipped (HyDE template)", ORANGE), ("hybrid_rerank_nohyde", "Without HyDE expansion", PURPLE))):
        vals = [R[c][a]["top1"] for a, _ in s]
        ci = [R[c][a]["top1_ci"] for a, _ in s]
        bars = ax.bar(x + (k - 0.5) * 0.36, vals, 0.36, color=col, label=lab, yerr=errbars(vals, ci), error_kw=dict(lw=0.9, capsize=2, ecolor="#333"))
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, 0.82, f"{v:.3f}", ha="center", va="bottom", fontsize=7, color="white", rotation=90)
    ax.set_xticks(x); ax.set_xticklabels([l for _, l in s], fontsize=8)
    ax.set_ylim(0.8, 1.04); ax.set_ylabel("Top-1 accuracy")
    ax.set_title("Rule-based HyDE expansion did not help (differences within the intervals)")
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    save(fig, "f09_hyde_effect.png")


if __name__ == "__main__":
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09):
        fn()
