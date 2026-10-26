"""Result charts for the ATHENA documents, drawn from experiments/**/*.json into docs/figures/ (PNG, 150 dpi).

Every plotted value is read from the JSON files written by ml/train.py, ml/eval.py and scripts/run_experiments.py,
extract_stress.py and measure_api.py; nothing is typed in except the base-paper numbers (scripts/docs/facts.py).
    python scripts/docs_build/make_figures.py
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
sys.path.insert(0, str(ROOT / "scripts" / "docs"))
import facts as F  # noqa: E402

EXP = ROOT / "experiments"
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, BLUE, TEAL, ORANGE, RED, PURPLE, GREY = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#C0392B", "#6B5BD2", "#8795A8"
PRIO_COLORS = ["#C0392B", "#D9772F", "#E3B341", "#2B6CB0", "#14907F"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

SH, X, ST, LAT = F.SHIPPED, F.X, F.STRESS, F.LAT
PN = ["P1", "P2", "P3", "P4", "P5"]


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def f01():
    cm = np.array(SH["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    ax.imshow(cm / cm.sum(1, keepdims=True), cmap="Blues", vmin=0, vmax=1)
    for i in range(5):
        for j in range(5):
            share = cm[i, j] / cm[i].sum()
            ax.text(j, i, f"{cm[i, j]}\n{share * 100:.0f}%", ha="center", va="center", fontsize=9.5, color="white" if share > 0.5 else "black")
    ax.set_xticks(range(5)); ax.set_xticklabels(PN); ax.set_yticks(range(5)); ax.set_yticklabels(PN)
    ax.set_xlabel("Model priority"); ax.set_ylabel("Recorded priority (synthetic label)")
    ax.set_title(f"Confusion matrix, {F.N_TEST:,} held-out synthetic cases\ncolour = share of each recorded row; accuracy {F.ACC * 100:.1f}%", fontsize=10.5)
    ax.spines[:].set_visible(False)
    save(fig, "f01_confusion_matrix.png")


def f02():
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    rec = [r * 100 for r in F.REC]
    bars = ax.bar(PN, rec, color=PRIO_COLORS)
    for b, r, n in zip(bars, rec, F.SUP):
        ax.text(b.get_x() + b.get_width() / 2, r + 1.2, f"{r:.1f}%", ha="center", fontsize=9.5, fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, 3, f"n={n}", ha="center", fontsize=8.5, color="white")
    ax.axhline(F.ACC * 100, color=NAVY, ls="--", lw=1.2)
    ax.text(-0.45, F.ACC * 100 + 1.5, f"overall accuracy {F.ACC * 100:.1f}%", ha="left", fontsize=8.5, color=NAVY)
    ax.set_ylim(0, 100); ax.set_ylabel("Recall (%)"); ax.set_xlabel("Recorded priority")
    ax.set_title("Recall per priority: the most urgent classes are the hardest", fontsize=10.5)
    save(fig, "f02_recall_per_priority.png")


def f03():
    names = list(F.COMP)
    acc = [F.COMP[n]["accuracy"] * 100 for n in names]
    f1 = [F.COMP[n]["macro_f1"] * 100 for n in names]
    order = np.argsort(acc)
    names = [names[i] for i in order]; acc = [acc[i] for i in order]; f1 = [f1[i] for i in order]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    y = np.arange(len(names))
    for i, n in enumerate(names):
        shipped = n.startswith("XGBoost")
        ax.barh(y[i] + 0.19, acc[i], 0.36, color=ORANGE if shipped else BLUE)
        ax.barh(y[i] - 0.19, f1[i], 0.36, color="#E8A671" if shipped else "#8FB4DE")
        ax.text(acc[i] + 0.6, y[i] + 0.19, f"{acc[i]:.1f}", va="center", fontsize=8.5)
        ax.text(f1[i] + 0.6, y[i] - 0.19, f"{f1[i]:.1f}", va="center", fontsize=8.5, color=GREY)
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=9)
    ax.set_xlim(0, 85); ax.set_xlabel("Percent (dark = accuracy, light = macro F1 x 100)")
    ax.set_title("Eight models on the same split (uncalibrated; shipped configuration in orange)", fontsize=10.5)
    save(fig, "f03_model_comparison.png")


def f04():
    keys = ["Vitals only (8)", "Vitals + lab flags (14)", "Report only (28)", "Vitals + text flags (30)", "Fused (36)"]
    acc = [F.ABL[k]["accuracy"] * 100 for k in keys]
    f1 = [F.ABL[k]["macro_f1"] * 100 for k in keys]
    top2 = [F.ABL[k]["top2"] * 100 for k in keys]
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    x = np.arange(len(keys)); w = 0.26
    ax.bar(x - w, acc, w, label="Accuracy", color=[ORANGE if k.startswith("Fused") else BLUE for k in keys])
    ax.bar(x, f1, w, label="Macro F1 x 100", color="#8FB4DE")
    ax.bar(x + w, top2, w, label="Top-2 accuracy", color=TEAL, alpha=0.8)
    for i in range(len(keys)):
        ax.text(x[i] - w, acc[i] + 1, f"{acc[i]:.1f}", ha="center", fontsize=8.2)
    ax.set_xticks(x); ax.set_xticklabels([k.replace(" (", "\n(") for k in keys], fontsize=8.6)
    ax.set_ylim(0, 105); ax.set_ylabel("Percent")
    ax.legend(fontsize=8.5, loc="upper left", ncol=3, frameon=False)
    ax.set_title("Modality ablation: the fused record beats either source alone (synthetic data)", fontsize=10.5)
    save(fig, "f04_modality_ablation.png")


def f05():
    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    ax.plot([0, 1], [0, 1], color=GREY, ls="--", lw=1.2, label="perfect calibration")
    for key, color, name, e in (("bins_uncalibrated", ORANGE, "uncalibrated", F.CAL["ece_uncalibrated"]), ("bins_isotonic", BLUE, "isotonic (shipped)", F.CAL["ece_isotonic"])):
        b = F.CAL[key]
        ax.plot([r["confidence"] for r in b], [r["accuracy"] for r in b], marker="o", color=color, lw=1.8, label=f"{name}, ECE {e:.3f}")
    ax.set_xlim(0.3, 1.0); ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("Mean predicted confidence in the bin"); ax.set_ylabel("Observed accuracy in the bin")
    ax.legend(fontsize=8.8, loc="upper left", frameon=False)
    ax.set_title("Reliability: isotonic calibration helps a little;\nthe 0.8-0.9 bin is over-confident", fontsize=10.5)
    save(fig, "f05_calibration_reliability.png")


def f06():
    t = [r["threshold"] for r in F.THR]
    cov = [r["coverage"] * 100 for r in F.THR]
    acc = [r["accuracy"] * 100 for r in F.THR]
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    ax.plot(t, acc, marker="o", color=BLUE, lw=2, label="accuracy of cases kept")
    ax.plot(t, cov, marker="s", color=ORANGE, lw=2, label="coverage (share of cases kept)")
    r85 = F.thr_row(0.85)
    ax.axvline(0.85, color=GREY, ls="--", lw=1.1)
    ax.annotate(f"0.85: keep {r85['coverage'] * 100:.1f}%\naccuracy {r85['accuracy'] * 100:.1f}%", (0.85, r85["accuracy"] * 100), xytext=(0.1, 40), fontsize=8.8,
                arrowprops=dict(arrowstyle="->", color=GREY))
    ax.set_xlabel("Confidence threshold"); ax.set_ylabel("Percent"); ax.set_ylim(0, 105)
    ax.legend(fontsize=8.8, loc="lower left", frameon=False)
    ax.set_title("Raising the confidence threshold trades coverage for accuracy", fontsize=10.5)
    save(fig, "f06_threshold_coverage.png")


def f07():
    d = [r["drop_rate"] * 100 for r in F.ROB]
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    ax.plot(d, [r["accuracy"] * 100 for r in F.ROB], marker="o", color=BLUE, lw=2, label="accuracy")
    ax.plot(d, [r["within_one"] * 100 for r in F.ROB], marker="s", color=TEAL, lw=2, label="within one level")
    ax.plot(d, [r["macro_f1"] * 100 for r in F.ROB], marker="^", color=ORANGE, lw=2, label="macro F1 x 100")
    for x_, r in zip(d, F.ROB):
        ax.text(x_, r["accuracy"] * 100 + 3.5, f"{r['accuracy'] * 100:.0f}", ha="center", fontsize=8.2, color=BLUE)
    ax.set_xlabel("Share of positive report flags removed before scoring (%)"); ax.set_ylabel("Percent"); ax.set_ylim(0, 105)
    ax.legend(fontsize=8.8, frameon=False, loc="lower left")
    ax.set_title("Robustness to a reader that misses findings (100% = no report at all)", fontsize=10.5)
    save(fig, "f07_robustness_dropped_flags.png")


def f08():
    lab = {"spo2": "SpO2", "arrival_code": "Arrival mode", "dyspnea": "Shortness of breath", "sbp": "Systolic BP", "resp_rate": "Respiratory rate", "st_elevation": "ST elevation",
           "stroke_signs": "Focal weakness / speech", "lab_troponin_high": "Troponin raised", "chest_pain": "Chest pain", "lab_lactate_high": "Lactate raised",
           "altered_mental": "Altered mental state", "heart_rate": "Heart rate", "trauma": "Trauma", "age": "Age", "ct_hemorrhage": "Intracranial haemorrhage"}
    vit = {"spo2", "arrival_code", "sbp", "resp_rate", "heart_rate", "age"}
    top = F.SHAP_TOP[:12]
    names = [lab.get(r["feature"], r["feature"]) for r in top][::-1]
    vals = [r["mean_abs_shap"] for r in top][::-1]
    cols = [BLUE if r["feature"] in vit else TEAL for r in top][::-1]
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    ax.barh(names, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + 0.006, i, f"{v:.3f}", va="center", fontsize=8.5)
    ax.set_xlabel("Mean |SHAP| over the test set and all five classes")
    ax.set_title("Global importance: vitals (blue) and report findings (teal) both matter", fontsize=10.5)
    save(fig, "f08_shap_global.png")


def f09():
    cats = list(ST["by_category"])
    nice = {"plain": "plain", "negation": "negation", "abbreviation": "abbrev.", "ocr": "OCR noise", "labs": "labs", "history": "history", "paraphrase": "paraphrase", "mixed": "mixed"}
    p = [ST["by_category"][c]["precision"] * 100 for c in cats]
    r = [ST["by_category"][c]["recall"] * 100 for c in cats]
    n = [ST["by_category"][c]["cases"] for c in cats]
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    x = np.arange(len(cats)); w = 0.38
    ax.bar(x - w / 2, p, w, label="precision", color=BLUE)
    ax.bar(x + w / 2, r, w, label="recall", color=ORANGE)
    for i in range(len(cats)):
        ax.text(x[i] - w / 2, p[i] + 1.5, f"{p[i]:.0f}", ha="center", fontsize=8)
        ax.text(x[i] + w / 2, r[i] + 1.5, f"{r[i]:.0f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([f"{nice.get(c, c)}\n(n={k})" for c, k in zip(cats, n)], fontsize=8.6)
    ax.set_ylim(0, 125); ax.set_ylabel("Percent")
    ax.axhline(ST["recall"] * 100, color=GREY, ls="--", lw=1, label=f"overall recall {ST['recall'] * 100:.1f}%")
    ax.legend(fontsize=8.8, frameon=False, loc="upper center", ncol=3)
    ax.set_title(f"Report reader on {ST['cases']} hand-written fragments: paraphrases and negation are the weak spots", fontsize=10)
    save(fig, "f09_reader_stress_by_category.png")


def f10():
    items = [("health", "GET /health"), ("queue_list", "GET /patients (queue)"), ("extract_pdf", "extract, PDF report"), ("summary_pdf", "GET summary.pdf"), ("metrics", "GET /metrics"),
             ("create_patient", "POST /patients (model + SHAP)"), ("flow_pdf_then_triage", "flow: PDF + triage"), ("login", "POST /auth/login (bcrypt)"),
             ("flow_scan_then_triage", "flow: scan + triage"), ("extract_scan_png", "extract, PNG scan (OCR)")]
    items.sort(key=lambda kv: LAT[kv[0]]["median_ms"])
    fig, ax = plt.subplots(figsize=(7.4, 4.7))
    y = np.arange(len(items))
    med = [LAT[k]["median_ms"] for k, _ in items]
    p95 = [LAT[k]["p95_ms"] for k, _ in items]
    ax.barh(y, med, color=[ORANGE if m > 100 else BLUE for m in med])
    ax.scatter(p95, y, color=NAVY, marker="|", s=140, zorder=3, label="95th percentile")
    for i, m in enumerate(med):
        ax.text(max(m, p95[i]) * 1.12, i, f"{m:,.1f} ms", va="center", fontsize=8.5)
    ax.set_xscale("log"); ax.set_xlim(1, 12000)
    ax.set_yticks(y); ax.set_yticklabels([n for _, n in items], fontsize=8.8)
    ax.set_xlabel("Response time in ms (median bar, log scale), 127.0.0.1, CPU only")
    ax.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax.set_title("HTTP response times: PDFs are instant, image scans cost about 2 s of OCR", fontsize=10.5)
    save(fig, "f10_latency.png")


def f11():
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 3.9), gridspec_kw={"width_ratios": [1, 1.25]})
    sh = [s * 100 for s in F.PRIO_SHARE]
    bars = axs[0].bar(PN, sh, color=PRIO_COLORS)
    for b, v in zip(bars, sh):
        axs[0].text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.1f}%", ha="center", fontsize=8.8)
    axs[0].set_ylabel("Share of the 6,000 rows (%)"); axs[0].set_ylim(0, 33)
    axs[0].set_title("Priority labels", fontsize=10)
    arch = sorted(F.ARCH_SHARE.items(), key=lambda kv: kv[1])
    axs[1].barh([k for k, _ in arch], [v * 100 for _, v in arch], color=TEAL)
    for i, (_, v) in enumerate(arch):
        axs[1].text(v * 100 + 0.5, i, f"{v * 100:.1f}%", va="center", fontsize=8.8)
    axs[1].set_xlim(0, 42); axs[1].set_xlabel("Share of rows (%)")
    axs[1].set_title("Clinical archetypes used to simulate patients", fontsize=10)
    fig.suptitle("Synthetic training data (seed 7307): P1 is rare, which explains its low recall", fontsize=10.5)
    fig.tight_layout()
    save(fig, "f11_priority_distribution.png")


def f12():
    B = F.BASE_PAPER_RESULTS
    labs = ["Base paper\ninternal med.\n(GB, real, 55 cl.)", "Base paper\npediatrics\n(MLP, real, 32 cl.)", "ATHENA\n(XGBoost, synthetic,\n5 priorities)"]
    top1 = [B["best_int"][1] * 100, B["best_ped"][1] * 100, F.ACC * 100]
    topk = [B["top3_best_int"] * 100, B["top3_best_ped"] * 100, F.TOP2 * 100]
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    x = np.arange(3); w = 0.34
    ax.bar(x - w / 2, top1, w, color=[GREY, GREY, ORANGE], label="Top-1 accuracy")
    ax.bar(x + w / 2, topk, w, color=["#B9C2CF", "#B9C2CF", "#E8A671"], label="Top-3 (base paper) / Top-2 (ATHENA)")
    for i in range(3):
        ax.text(x[i] - w / 2, top1[i] + 1, f"{top1[i]:.1f}", ha="center", fontsize=8.8)
        ax.text(x[i] + w / 2, topk[i] + 1, f"{topk[i]:.1f}", ha="center", fontsize=8.8)
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8.6)
    ax.set_ylim(0, 112); ax.set_ylabel("Percent")
    ax.legend(fontsize=8.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    ax.text(1, 106, "Different task and data: indicative only, not a comparison of quality", ha="center", fontsize=9, color=RED, fontweight="bold")
    ax.set_title("Base-paper best results next to ATHENA's measured results", fontsize=10.5, pad=14)
    save(fig, "f12_base_paper_context.png")


def f13():
    cm = np.array(SH["confusion_matrix"])
    exact, under, over = [], [], []
    for i in range(5):
        row = cm[i] / cm[i].sum() * 100
        exact.append(row[i])
        under.append(row[i + 1:].sum())   # model less urgent than recorded
        over.append(row[:i].sum())        # model more urgent than recorded
    fig, ax = plt.subplots(figsize=(6.8, 4.3))
    ax.bar(PN, exact, color=TEAL, label="exact")
    ax.bar(PN, under, bottom=exact, color=RED, label="under-triaged (model less urgent)")
    ax.bar(PN, over, bottom=np.array(exact) + np.array(under), color=BLUE, label="over-triaged (model more urgent)")
    for i in range(5):
        ax.text(i, exact[i] / 2, f"{exact[i]:.0f}%", ha="center", color="white", fontsize=9, fontweight="bold")
        if under[i] > 4:
            ax.text(i, exact[i] + under[i] / 2, f"{under[i]:.0f}%", ha="center", color="white", fontsize=9)
        if over[i] > 4:
            ax.text(i, exact[i] + under[i] + over[i] / 2, f"{over[i]:.0f}%", ha="center", color="white", fontsize=9)
    ax.set_ylim(0, 112); ax.set_ylabel("Share of recorded cases (%)"); ax.set_xlabel("Recorded priority")
    ax.legend(fontsize=8.2, frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0))
    ax.set_title(f"Direction of the errors: overall under-triage {F.SAFE['under_triage_any'] * 100:.1f}%, over-triage {F.SAFE['over_triage_any'] * 100:.1f}%", fontsize=10.5, pad=14)
    save(fig, "f13_triage_direction.png")


def main():
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13):
        fn()


if __name__ == "__main__":
    main()
