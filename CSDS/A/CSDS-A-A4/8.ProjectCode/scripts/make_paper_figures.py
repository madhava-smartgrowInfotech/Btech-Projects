"""Compact figures for the IEEE paper (one-column width, 3.4 in), drawn from the same facts as the report.

    python scripts/make_paper_figures.py   ->  docs/paper/fig1_architecture.png, fig2_flow.png, fig4_plan.png, fig5_compare.png
(fig3_results.png is made by make_result_charts.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image  # noqa: E402

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper"
OUT.mkdir(parents=True, exist_ok=True)


def fig1():
    c = Canvas(3.4, 2.7)
    c.zone(0.3, 21.4, 33.4, 5.5, "", fc="#f4f5fb")
    c.box(0.9, 22.0, 15.6, 4.0, "Planner (browser)", fc="white", fs=5.4, r=0.8, lw=0.8)
    c.box(17.5, 22.0, 15.6, 4.0, "Analyst (CLI)", fc="white", fs=5.4, r=0.8, lw=0.8)
    c.box(0.3, 16.8, 33.4, 3.6, "React 18 + Vite: 7 pages, SVG network map, charts", fc=BLUE_L, fs=5.3, r=0.8, lw=0.8)
    c.box(0.3, 12.6, 33.4, 3.4, "FastAPI: 14 endpoints, validation, background jobs", fc=INDIGO_L, ec=INDIGO, fs=5.5, r=0.8, lw=0.8, bold=True)
    mods = ["data.py\nclean, features", "forecast.py\nRandom Forest", "model.py\nMIP, KPIs", "matheuristic.py\nsearch + kernel", "baselines.py\nrolling.py"]
    for i, t in enumerate(mods):
        x = 0.3 + i * 6.8
        c.box(x, 7.4, 6.4, 4.2, t, fc=GREEN_L, fs=4.0, r=0.6, lw=0.7)
    c.box(0.3, 1.0, 12.4, 4.4, "scikit-learn\nRandom Forest", fc=AMBER_L, fs=4.9, r=0.8, lw=0.8)
    c.box(13.6, 1.0, 9.6, 4.4, "PuLP + CBC", fc=AMBER_L, fs=5.0, r=0.8, lw=0.8)
    c.box(24.1, 1.0, 9.6, 4.4, "CSV, joblib,\nJSON files", fc=GREY_L, fs=4.9, r=0.8, lw=0.8)
    c.arrow((8.5, 22.0), (8.5, 20.4), both=True, lw=0.8)
    c.arrow((17, 16.8), (17, 16.0), both=True, lw=0.8)
    c.arrow((17, 12.6), (17, 11.6), both=True, lw=0.8)
    for x in (6.5, 18.3, 28.5):
        c.arrow((x, 7.4), (x, 5.4), both=True, lw=0.8)
    c.save(OUT / "fig1_architecture.png")


def fig2():
    c = Canvas(3.4, 3.7)
    cx, w = 16.0, 28
    ys = [34.4, 30.0, 25.6, 21.2, 16.8, 12.4, 8.0, 3.6]
    items = [("Order history, 90 regions x 36 months\nclean, 19 shifted features", BLUE_L),
             ("Random Forest (400 trees)\nforecast next-month demand", INDIGO_L),
             ("Instance: distances x1.25, time, cost,\ncapacity = 1.25 x demand / p", INDIGO_L),
             ("Matheuristic: construct, screened\nswap/drop/add, kernel search", GREEN_L),
             ("Exact assignment MIPs (CBC)\nprice each candidate hub set", GREEN_L),
             ("Score the plan on realised demand:\ncost, delivery time, fulfilment", AMBER_L),
             ("Compare with 5 baselines\nand a static plan", AMBER_L),
             ("Next month: re-forecast, re-plan", ROSE_L)]
    for y, (t, fc) in zip(ys, items):
        c.box(cx - w / 2, y - 1.8, w, 3.6, t, fc=fc, fs=4.9, r=0.7, lw=0.8)
    for a, b in zip(ys[:-1], ys[1:]):
        c.arrow((cx, a - 1.8), (cx, b + 1.8), lw=0.8)
    c.path([(cx + w / 2, ys[-1]), (cx + w / 2 + 1.6, ys[-1]), (cx + w / 2 + 1.6, ys[0]), (cx + w / 2, ys[0])], ls="--", lw=0.8)
    c.save(OUT / "fig2_flow.png")


def crops():
    im = Image.open(ROOT / "docs" / "screenshots" / "09_plan_kpis.png")
    im.crop((280, 80, 1430, 640)).save(OUT / "fig4_plan.png")
    im = Image.open(ROOT / "docs" / "screenshots" / "16_compare_full.png")
    im.crop((285, 745, 1395, 1510)).save(OUT / "fig5_compare.png")


if __name__ == "__main__":
    fig1()
    fig2()
    crops()
    print("paper figures done")
