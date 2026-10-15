"""Flowchart of the core algorithm (backend/app/services/engine/engine.py: solve)."""
from __future__ import annotations

from diagram_kit import AMBER_L, GREEN_L, INDIGO_L, ROSE_L, Canvas


def flowchart(out):
    c = Canvas(9.6, 12.6)
    c.ax.set_ylim(-15, 111)  # coordinates below run from about -11 (bottom) to 109 (top)
    cx, w = 34, 46

    def proc(y, text, h=7.2, fc=INDIGO_L):
        return c.box(cx - w / 2, y - h / 2, w, h, text, fc=fc, fs=7.0)

    c.terminal(cx, 106, 22, 5, "Start")
    proc(98, "Load the sitting: candidates (paper, department,\nneeds accessible seat), selected halls, rules, seed")
    proc(88.5, "Pre-checks: enough seats? enough accessible seats?\nlargest paper within the colour-class ceiling?")
    c.diamond(cx, 77, 30, 9, "Problem\nfound?")
    c.box(62, 71.5, 22, 11, "Stop: explain the reason\nin plain language and\nsuggest a fix", fc=ROSE_L, fs=6.6)
    proc(64, "Stage A, pass 1 (CP-SAT): choose the fewest halls; allocate\ngroups (paper, department, accessible) to halls and colour\nclasses; minimise peak fill, spread papers and departments", h=8.6)
    proc(53.5, "Stage A, pass 2: keep that optimum and follow seeded\nrandom weights, so classes and halls cannot be guessed")
    c.diamond(cx, 43.5, 32, 9, "Allocation\nfound?")
    c.box(62, 38, 22, 11, "Stop: explain that no\nsharing of candidates\nmeets every rule", fc=ROSE_L, fs=6.6)
    proc(32.5, "Split the candidates between halls with a seeded shuffle")
    proc(22.5, "Stage B in every hall, in parallel threads (CP-SAT): one seat\nper candidate, accessible needs, roll-number gap; minimise\nsame-department neighbours + seeded random term", h=8.6)
    c.diamond(cx, 11.2, 34, 9.4, "Every hall\nsolved?")
    c.box(60, 6.8, 30, 9, "No: a hall that found nothing gets one try with\n4x the budget; if it still fails, ease that hall's\ncapacity and re-run Stage A (at most 5 times)", fc=AMBER_L, fs=6.2)
    c.box(cx - 24, -6.5, 48, 9, "Independent validator (no solver) re-checks every rule: scorecard,\nroll-order baseline; store the plan with seed, rules, three SHA-256 hashes", fc=GREEN_L, fs=6.6)
    c.terminal(cx, -10.2, 22, 4.6, "End")
    c.arrow((cx, 103.5), (cx, 101.6))
    c.arrow((cx, 94.4), (cx, 92.1))
    c.arrow((cx, 84.9), (cx, 81.5))
    c.arrow((cx + 15, 77), (62, 77), label="yes", fs=6.5, loff=(0, 1.6))
    c.arrow((cx, 72.5), (cx, 68.3), label="no", fs=6.5, loff=(2.2, 0))
    c.arrow((cx, 59.7), (cx, 57.1))
    c.arrow((cx, 49.9), (cx, 48))
    c.arrow((cx + 16, 43.5), (62, 43.5), label="no", fs=6.5, loff=(0, 1.6))
    c.arrow((cx, 39), (cx, 36.1), label="yes", fs=6.5, loff=(2.2, 0))
    c.arrow((cx, 28.9), (cx, 26.8))
    c.arrow((cx, 18.2), (cx, 15.9))
    c.arrow((cx + 17, 11.2), (60, 11.2), label="no", fs=6.5, loff=(0, 1.6))
    c.path([(90, 11.3), (94, 11.3), (94, 64), (cx + w / 2, 64)])
    c.arrow((cx, 6.5), (cx, 2.5), label="yes", fs=6.5, loff=(2.2, 0))
    c.arrow((cx, -6.5), (cx, -7.9))
    c.save(out)
