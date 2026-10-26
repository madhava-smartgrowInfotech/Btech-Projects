"""
make_figures.py
---------------
Draws the evaluation charts from the saved measurements - it never re-runs the timing experiments.

    python -X utf8 scripts/make_figures.py

Reads  experiments/lablens/metrics.json and api_latency.json  (written by run_experiments.py / measure_api.py).
Writes docs/figures/*.png:
  - redraws fig_extraction_by_layout, fig_threshold_sweep, fig_name_noise, fig_latency_stages
    (same drawing code as run_experiments.make_figures, legends below the axes);
  - new: fig_unit_accuracy_by_layout, fig_failure_kinds, fig_insight_coverage, fig_latency_scaling,
    fig_api_latency, fig_status_confusion.
fig_status_confusion needs a small re-count over the generated corpus (seed 42, deterministic); the counts are saved
to experiments/lablens/status_confusion.json.
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

EXP = ROOT / "experiments" / "lablens"
FIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

M = json.load(open(EXP / "metrics.json", encoding="utf-8"))
API = json.load(open(EXP / "api_latency.json", encoding="utf-8"))
plt.rcParams.update({"font.family": "serif", "font.size": 10})
BLUE, ORANGE, GREEN, PURPLE, RED, GREY = "#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728", "#7f7f7f"
LAYOUTS = ["plain", "paren", "flag", "colon", "unit_last", "mixed_sep", "tabular", "ocr_noise"]


def save(fig, name):
    fig.savefig(FIG / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", FIG / name)


# --------------------------------------------------------------------------- the four charts of run_experiments
def redraw_existing():
    import run_experiments as rx

    rx.make_figures(M["extraction"], M["name_normalisation"], M["latency"])


# --------------------------------------------------------------------------- new charts
def unit_accuracy():
    lay = M["extraction"]["per_layout"]
    vals = [lay[o]["unit_acc"] for o in LAYOUTS]
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    cols = [RED if (v is not None and v < 0.7) else BLUE for v in vals]
    ax.bar(range(len(LAYOUTS)), [v or 0 for v in vals], color=cols, width=0.62)
    for i, v in enumerate(vals):
        ax.text(i, (v or 0) + 0.015, "n/a (no rows)" if v is None else f"{v:.2f}", ha="center", fontsize=8.5, rotation=0 if v is not None else 90, va="bottom")
    ax.set_xticks(range(len(LAYOUTS)))
    ax.set_xticklabels(LAYOUTS, rotation=20)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Unit accuracy (detected rows)")
    ax.set_title("Unit accuracy by report layout")
    ax.grid(axis="y", alpha=0.3)
    ax.text(2, 0.74, "flag letter (L / H) between\nvalue and unit hides the unit", ha="center", fontsize=8, color=RED)
    fig.tight_layout()
    save(fig, "fig_unit_accuracy_by_layout.png")


def failure_kinds():
    fk = dict(M["extraction"]["failure_kinds"])
    label = {
        "missed row": "Missed row (no row produced)",
        "field error: unit": "Unit wrong or missing",
        "false positive row": "False-positive row (e.g. date line)",
        "field error: name": "Test name wrong (snapped)",
    }
    main = {label[k]: fk.pop(k) for k in list(label) if k in fk}
    other = sum(fk.values())
    if other:
        main["Several fields wrong in one row"] = other
    items = sorted(main.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    ax.barh([k for k, _ in items], [v for _, v in items], color=[RED if "Missed" in k else BLUE for k, _ in items])
    for i, (_, v) in enumerate(items):
        ax.text(v + 3, i, str(v), va="center", fontsize=9)
    ax.set_xlim(0, max(v for _, v in items) * 1.15)
    ax.set_xlabel("Occurrences over 1,680 ground-truth rows")
    ax.set_title("Where extraction goes wrong (120 generated reports)")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    save(fig, "fig_failure_kinds.png")


def insight_coverage():
    ic = M["insight_coverage"]
    rows = [("Dictionary tests\n(55)", ic["dictionary_tests_with_specific_text"], ic["dictionary_tests"]),
            ("Abnormal rows in\ncorpus (565)", ic["abnormal_rows_with_specific_text"], ic["abnormal_dictionary_rows_in_corpus"])]
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    for i, (lab, a, b) in enumerate(rows):
        ax.barh(i, a / b, color=GREEN, height=0.5, label="Test-specific text" if i == 0 else None)
        ax.barh(i, 1 - a / b, left=a / b, color="#cfd4da", height=0.5, label="Generic fallback text" if i == 0 else None)
        ax.text(a / b / 2, i, f"{a} ({a / b * 100:.1f}%)", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        ax.text(a / b + (1 - a / b) / 2, i, f"{b - a}", ha="center", va="center", color="#333", fontsize=9)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share")
    ax.set_title("How much of the explanation text is test-specific")
    ax.invert_yaxis()
    ax.legend(ncol=2, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.28), frameon=False)
    fig.tight_layout()
    save(fig, "fig_insight_coverage.png")


def latency_scaling():
    sc = M["latency"]["field_extraction_scaling_by_rows"]
    n = np.array([int(k) for k in sc])
    med = np.array([sc[k]["median_ms"] for k in sc])
    p95 = np.array([sc[k]["p95_ms"] for k in sc])
    slope, icpt = np.polyfit(n, med, 1)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(n, med, "o-", color=BLUE, label="median")
    ax.plot(n, p95, "s--", color=ORANGE, label="95th percentile")
    xs = np.linspace(0, n.max(), 50)
    ax.plot(xs, slope * xs + icpt, ":", color=GREY, label=f"linear fit ({slope:.2f} ms per row)")
    for x, y in zip(n, med):
        ax.text(x + 2, y - 11, f"{y:.1f} ms", ha="left", fontsize=8.5, color=BLUE)
    ax.set_xlabel("Rows in the report")
    ax.set_ylabel("Field-extraction time (ms)")
    ax.set_title("Parsing time grows linearly with report length")
    ax.set_xlim(0, n.max() * 1.05)
    ax.set_ylim(-14, p95.max() * 1.18)
    ax.grid(alpha=0.3)
    ax.legend(ncol=3, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    fig.tight_layout()
    save(fig, "fig_latency_scaling.png")


def api_latency():
    ep = API["endpoints"]
    names = list(ep)
    med = [ep[k]["median_ms"] for k in names]
    p95 = [ep[k]["p95_ms"] for k in names]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    y = np.arange(len(names))
    ax.barh(y, med, color=BLUE, height=0.55, label="median")
    ax.plot(p95, y, "D", color=ORANGE, markersize=5, label="95th percentile")
    for i, v in enumerate(med):
        ax.text(max(v, p95[i]) * 1.25, i, f"{v:g} ms", va="center", fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xlim(0.5, max(p95) * 6)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("Latency on 127.0.0.1 (ms, log scale)")
    ax.set_title("API response time per endpoint")
    ax.grid(axis="x", alpha=0.3)
    ax.legend(ncol=2, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.17), frameon=False)
    fig.tight_layout()
    save(fig, "fig_api_latency.png")


def status_confusion():
    import run_experiments as rx

    cache = EXP / "status_confusion.json"
    if cache.exists():
        counts = json.load(open(cache, encoding="utf-8"))["counts"]
    else:
        corpus = rx.build_corpus()
        counts = {}
        missed = 0
        total = 0
        for item in corpus:
            text = rx.ocr.extract_text(item["id"] + ".pdf", item["pdf"])
            pred = rx.ra.analyze_results(rx.ner.extract_structured_tests(text))
            used = set()
            for g in item["gt"]:
                total += 1
                hit = None
                for j, p in enumerate(pred):
                    if j not in used and rx.feq(p.result_value, g["value"]):
                        hit = j
                        break
                if hit is None:
                    missed += 1
                    continue
                used.add(hit)
                key = f'{g["status"]}|{pred[hit].status}'
                counts[key] = counts.get(key, 0) + 1
        json.dump({"counts": counts, "ground_truth_rows": total, "rows_not_detected": missed,
                   "note": "gt status = reference rule applied to the generated value and the generated range; rows the parser did not produce are excluded"},
                  open(cache, "w", encoding="utf-8"), indent=2)
        print("wrote", cache)
    labels = ["LOW", "NORMAL", "HIGH", "UNKNOWN"]
    mat = np.array([[counts.get(f"{g}|{p}", 0) for p in labels] for g in labels[:3]])
    fig, ax = plt.subplots(figsize=(6.0, 3.9))
    ax.imshow(np.log10(mat + 1), cmap="Blues", vmin=0, vmax=np.log10(mat.max() + 1) * 1.15)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]}", ha="center", va="center", fontsize=11, fontweight="bold" if i == j else "normal",
                    color="white" if i == j else "#222")
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(3))
    ax.set_yticklabels(labels[:3])
    ax.set_xlabel("Predicted status (from the extracted row)")
    ax.set_ylabel("Ground-truth status")
    acc = np.trace(mat[:, :3]) / mat.sum()
    ax.set_title(f"Status confusion over detected rows (n = {mat.sum()}, {acc * 100:.2f}% agree)")
    fig.tight_layout()
    save(fig, "fig_status_confusion.png")
    return mat, acc


def main():
    redraw_existing()
    unit_accuracy()
    failure_kinds()
    insight_coverage()
    latency_scaling()
    api_latency()
    mat, acc = status_confusion()
    print(mat.tolist(), round(float(acc), 4))


if __name__ == "__main__":
    main()
