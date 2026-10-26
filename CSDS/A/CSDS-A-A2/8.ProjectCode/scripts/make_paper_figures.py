"""Figures for the IEEE paper, sized for one 3.4 in column: a compact architecture, a compact main flow, a results chart and two cropped screens.

    python scripts/make_paper_figures.py      -> docs/paper/*.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper"
SHOTS = ROOT / "docs" / "screenshots"
EVAL = ROOT / "docs" / "evaluation"
FS = 5.6


def architecture(path):
    c = Canvas(3.45, 2.75)
    c.box(1, 22.0, 32.5, 4.2, "Browser: React 19 + Vite (port 5102), camera + GPS", fc=BLUE_L, fs=FS, bold=True, r=1)
    c.box(1, 16.6, 32.5, 4.2, "FastAPI REST API (port 8102): JWT + device id, 27 endpoints", fc=INDIGO_L, ec=INDIGO, fs=FS, bold=True, r=1)
    c.arrow((17, 22.0), (17, 20.8), both=True, lw=0.8)
    svc = ["Eligibility\n+ device\nbinding", "Geo-fence\n(haversine)", "Liveness\nchallenge\n(Face Mesh)", "Face match\n(ArcFace)", "Records,\nlog, Excel\nexport"]
    bw = 6.0
    for i, t in enumerate(svc):
        x = 1 + i * (bw + 0.625)
        c.box(x, 9.4, bw, 5.8, t, fc="white", fs=4.9, r=0.8)
        c.arrow((x + bw / 2, 16.6), (x + bw / 2, 15.2), lw=0.7)
    c.box(1, 3.0, 12.0, 4.8, "SQLite\n5 tables", fc=AMBER_L, fs=FS, r=0.8)
    c.box(14.2, 3.0, 19.3, 4.8, "MediaPipe Face Mesh +\nInsightFace buffalo_l (CPU)", fc=GREEN_L, fs=FS, r=0.8)
    c.arrow((7.0, 9.4), (7.0, 7.8), both=True, lw=0.7)
    c.arrow((23.9, 9.4), (23.9, 7.8), both=True, lw=0.7)
    c.arrow((17.1, 9.4), (19.5, 7.8), both=True, lw=0.7)
    c.text(17.2, 1.0, "core/ services run in the API process; no external service", fs=4.8, italic=True)
    c.save(path)


def flow(path):
    c = Canvas(3.45, 3.4)  # trimmed below
    L, R, bw, h = 1.0, 18.0, 15.5, 2.8
    cx = L + bw / 2
    a = c.box(L, 30.3, bw, h, "Student signs in\n(JWT + device)", fc=BLUE_L, fs=4.8, r=0.8)
    b = c.box(L, 26.0, bw, h, "1 Eligibility: live, roll\nallowed, not marked", fc=INDIGO_L, fs=4.6, r=0.8)
    g = c.box(L, 21.7, bw, h, "2 Geo-fence: d <= 75 m,\nGPS accuracy <= 150 m", fc=INDIGO_L, fs=4.6, r=0.8)
    lv = c.box(L, 17.4, bw, h, "3 Random challenge on\ntwo photos (3 tries)", fc=INDIGO_L, fs=4.6, r=0.8)
    for p, q in ((a, b), (b, g), (g, lv)):
        c.arrow(anchor(p, "b"), anchor(q, "t"), lw=0.7)
    fm = c.box(L, 13.1, bw, h, "4 Embeddings (ArcFace)\n512-d, cosine", fc=INDIGO_L, fs=4.6, r=0.8)
    c.arrow(anchor(lv, "b"), anchor(fm, "t"), lw=0.7)
    c.arrow(anchor(fm, "b"), (cx, 10.4), lw=0.7)
    c.diamond(cx, 7.7, bw, 5.2, "consistency >= 0.45,\nidentity >= 0.40,\nduplicate < 0.45 ?", fs=4.2)
    ok = c.box(R, 5.9, bw, h, "Record attendance\n+ log (Excel export)", fc=GREEN_L, fs=4.6, r=0.8, bold=True)
    c.arrow((L + bw, 7.7), (R, 7.3), lw=0.7, label="yes", fs=4.2, loff=(0, 1.1))
    bl = c.box(R, 21.7, bw, 6.6, "Any failed stage:\nblock, show reason,\nwrite attempt row\n(3 liveness fails\nlock the wizard)", fc=ROSE_L, fs=4.4, r=0.8)
    c.text(R + bw / 2, 19.6, "each stage appends a\nrow to verification_attempts", fs=4.2, italic=True)
    c.arrow((L + bw, 27.4), (R, 27.4), lw=0.6, ls="--")
    c.arrow((L + bw, 23.1), (R, 23.1), lw=0.6, ls="--")
    c.arrow((L + bw, 18.8), (R, 21.7), lw=0.6, ls="--")
    c.save(path)
    from PIL import ImageChops
    im = Image.open(path).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    im.crop((0, max(0, bbox[1] - 6), im.size[0], min(im.size[1], bbox[3] + 6))).save(path)


def results_chart(path):
    fv = json.loads((EVAL / "face_verification.json").read_text())
    pb = json.loads((EVAL / "photo_bank_attack.json").read_text())
    sweep = [s for s in fv["sweep"] if 0.0 <= s["threshold"] <= 0.7]
    fig, (a, b) = plt.subplots(2, 1, figsize=(3.45, 3.5), gridspec_kw={"height_ratios": [1, 1.05], "hspace": 0.62})
    th = [s["threshold"] for s in sweep]
    a.plot(th, [100 * s["tar"] for s in sweep], color="#2a7a4b", lw=1.2, label="TAR (genuine accepted)")
    a.plot(th, [100 * s["far"] for s in sweep], color="#c0392b", lw=1.2, label="FAR (impostor accepted)")
    for x, t in ((0.40, "identity 0.40"), (0.45, "duplicate 0.45")):
        a.axvline(x, color="#44506b", lw=0.6, ls="--")
    a.text(0.395, 45, "0.40", fontsize=5.5, ha="right", color="#44506b")
    a.text(0.455, 45, "0.45", fontsize=5.5, ha="left", color="#44506b")
    a.set_xlabel("cosine-similarity threshold", fontsize=6.5, labelpad=1)
    a.set_ylabel("%", fontsize=6.5, labelpad=1)
    a.set_title("(a) LFW verification: 2,141 genuine / 2,166 impostor pairs", fontsize=6.5, pad=2)
    a.legend(fontsize=5.5, loc="center left", frameon=False)
    a.tick_params(labelsize=6, length=2)
    names = ["TURN_LEFT", "TURN_RIGHT", "LOOK_UP", "LOOK_DOWN", "TILT_LEFT", "TILT_RIGHT", "OPEN_MOUTH", "CLOSE_EYES"]
    vals = [100 * pb["by_challenge"][n]["full_chain_rate"] for n in names]
    lab = [n.replace("_", " ").title() for n in names]
    y = range(len(names))
    b.barh(list(y), vals, color="#c0392b", height=0.62)
    b.set_yticks(list(y))
    b.set_yticklabels(lab, fontsize=5.5)
    b.invert_yaxis()
    for i, v in enumerate(vals):
        b.text(v + 1, i, f"{v:.1f}", va="center", fontsize=5.5)
    b.set_xlim(0, 112)
    b.set_xlabel("attack success %, attacker holds several photos of the victim", fontsize=6, labelpad=1)
    b.set_title(f"(b) Photo-bank attack on the full chain ({pb['victims']} victims)", fontsize=6.5, pad=2)
    b.tick_params(labelsize=6, length=2)
    for ax in (a, b):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.94, bottom=0.1)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def crop(src, box, dst, width=1000):
    im = Image.open(src).convert("RGB").crop(box)
    ratio = width / im.size[0]
    im.resize((width, int(im.size[1] * ratio)), Image.LANCZOS).save(dst, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "fig1_architecture.png")
    flow(OUT / "fig2_flow.png")
    results_chart(OUT / "fig3_results.png")
    crop(SHOTS / "24_checkin_marked.png", (100, 475, 1340, 1010), OUT / "fig4_marked.png")
    crop(SHOTS / "26_checkin_static_photo_rejected.png", (100, 480, 1340, 830), OUT / "fig5_rejected.png")
    print("saved", OUT)
