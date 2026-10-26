"""Figures for the IEEE paper, sized for one 3.4 in column: architecture, main flow, a results chart, a threshold chart and two cropped screens.

    python scripts/make_paper_figures.py      -> docs/paper/*.png      (system python with matplotlib + Pillow)
Every value is read from experiments/**/metrics.json (or the cached embeddings), never typed in.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper"
SHOTS = ROOT / "docs" / "screenshots"
EXP = ROOT / "experiments"
FS = 5.0


def j(p):
    return json.loads((EXP / p).read_text(encoding="utf-8"))


def architecture(path):
    c = Canvas(3.45, 3.2)
    W = 33.5
    c.box(1, 28.0, W - 1, 3.2, "Browser: React 19 + Vite app (port 5106)", fc=BLUE_L, fs=FS + 0.3, bold=True, r=1)
    c.box(1, 22.6, W - 1, 3.6, "FastAPI (port 8106): routers auth, contracts, eval\nJWT (HS256) + bcrypt, owner check on every contract route", fc=INDIGO_L, ec=INDIGO, fs=FS - 0.1, bold=True, r=1)
    c.arrow((17, 28.0), (17, 26.2), both=True, lw=0.8)
    c.zone(1, 8.4, 22.6, 12.8, "pipeline.process_upload()", fs=4.6)
    svc = [("parsing\nPyMuPDF,\npython-docx", 1.8, 14.6), ("classify\nembedding +\n20 centroids", 8.9, 14.6), ("rules\n8 regex\n(Indian law)", 16.0, 14.6),
           ("graph\n3 risky\ncombinations", 1.8, 9.6), ("complexity\nFlesch, jargon\n-> A-F", 8.9, 9.6), ("explain\nreason, safer\nwording, summary", 16.0, 9.6)]
    for t, x, y in svc:
        c.box(x, y, 6.5, 4.0, t, fc="white", fs=3.7, r=0.6)
    c.arrow((12.3, 22.6), (12.3, 21.2), lw=0.8)
    c.box(24.6, 8.4, 8.9, 12.8, "Google Gemini API\n- gemini-embedding-001\n  (3,072-d vectors)\n- text model:\n  tie-break,\n  reasons, safer\n  wording, summary", fc=ROSE_L, ec="#c98a8a", fs=4.0, r=0.8)
    c.arrow((23.6, 14.8), (24.6, 14.8), both=True, lw=0.8, ls="--")
    c.box(1, 1.2, 10.2, 5.4, "SQLite: users,\ncontracts, clauses\n(+ embedding BLOB),\nflags", fc=AMBER_L, fs=4.0, r=0.8)
    c.box(12.1, 1.2, 10.2, 5.4, "centroid cache\n(npz, 20 x 3,072)\nCUAD splits,\nmetrics.json", fc=AMBER_L, fs=4.0, r=0.8)
    c.box(23.2, 1.2, 10.3, 5.4, "No GPU, no vector\nor graph database:\ngraph rebuilt\nper request", fc=GREY_L, fs=4.0, r=0.8)
    c.arrow((6, 8.4), (6, 6.6), both=True, lw=0.7, ls=":")
    c.arrow((17, 8.4), (17, 6.6), both=True, lw=0.7, ls=":")
    c.save(path)


def flow(path):
    c = Canvas(3.45, 3.3)
    bw, h = 15.2, 3.4
    L, R = 1.0, 18.3
    left = [("1 Upload PDF / DOCX\n(signed-in user)", BLUE_L), ("2 Parse pages\n(PDF per page, DOCX = 1)", BLUE_L), ("3 Segment into clauses\n(headings, else paragraphs)", BLUE_L),
            ("4 Gemini embedding;\nnearest of 20 centroids", ROSE_L), ("5 Eight regex rules\n(per clause)", INDIGO_L)]
    right = [("6 Gemini explains each\nflag: reason, wording", ROSE_L), ("7 Three risky\ncombinations", INDIGO_L), ("8 Complexity score\nand grade A-F", INDIGO_L),
             ("9 Gemini summary and\nkey obligations", ROSE_L), ("10 Commit to SQLite;\nreport, clauses, graph", GREEN_L)]
    ys = [27.2, 21.8, 16.4, 11.0, 5.6]
    lb = [c.box(L, y, bw, h, t, fc=f, fs=4.3, r=0.8) for (t, f), y in zip(left, ys)]
    rb = [c.box(R, y, bw, h, t, fc=f, fs=4.3, r=0.8) for (t, f), y in zip(right, ys)]
    for a, b in zip(lb[:-1], lb[1:]):
        c.arrow(anchor(a, "b"), anchor(b, "t"), lw=0.7)
    for a, b in zip(rb[:-1], rb[1:]):
        c.arrow(anchor(a, "b"), anchor(b, "t"), lw=0.7)
    c.path([(L + bw, ys[-1] + 1.7), (17.2, ys[-1] + 1.7), (17.2, ys[0] + 1.7), (R, ys[0] + 1.7)], lw=0.7)
    c.text(17.2, 2.4, "Pink steps call Gemini; the rest is local code.", fs=4.2, italic=True)
    c.save(path)


def results_chart(path):
    cl = j("classification/metrics.json")
    ru = j("rules/metrics.json")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.45, 2.05), gridspec_kw={"width_ratios": [1.15, 1]})
    b = cl["baselines_top1"]
    order = [("chance (20 categories)", "chance"), ("Gemini embedding 1-NN", "1-NN"), ("TF-IDF nearest centroid", "TF-IDF\ncentroid"),
             ("TF-IDF + logistic regression", "TF-IDF\n+ LR"), ("Gemini embedding 5-NN", "5-NN"),
             ("Gemini embedding nearest centroid (shipped)", "centroid\n(shipped)"), ("Gemini embedding + logistic regression", "emb.\n+ LR")]
    vals = [b[k] for k, _ in order]
    cols = ["#9aa5ba", "#3b82c4", "#3b82c4", "#3b82c4", "#4a4ad0", "#2f9e6e", "#4a4ad0"]
    a1.bar(range(len(vals)), vals, color=cols, width=0.7)
    for i, v in enumerate(vals):
        a1.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=4.4)
    a1.set_xticks(range(len(vals)))
    a1.set_xticklabels([n for _, n in order], fontsize=3.9)
    a1.set_ylim(0, 1.0)
    a1.tick_params(axis="y", labelsize=5)
    a1.set_ylabel("top-1 accuracy, 240 CUAD spans", fontsize=5)
    a1.set_title("(a) clause classification", fontsize=5.6)
    s, p = ru["shipped_set"]["overall"], ru["probe_set"]["overall"]
    x = np.arange(3)
    w = 0.36
    r1 = a2.bar(x - w / 2, [s["precision"], s["recall"], s["f1"]], w, color="#4a4ad0", label="shipped set (n=40)")
    r2 = a2.bar(x + w / 2, [p["precision"], p["recall"], p["f1"]], w, color="#e0a030", label="probe set (n=40)")
    for rr in (r1, r2):
        for r in rr:
            a2.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.02, f"{r.get_height():.2f}", ha="center", fontsize=4.4)
    a2.set_xticks(x)
    a2.set_xticklabels(["precision", "recall", "F1"], fontsize=5)
    a2.set_ylim(0, 1.3)
    a2.tick_params(axis="y", labelsize=5)
    a2.legend(fontsize=4.3, frameon=False, loc="upper right")
    a2.set_title("(b) predatory-clause rules", fontsize=5.6)
    for a in (a1, a2):
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def threshold_chart(path):
    z = np.load(EXP / "classification" / "embeddings.npz")
    tr, ev = z["train"], z["eval"]
    it = json.loads((ROOT / "data/sample/cuad_train_examples.json").read_text(encoding="utf-8"))
    lab = np.array([i for i, c in enumerate(it["categories"]) for _ in it["examples"][c]])
    cen = np.vstack([tr[lab == k].mean(axis=0) for k in range(20)])
    u = lambda a: a / np.linalg.norm(a, axis=-1, keepdims=True)  # noqa: E731
    srt = np.sort(u(ev) @ u(cen).T, axis=1)
    top1, margin = srt[:, -1], srt[:, -1] - srt[:, -2]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.45, 1.55))
    a1.hist(top1, bins=np.arange(0.3, 0.9, 0.03), color="#3b82c4", edgecolor="white", lw=0.3)
    a1.axvline(0.60, color="#d9576b", ls="--", lw=0.8)
    a1.axvline(0.35, color="#e0a030", ls="--", lw=0.8)
    a1.text(0.37, a1.get_ylim()[1] * 0.9, "floor 0.35", fontsize=4.4, color="#b37a10")
    a1.text(0.455, a1.get_ylim()[1] * 0.70, "tie-break\nbelow 0.60", fontsize=4.4, color="#d9576b")
    a1.set_xlabel("top-1 cosine similarity", fontsize=5)
    a1.set_ylabel("held-out spans", fontsize=5)
    a1.set_title("(a) top-1 similarity", fontsize=5.6)
    a2.hist(margin, bins=np.arange(0, 0.12, 0.008), color="#4a4ad0", edgecolor="white", lw=0.3)
    a2.axvline(0.03, color="#d9576b", ls="--", lw=0.8)
    a2.text(0.034, a2.get_ylim()[1] * 0.85, f"margin < 0.03:\n{int((margin < 0.03).sum())} of 240", fontsize=4.4, color="#d9576b")
    a2.set_xlabel("top-1 minus top-2 similarity", fontsize=5)
    a2.set_title("(b) margin", fontsize=5.6)
    for a in (a1, a2):
        a.tick_params(labelsize=4.8)
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def crop(src, box, dst, width=1150):
    im = Image.open(src).convert("RGB").crop(box)
    ratio = width / im.size[0]
    im.resize((width, int(im.size[1] * ratio)), Image.LANCZOS).save(dst, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "fig1_architecture.png")
    flow(OUT / "fig2_flow.png")
    results_chart(OUT / "fig3_results.png")
    threshold_chart(OUT / "fig6_thresholds.png")
    crop(SHOTS / "08_report_freelance_top.png", (288, 205, 1412, 880), OUT / "fig4_report.png")
    crop(SHOTS / "11_clause_detail_termination.png", (288, 140, 1412, 745), OUT / "fig5_clause.png")
    print("saved", OUT)
