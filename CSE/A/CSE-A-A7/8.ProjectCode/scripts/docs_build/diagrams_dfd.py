"""ATHENA data flow diagrams, levels 0, 1 and 2 (03_dfd_level0.png, 04_dfd_level1.png, 05_dfd_level2.png).

Level 1 mirrors backend/app/routes/api.py; level 2 expands the report-reading process of backend/app/services/extract.py.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


class Node:
    """A drawn element with a centre and a size, used to trim arrows to its outline."""

    def __init__(self, kind, x, y, w, h=None):
        self.kind, self.x, self.y, self.w, self.h = kind, x, y, w, h if h is not None else w

    def shifted(self, dx, dy):
        return Node(self.kind, self.x + dx, self.y + dy, self.w, self.h)

    def edge(self, tx, ty):
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy) or 1
        if self.kind == "c":
            return self.x + dx / d * self.w, self.y + dy / d * self.w
        hw, hh = self.w / 2, self.h / 2
        s = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
        return self.x + dx * s, self.y + dy * s


def flow(ax, a, b, label=None, rad=0.0, lo=(0, 1.1), fs=6.6, color=GREY, ls="-", off=0.0):
    """One arrow from node a to node b, trimmed at both outlines; off shifts it sideways (parallel arrows)."""
    dx, dy = b.x - a.x, b.y - a.y
    d = math.hypot(dx, dy) or 1
    nx, ny = -dy / d * off, dx / d * off
    a2, b2 = a.shifted(nx, ny), b.shifted(nx, ny)
    p1 = a2.edge(b2.x, b2.y)
    p2 = b2.edge(a2.x, a2.y)
    arrow(ax, p1, p2, label, color=color, rad=rad, lo=lo, fs=fs, lw=1.2, ls=ls)


def pair(ax, a, b, ab, ba, off=1.9, lab=3.3, fs=6.5, ab_pos=0.5, ba_pos=0.5):
    """Two parallel arrows a->b (navy) and b->a (teal); labels sit on opposite sides at chosen fractions of the way from a to b."""
    dx, dy = b.x - a.x, b.y - a.y
    d = math.hypot(dx, dy) or 1
    nx, ny = -dy / d, dx / d
    flow(ax, a, b, None, color=NAVY, off=off)
    flow(ax, b, a, None, color=TEAL, off=off)
    sgn = 1 if ny >= 0 else -1
    ax.text(a.x + dx * ab_pos + nx * (off + lab) * sgn, a.y + dy * ab_pos + ny * (off + lab) * sgn, ab, ha="center", va="center",
            fontsize=fs, color=NAVY, zorder=6, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
    ax.text(a.x + dx * ba_pos - nx * (off + lab) * sgn, a.y + dy * ba_pos - ny * (off + lab) * sgn, ba, ha="center", va="center",
            fontsize=fs, color=TEAL, zorder=6, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def entity(ax, x, y, w, h, text, ec=NAVY, fs=7.6):
    box(ax, x, y, w, h, text, WHITE, tc=INK, ec=ec, fs=fs, r=0.3)
    return Node("r", x, y, w, h)


def dfd_level0():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(50, 63, "DFD level 0 - context diagram", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    sysn = Node("c", 50, 33, 11.5)
    circle(ax, 50, 33, 11.5, "0\nATHENA\ntriage\nsystem", BLUE, fs=9.5)
    nurse = entity(ax, 12, 49, 18, 9, "Triage nurse /\nclinician")
    admin = entity(ax, 12, 17, 18, 9, "Administrator")
    dev = entity(ax, 88, 17, 18, 9, "Developer\n(offline)")
    lib = entity(ax, 88, 49, 18, 9, "Sample report\nlibrary", ec=TEAL)
    pair(ax, nurse, sysn, "sign-in, report file, vitals,\naccept / change + reason", "findings with pages, priority +\nreasons, queue, summary PDF", lab=4.2, ab_pos=0.42, ba_pos=0.55)
    pair(ax, admin, sysn, "sign-in,\nview performance", "model metrics,\nlive counts", lab=3.6)
    pair(ax, dev, sysn, "synthetic data set,\nretrain command", "model file,\nmetrics.json", lab=3.6)
    flow(ax, lib, sysn, "sample PDFs and\nscans (12 files)", lo=(3, 3.2), color=NAVY)
    save(fig, OUT / "03_dfd_level0.png")


def dfd_level1():
    fig, ax = canvas(10, 9.0, 100, 90)
    ax.text(2, 87, "DFD level 1 - seven processes, six data stores", ha="left", fontsize=10, color=NAVY, fontweight="bold")
    R = 6.3
    P = {}
    spec = {"1": (31, 76, "1.0\nAuthenticate"), "2": (31, 60, "2.0\nRead report"), "3": (31, 44, "3.0\nAssess\npriority"),
            "4": (31, 28, "4.0\nStore and\nqueue"), "5": (31, 12, "5.0\nRecord\ndecision"),
            "6": (85, 74, "6.0\nReport\nmetrics"), "7": (85, 28, "7.0\nBuild\nsummary")}
    for k, (x, y, t) in spec.items():
        P[k] = Node("c", x, y, R)
        circle(ax, x, y, R, t, BLUE, fs=7.0)
    S = {}
    sspec = {"D1": (60, 76, "D1 users"), "D6": (60, 60, "D6 sample reports"), "D4": (60, 44, "D4 model file"),
             "D2": (60, 28, "D2 patients"), "D3": (60, 12, "D3 overrides"), "D5": (85, 55, "D5 metrics files")}
    for k, (x, y, t) in sspec.items():
        S[k] = Node("r", x, y, 17, 5.6)
        store(ax, x, y, 17, 5.6, t, fs=6.8)
    ca = entity(ax, 9, 68, 14, 8, "Triage nurse /\nclinician", fs=6.8)
    cb = entity(ax, 9, 20, 14, 8, "Triage nurse /\nclinician", fs=6.8)
    adm = entity(ax, 70, 85, 14, 5.4, "Administrator", fs=6.6)
    f = lambda a, b, t=None, **k: flow(ax, a, b, t, **k)
    pair(ax, ca, P["1"], "credentials", "token", lab=2.4, fs=6.3, ab_pos=0.3, ba_pos=0.7)
    f(S["D1"], P["1"], "user record", lo=(0, 1.3))
    pair(ax, ca, P["2"], "report file", "findings, pages", lab=2.4, fs=6.3, ab_pos=0.7, ba_pos=0.3)
    f(S["D6"], P["2"], "sample report", lo=(0, 1.3))
    f(ca, P["3"], "vitals", lo=(-3.2, 0.5))
    f(P["2"], P["3"], "report flags", lo=(5.6, 0))
    f(S["D4"], P["3"], "model bundle", lo=(0, 1.3))
    f(P["3"], P["4"], "priority, risk,\nSHAP, fused", lo=(7.4, 0))
    f(P["4"], S["D2"], "patient record", lo=(0, 1.3))
    f(P["4"], cb, "queue, result", lo=(0, 2.0), color=TEAL)
    pair(ax, cb, P["5"], "accept / change\n+ reason", "updated patient", lab=3.0, fs=6.3)
    f(P["5"], S["D3"], "override entry", lo=(0, 1.3))
    f(P["5"], S["D2"], "new priority", lo=(2.8, -2.2))
    f(S["D5"], P["6"], "evaluation\nfiles", lo=(5.4, 0))
    f(S["D2"], P["6"], "live counts", lo=(-3.8, 1.0))
    pair(ax, adm, P["6"], "view request", "metrics", lab=2.6, fs=6.3, ab_pos=0.4, ba_pos=0.6)
    f(S["D2"], P["7"], "patient record", lo=(0, 1.3))
    # summary PDF back to the clinician along the bottom edge
    ax.plot([85, 85, 9], [21.6, 3.2, 3.2], color=TEAL, lw=1.2, zorder=4)
    arrow(ax, (9, 3.2), (9, 15.8), color=TEAL, lw=1.2)
    ax.text(47, 4.9, "summary PDF (on request)", ha="center", fontsize=6.5, color=TEAL,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
    save(fig, OUT / "04_dfd_level1.png")


def dfd_level2():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(50, 63, "DFD level 2 - process 2.0 Read report expanded (services/extract.py)", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    R = 6.2
    spec = {"1": (24, 33, "2.1\nDetect\nfile type"), "2": (42, 51, "2.2\nRead PDF\ntext layer"), "3": (42, 15, "2.3\nOCR the\nimage"),
            "4": (58, 33, "2.4\nUnwrap and\nsplit"), "5": (74, 51, "2.5\nMatch terms\n+ negation"), "6": (74, 15, "2.6\nParse lab\nvalues"),
            "7": (91, 33, "2.7\nAssemble\nresult")}
    P = {}
    for k, (x, y, t) in spec.items():
        P[k] = Node("c", x, y, R)
        circle(ax, x, y, R, t, BLUE, fs=6.4)
    src = entity(ax, 7, 33, 12, 9, "1.0 /\nclinician:\nuploaded file", fs=6.4)
    lex = Node("r", 74, 33, 17, 8.4)
    store(ax, 74, 33, 17, 8.4, "lexicon: 22 terms,\nnegation words,\n6 lab ranges (code)", fs=6.0)
    out = entity(ax, 91, 8, 13, 8, "to 3.0 and\nthe clinician", ec=TEAL, fs=6.4)
    f = lambda a, b, t=None, **k: flow(ax, a, b, t, **k)
    f(src, P["1"], "bytes + name", lo=(1.0, 2.4))
    f(P["1"], P["2"], "PDF", lo=(-3.5, 1.2))
    f(P["1"], P["3"], "image", lo=(-3.5, -1.2))
    f(P["2"], P["3"], "page with no\ntext layer", lo=(-7.4, 0))
    f(P["2"], P["4"], "page text", lo=(3.5, 2.3))
    f(P["3"], P["4"], "OCR text", lo=(3.5, -2.3))
    f(P["4"], P["5"], "sentences", lo=(-2.2, 2.6))
    f(P["4"], P["6"], "sentences", lo=(-2.2, -2.6))
    f(lex, P["5"])
    f(lex, P["6"])
    f(P["5"], P["7"], "items + pages", lo=(3.0, 3.3))
    f(P["6"], P["7"], "labs + flags", lo=(3.0, -3.3))
    f(P["7"], out, None, color=TEAL)
    ax.text(92.4, 21.5, "flags,\nitems,\ntext", ha="left", va="center", fontsize=6.3, color=TEAL)
    save(fig, OUT / "05_dfd_level2.png")


def main():
    dfd_level0()
    dfd_level1()
    dfd_level2()


if __name__ == "__main__":
    main()
