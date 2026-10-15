"""Figures for the IEEE paper, sized for one 3.4 in column: a compact architecture, a compact main flow, and two cropped screens.\n\n    python scripts/make_paper_figures.py      -> docs/paper/*.png\n"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper"
SHOTS = ROOT / "docs" / "screenshots"
FS = 5.6


def architecture(path):
    c = Canvas(3.45, 2.75)
    W = 34.5
    c.box(1, 22.0, 32.5, 4.2, "Policyholder - browser (React 18 + Vite, port 5101)", fc=BLUE_L, fs=FS, bold=True, r=1)
    c.box(1, 16.6, 32.5, 4.2, "FastAPI REST API (port 8101): JWT, owner-only access, 42 routes", fc=INDIGO_L, ec=INDIGO, fs=FS, bold=True, r=1)
    c.arrow((17, 22.0), (17, 20.8), both=True, lw=0.8)
    svc = ["Ingest +\nparse +\nsegment", "Hybrid\nretrieval", "Answerer\n+ NLI\nscore", "Policy Card\n+ risks", "Claim\nCopilot\n+ compare"]
    bw = 6.0
    for i, t in enumerate(svc):
        x = 1 + i * (bw + 0.625)
        c.box(x, 9.4, bw, 5.8, t, fc="white", fs=4.9, r=0.8)
        c.arrow((x + bw / 2, 16.6), (x + bw / 2, 15.2), lw=0.7)
    c.box(1, 3.0, 8.4, 4.8, "SQLite\n12 tables", fc=AMBER_L, fs=FS, r=0.8)
    c.box(10.4, 3.0, 8.4, 4.8, "ChromaDB\n801 vectors", fc=AMBER_L, fs=FS, r=0.8)
    c.box(19.8, 3.0, 6.4, 4.8, "3 CPU\nmodels", fc=GREEN_L, fs=FS, r=0.8)
    c.box(27.2, 3.0, 6.3, 4.8, "Gemini\nAPI", fc=ROSE_L, fs=FS, r=0.8)
    for x in (5.2, 14.6, 23.0):
        c.arrow((x, 9.4), (x, 7.8), both=True, lw=0.7)
    c.arrow((30.3, 9.4), (30.3, 7.8), both=True, lw=0.7, ls="--")
    c.text(17.2, 1.0, "solid: local calls    dashed: external model", fs=4.8, italic=True)
    c.save(path)


def flow(path):
    c = Canvas(3.45, 3.4)
    L, R, bw, h = 1.0, 18.0, 15.5, 2.8
    q = c.box(L, 30.3, bw, h, "Question (en / hi / te)", fc=BLUE_L, fs=5.0, r=0.8)
    t = c.box(L, 26.3, bw, h, "Translate to English\nif needed", fc=BLUE_L, fs=4.8, r=0.8)
    r = c.box(L, 22.3, bw, h, "BM25 top 30 + dense\ntop 30 per query", fc=INDIGO_L, fs=4.8, r=0.8)
    f = c.box(L, 18.3, bw, h, "RRF; pool 20 + 8;\ncross-encoder; top 7", fc=INDIGO_L, fs=4.8, r=0.8)
    for a, b in ((q, t), (t, r), (r, f)):
        c.arrow(anchor(a, "b"), anchor(b, "t"), lw=0.7)
    cx = L + bw / 2
    c.arrow(anchor(f, "b"), (cx, 15.3), lw=0.7)
    c.diamond(cx, 12.6, bw, 5.4, "re-rank < 0.004\nand BM25 < 9.0 ?", fs=4.6)
    g = c.box(L, 3.6, bw, h, "Gemini: tagged clauses\n+ JSON schema", fc=GREEN_L, fs=4.8, r=0.8)
    c.arrow((cx, 9.9), (cx, 6.4), lw=0.7, label="no", fs=4.4, loff=(1.3, 0))
    d = c.box(R, 3.6, bw, h, "Drop uncited tags;\nbuild citations", fc=GREEN_L, fs=4.8, r=0.8)
    n = c.box(R, 8.4, bw, h, "NLI support per claim\n-> score 0-100", fc=GREEN_L, fs=4.8, r=0.8)
    a_ = c.box(R, 13.2, bw, h, "Answer + sources\n+ faithfulness", fc=BLUE_L, fs=4.8, r=0.8, bold=True)
    c.arrow((L + bw, 5.0), (R, 5.0), lw=0.7)
    c.arrow((R + bw / 2, 6.4), (R + bw / 2, 8.4), lw=0.7)
    c.arrow((R + bw / 2, 11.2), (R + bw / 2, 13.2), lw=0.7)
    nc = c.box(R, 19.5, bw, 3.4, "\"Not covered in this\npolicy\" (no LLM call)", fc=AMBER_L, fs=4.6, r=0.8)
    c.path([(L + bw, 12.6), (17.2, 12.6), (17.2, 21.2), (R, 21.2)], lw=0.7, label="yes", fs=4.4, seg=1, loff=(-1.2, 0))
    c.save(path)


def crop(src, box, dst, width=1000):
    im = Image.open(src).convert("RGB").crop(box)
    ratio = width / im.size[0]
    im.resize((width, int(im.size[1] * ratio)), Image.LANCZOS).save(dst, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "fig1_architecture.png")
    flow(OUT / "fig2_flow.png")
    crop(SHOTS / "11_chat_answer.png", (585, 92, 1407, 665), OUT / "fig4_answer.png")
    crop(SHOTS / "16_claim_result_partly.png", (288, 230, 1085, 900), OUT / "fig5_claim.png")
    print("saved", OUT)
