"""Data-flow diagrams, level 1 and level 2 (expansion of process 3)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, INDIGO, INDIGO_L, ROSE_L, Canvas

STORE = "#fff8e8"


def _store(c, x, y, w, text):
    c.box(x, y, w, 5.4, "", fc=STORE, r=0.6)
    c.line((x + 3.4, y), (x + 3.4, y + 5.4), lw=1.0)
    c.text(x + 3.4 + (w - 3.4) / 2, y + 2.7, text, fs=7.3)


def _proc(c, cx, cy, text, fc=INDIGO_L, w=20, h=9.6, fs=7.4):
    c.ellipse(cx, cy, w, h, text, fc=fc, ec=INDIGO, fs=fs)


def dfd1(out):
    c = Canvas(10.4, 8.2)
    c.box(1, 34, 14, 10, "Exam\ncontroller", fc=BLUE_L, bold=True, fs=8)
    ys = {"1": 73, "2": 61, "3": 49, "4": 37, "5": 25, "8": 12}
    names = {"1": "1  Authenticate\nand authorise", "2": "2  Import and\nvalidate data", "3": "3  Generate\nseating plan",
             "4": "4  Review, swap\nand publish", "5": "5  Produce outputs\n(PDF, Excel, QR)", "8": "8  Analytics and\naudit view"}
    for k, y in ys.items():
        _proc(c, 34, y, names[k], fc=ROSE_L if k == "8" else INDIGO_L)
    for k, lab in [("1", "credentials"), ("2", "data files"), ("3", "rules, halls, seed"), ("4", "swap, publish"), ("5", "download"), ("8", "view")]:
        c.arrow((15, 39), (24.2, ys[k]), lw=0.9, label=lab if k in "1234" else None, fs=6.3, lpos=0.62, loff=(0, 1.3))
    _store(c, 54, 70.3, 24, "D1  Users and settings")
    _store(c, 54, 58.3, 24, "D2  Reference data")
    _store(c, 54, 38.5, 24, "D3  Plans and seats")
    _store(c, 54, 18.3, 24, "D4  Attendance")
    _store(c, 54, 3.3, 24, "D5  Audit trail")
    c.arrow((44, 73), (54, 73), both=True)
    c.arrow((44, 61), (54, 61), both=True)
    c.arrow((54, 59.2), (43.5, 51.8), label="candidates, halls,\ntimetable", fs=6.3, lpos=0.5, loff=(5.5, -3))
    c.arrow((44, 47), (54, 41.8), label="new plan", fs=6.3, lpos=0.45, loff=(0, 2))
    c.arrow((44, 37), (54, 40.5), both=True, lw=1.0)
    c.arrow((54, 38.6), (43, 27.2), label="published plan", fs=6.3, lpos=0.5, loff=(-1, -3))
    c.arrow((54, 20.6), (43.4, 14), label="marks", fs=6.3, lpos=0.5, loff=(1.5, 2.4))
    c.arrow((54, 6.5), (43.5, 10.4), label="events", fs=6.3, lpos=0.5, loff=(0, -2.4))
    # candidate and seat lookup
    c.box(86, 40, 15, 8, "Candidate", fc=AMBER_L, bold=True, fs=8)
    _proc(c, 91, 58, "6  Seat lookup", fc=AMBER_L, w=16, h=8)
    c.arrow((78, 42), (85, 54.6), label="published seats", fs=6.3, lpos=0.4, loff=(-4.8, 0.5))
    c.arrow((96, 48), (95, 54.2), label="candidate\nID", fs=6.3, loff=(4.5, 0))
    c.arrow((88.5, 54.2), (90, 48), ls="--", label="seat,\nQR slip", fs=6.3, loff=(-4.5, 0))
    # invigilator and attendance
    c.box(86, 3, 15, 8, "Invigilator", fc=GREEN_L, bold=True, fs=8)
    _proc(c, 91, 27, "7  Hall\nattendance", fc=GREEN_L, w=16, h=9)
    c.arrow((78, 40), (84.5, 30.6), label="seat lists", fs=6.3, lpos=0.5, loff=(-3.8, 0))
    c.arrow((83.2, 24.6), (78, 21.6), both=True)
    c.arrow((96, 11), (94.5, 22.5), label="scan, tap,\nsubmit", fs=6.3, loff=(4.4, 0))
    c.arrow((88, 22.7), (90, 11), ls="--", label="seat map,\ncounts", fs=6.3, loff=(-4.8, 0))
    c.text(52, 0.9, "Level 1 data-flow diagram. Processes 2 to 7 append their events to the audit trail D5.", fs=7.2, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(10.4, 6.0)
    c.box(1, 40, 14, 9, "Exam\ncontroller", fc=BLUE_L, bold=True, fs=8)
    c.box(3, 24.5, 14, 6.5, "D2  Reference\ndata", fc=STORE, fs=7.3, r=0.8)
    c.box(87, 3.5, 14, 9, "D3  Plans\nD5  Audit", fc=STORE, bold=True, fs=8, r=0.8)
    row1 = [("3.1  Load sitting\ndata", 31), ("3.2  Pre-check\ncapacity", 54), ("3.3  Stage A\nhall + class\nallocation", 77)]
    row2 = [("3.4  Split candidates\nby hall (seeded)", 77), ("3.5  Stage B\nseat layout per\nhall (parallel)", 54), ("3.6  Validate\nand score", 31)]
    for t, x in row1:
        _proc(c, x, 44.5, t, w=19, h=12, fs=7.2)
    for t, x in row2:
        _proc(c, x, 22, t, w=19, h=12, fs=7.2)
    c.arrow((15, 46), (21.6, 46), label="rules,\nhalls, seed", fs=6.2, loff=(0, -4.6))
    c.arrow((17, 29), (27.5, 39), lw=1.0)
    c.arrow((40.5, 44.5), (44.5, 44.5))
    c.arrow((63.5, 44.5), (67.5, 44.5), label="ok", fs=6.5, loff=(0, 2))
    c.arrow((77, 38.5), (77, 28), label="counts per hall,\ncolour class per paper", fs=6.3, loff=(11.5, 0))
    c.arrow((67.5, 22), (63.5, 22), label="candidates\nper hall", fs=6.3, loff=(0, 4.2))
    c.arrow((44.5, 22), (40.5, 22), label="placements", fs=6.3, loff=(0, 2.4))
    c.box(44, 4.2, 26, 5.8, "3.7  Store plan (version, seed,\nrules, three SHA-256 fingerprints)", fc=INDIGO_L, ec=INDIGO, fs=6.8, r=2.5)
    c.path([(31, 16), (31, 7.1), (44, 7.1)], label="scorecard,\nbaseline", fs=6.3, loff=(-6.5, 0), seg=0)
    c.arrow((70, 7.1), (87, 7.6), label="plan, seats,\naudit event", fs=6.3, loff=(0, 4.2))
    c.path([(54, 50.5), (54, 56), (8, 56), (8, 49.2)], label="impossible: plain-language reasons and a suggestion", fs=6.5, loff=(0, 1.6), seg=1, ls="--")
    c.arrow((57, 28), (70, 38.6), ls="--", label="a hall failed:\nre-balance, retry\n(max 5)", fs=6.2, lpos=0.55, loff=(-10.5, 0))
    c.text(52, 1.5, "Level 2 expansion of process 3 (Generate seating plan).", fs=7.2, italic=True)
    c.save(out)
