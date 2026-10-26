"""Figures for the IEEE paper, sized for one 3.4 in column: architecture, main flow, a results chart and two cropped screens.

    python scripts/make_paper_figures.py      -> docs/charts/p_*.png      (system python with matplotlib + Pillow)
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
OUT = ROOT / "docs" / "charts"
SHOTS = ROOT / "docs" / "screenshots"
STUDY = ROOT / "experiments" / "study"
FS = 5.0


def architecture(path):
    c = Canvas(3.45, 2.75)
    c.box(1, 22.6, 32.5, 4.2, "Browser: React 19 PWA (Vite, port 5107) - Leaflet map, Web Speech API,\ngeolocation, MediaRecorder, SafePhrase matcher (localStorage)", fc=BLUE_L, fs=4.5, bold=True, r=1)
    c.box(1, 15.2, 32.5, 4.6, "FastAPI (port 8107): REST routers auth, guardians, risk, routes, places, sos,\nevidence, track, ai + WebSocket /ws/track/{token}; JWT, owner-scoped queries", fc=INDIGO_L, ec=INDIGO, fs=4.5, bold=True, r=1)
    c.arrow((17, 22.6), (17, 19.8), both=True, lw=0.8)
    svc = ["Route risk\nscorer\n(467 tiers)", "Evidence\nSHA-256", "Alerts\nTelegram /\nGmail", "WebSocket\nmanager", "Gemini\nassistant"]
    bw = 6.0
    for i, t in enumerate(svc):
        x = 1 + i * (bw + 0.625)
        c.box(x, 7.6, bw, 5.4, t, fc="white", fs=4.3, r=0.8)
        c.arrow((x + bw / 2, 15.2), (x + bw / 2, 13.0), lw=0.7)
    c.box(1, 0.8, 10.5, 4.6, "SQLite, 6 tables\n(users, guardians,\nsessions, pings...)", fc=AMBER_L, fs=4.3, r=0.8)
    c.box(12.4, 0.8, 10.0, 4.6, "district_risk.csv,\nrisk_model.joblib,\nevidence files", fc=GREEN_L, fs=4.3, r=0.8)
    c.box(23.3, 0.8, 10.2, 4.6, "OSRM, Nominatim,\nOSM tiles, Gemini,\nTelegram, Gmail", fc=ROSE_L, fs=4.3, r=0.8)
    for x in (6.2, 17.4):
        c.arrow((x, 7.6), (x, 5.4), both=True, lw=0.7)
    c.arrow((28.4, 7.6), (28.4, 5.4), both=True, lw=0.7, ls="--")
    c.save(path)


def flow(path):
    c = Canvas(3.45, 3.0)
    bw, h = 15.0, 3.2
    L, R = 1.5, 18.0
    left = [("1 Register, add\nguardians", BLUE_L), ("2 Plan route: OSRM\nalternatives, risk score", INDIGO_L), ("3 SafePhrase listens\n(Web Speech API)", INDIGO_L),
            ("4 SOS: tap or phrase;\nPOST /sos/start", ROSE_L), ("5 Alerts + tracking link\nto guardians", ROSE_L)]
    right = [("6 Position every ~4 s\nPOST /location", AMBER_L), ("7 WebSocket push to\nguardian page", AMBER_L), ("8 Photo / audio evidence,\nSHA-256 + time", GREEN_L),
             ("9 Hold 3 s to cancel", GREEN_L), ("10 Guardian page shows\ncancelled", BLUE_L)]
    ys = [24.6, 19.6, 14.6, 9.6, 4.6]
    lb = [c.box(L, y, bw, h + 0.4, t, fc=f, fs=4.4, r=0.8) for (t, f), y in zip(left, ys)]
    rb = [c.box(R, y, bw, h + 0.4, t, fc=f, fs=4.4, r=0.8) for (t, f), y in zip(right, ys)]
    for a, b in zip(lb[:-1], lb[1:]):
        c.arrow(anchor(a, "b"), anchor(b, "t"), lw=0.7)
    for a, b in zip(rb[:-1], rb[1:]):
        c.arrow(anchor(a, "b"), anchor(b, "t"), lw=0.7)
    c.path([(L + bw, ys[-1] + 1.8), (16.7, ys[-1] + 1.8), (16.7, ys[0] + 1.8), (R, ys[0] + 1.8)], lw=0.7)
    c.text(17.2, 1.8, "steps 1-3 before an emergency; 4-5 start it; 6-10 run during and after it", fs=4.0, italic=True)
    c.save(path)


def results_chart(path):
    M = json.loads((STUDY / "metrics.json").read_text(encoding="utf-8"))
    S = json.loads((STUDY / "safephrase.json").read_text(encoding="utf-8"))
    fig = plt.figure(figsize=(3.45, 3.15))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.85], width_ratios=[1, 1.05], hspace=0.62, wspace=0.55)
    a1, a2, a3 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    ks = M["k_sweep"]
    a1.plot([r["k"] for r in ks], [r["silhouette"] for r in ks], "o-", ms=2.5, lw=1, color="#2f6fb0", label="silhouette")
    a1.set_xlabel("k", fontsize=5.5)
    a1.set_ylabel("silhouette", fontsize=5.5, color="#2f6fb0")
    a1.axvline(3, color="#9aa5ba", ls=":", lw=0.8)
    a1.tick_params(labelsize=5.2)
    b1 = a1.twinx()
    b1.plot([r["k"] for r in ks], [r["davies_bouldin"] for r in ks], "s--", ms=2.3, lw=0.9, color="#c8453c")
    b1.set_ylabel("Davies-Bouldin", fontsize=5.5, color="#c8453c")
    b1.tick_params(labelsize=5.2)
    a1.set_title("(a) k sweep, 467 districts\n(dotted: shipped k = 3)", fontsize=5.6)
    sens = ["Low", "Medium", "High", "Ultra"]
    rec = [S["by_sensitivity"][s]["recall"] * 100 for s in sens]
    fp = [S["by_sensitivity"][s]["false_trigger_rate"] * 100 for s in sens]
    x = range(4)
    a2.bar([i - 0.2 for i in x], rec, 0.38, color="#2e8b57", label="recall")
    a2.bar([i + 0.2 for i in x], fp, 0.38, color="#c8453c", label="false triggers")
    for i in x:
        a2.text(i - 0.2, rec[i] + 2, f"{rec[i]:.0f}", ha="center", fontsize=4.8)
        a2.text(i + 0.2, fp[i] + 2, f"{fp[i]:.0f}", ha="center", fontsize=4.8)
    a2.set_xticks(list(x), sens, fontsize=5.2)
    a2.set_ylim(0, 118)
    a2.set_ylabel("percent", fontsize=5.5)
    a2.tick_params(axis="y", labelsize=5.2)
    a2.legend(fontsize=4.8, frameon=False, loc="upper left")
    a2.set_title("(b) SafePhrase matcher,\nwritten transcripts", fontsize=5.6)
    cov = M["city_coverage"]["nearest_district_km"]
    items = sorted(cov.items(), key=lambda kv: -kv[1])[:10]
    a3.bar([k for k, _ in items], [v for _, v in items], color=["#c8453c" if v > 100 else "#e0a030" for _, v in items], width=0.65)
    for i, (_, v) in enumerate(items):
        a3.text(i, v + 4, f"{v:.0f}", ha="center", fontsize=4.8)
    a3.axhline(100, color="#333", ls="--", lw=0.6)
    a3.set_ylabel("km", fontsize=5.5)
    a3.tick_params(axis="y", labelsize=5.2)
    a3.set_xticks(range(len(items)), [k for k, _ in items], fontsize=4.8, rotation=25, ha="right")
    a3.set_title("(c) nearest district to each city centre, 10 farthest of 40 (dashed: 100 km)", fontsize=5.4)
    for a in (a1, a2, a3):
        a.spines[["top", "right"]].set_visible(False)
    b1.spines["top"].set_visible(False)
    fig.savefig(path, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def crop(src, box, dst, width=1100):
    im = Image.open(src).convert("RGB").crop(box)
    ratio = width / im.size[0]
    im.resize((width, int(im.size[1] * ratio)), Image.LANCZOS).save(dst, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "p_arch.png")
    flow(OUT / "p_flow.png")
    results_chart(OUT / "p_results.png")
    crop(SHOTS / "06_route_delhi_jaipur.png", (392, 205, 1368, 865), OUT / "p_route.png")
    crop(SHOTS / "14_guardian_tracking.png", (384, 60, 1056, 600), OUT / "p_track.png", width=900)
    print("done")
