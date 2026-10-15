"""Use-case diagram, sequence diagram (generate -> publish -> look up) and the engine flowchart."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, ROSE_L, Canvas, anchor


# ------------------------------------------------------------------ use cases
def _actor(c, x, y, label):
    c.ax.add_patch(__import__("matplotlib.patches", fromlist=["Circle"]).Circle((x, y + 6.2), 1.6, fc="white", ec=INK, lw=1.3))
    c.line((x, y + 4.6), (x, y + 0.4), lw=1.3)
    c.line((x - 2.4, y + 3.2), (x + 2.4, y + 3.2), lw=1.3)
    c.line((x, y + 0.4), (x - 2.0, y - 2.6), lw=1.3)
    c.line((x, y + 0.4), (x + 2.0, y - 2.6), lw=1.3)
    c.text(x, y - 5.0, label, fs=7.8, bold=True)
    return (x, y + 3.2)


def usecase(out):
    c = Canvas(9.6, 9.4)
    c.rect(16, 2, 66, 90, fc="#fbfbfe", ec=INDIGO, lw=1.4)
    c.text(49, 89.6, "SeatWise", fs=10, bold=True, color=INDIGO)
    admin_cases = ["Import and validate\ncourses, halls, candidates,\ntimetable", "Set default seating\nrules", "Generate a seating plan\n(seeded, constraint-optimised)",
                   "Verify a plan\n(re-run with stored seed)", "Review and swap seats\n(live rule check)", "Publish a plan",
                   "Download charts, hall lists,\ninvigilator sheets, QR slips", "View analytics and\nengine benchmark", "View the audit trail",
                   "Manage team (approve\nor disable invigilators)"]
    other_cases = ["Request an account", "View my halls", "Mark attendance\n(tap or scan a slip)", "Submit and lock\nthe register", "Print a hall chart\nor invigilator sheet",
                   "Look up my seat", "Download my QR seat slip"]
    ys_a = [82 - i * 8.0 for i in range(len(admin_cases))]
    pts = {}
    for t, y in zip(admin_cases, ys_a):
        c.ellipse(34, y, 28, 6.8, t, fc=BLUE_L, ec=INDIGO, fs=6.3)
        pts[t] = (20, y)
    signin_y = 82
    c.ellipse(66, signin_y, 24, 5.6, "Sign in", fc=INDIGO_L, ec=INDIGO, fs=7)
    ys_o = [72 - i * 8.2 for i in range(len(other_cases))]
    for t, y in zip(other_cases, ys_o):
        fc = AMBER_L if "seat" in t.lower() and ("Look" in t or "QR" in t) else GREEN_L
        c.ellipse(66, y, 24, 6.6, t, fc=fc, ec=INDIGO, fs=6.3)
        pts[t] = (54, y)
    admin = _actor(c, 8, 44, "Exam controller\n(administrator)")
    inv = _actor(c, 91, 55, "Invigilator")
    cand = _actor(c, 91, 14, "Candidate")
    for t in admin_cases:
        c.line((admin[0] + 2.8, admin[1]), (20, pts[t][1]), lw=0.8)
    c.line((admin[0] + 2.8, admin[1]), (54, signin_y), lw=0.8)
    for t in other_cases[:5]:
        c.line((inv[0] - 2.8, inv[1]), (78, pts[t][1]), lw=0.8)
    c.line((inv[0] - 2.8, inv[1]), (78, signin_y), lw=0.8)
    for t in other_cases[5:]:
        c.line((cand[0] - 2.8, cand[1]), (78, pts[t][1]), lw=0.8)
    c.text(66, 4.2, "Candidates need no account.", fs=6.6, italic=True)
    c.text(49, 0.8, "Use-case diagram. Administrators can also do everything an invigilator can.", fs=7.0, italic=True)
    c.save(out)


# ------------------------------------------------------------------ sequence diagram
def sequence(out):
    c = Canvas(11.0, 10.4)
    names = ["Administrator", "Web UI\n(React)", "FastAPI\nplans router", "PlanService", "Seating engine\n+ Validator", "SQLite", "Candidate"]
    xs = [7.5, 23, 38.5, 55, 71, 87, 102.5]
    fills = [AMBER_L, BLUE_L, INDIGO_L, INDIGO_L, GREEN_L, "#fff8e8", AMBER_L]
    for n, x, f in zip(names, xs, fills):
        c.box(x - 6.8, 96.5, 13.6, 7, n, fc=f, fs=7.2, bold=True)
        c.ax.plot([x, x], [96.5, 5], color="#8a93a8", lw=0.9, ls=(0, (4, 3)), zorder=0)
    y = 92.0

    def msg(i, j, text, dy=4.4, dashed=False, self_call=False):
        nonlocal y
        if self_call:
            x = xs[i]
            c.line((x, y), (x + 5, y), lw=1.1)
            c.line((x + 5, y), (x + 5, y - 3.2), lw=1.1)
            c.arrow((x + 5, y - 3.2), (x, y - 3.2), lw=1.1)
            c.text(x + 6.5, y - 1.6, text, fs=6.4, ha="left")
            y -= dy + 1.4
            return
        c.arrow((xs[i], y), (xs[j], y), ls="--" if dashed else "-", lw=1.1)
        mid = (xs[i] + xs[j]) / 2
        c.text(mid, y + 1.5, text, fs=6.4)
        y -= dy

    msg(0, 1, "choose sitting, rules, seed - Generate")
    msg(1, 2, "POST /api/sessions/{id}/plans")
    msg(2, 3, "generate(session, rules, halls, seed)")
    msg(3, 5, "load candidates, halls, timetable")
    msg(5, 3, "inputs", dashed=True)
    msg(3, 4, "solve(candidates, halls, rules, seed)")
    msg(4, 4, "pre-check, Stage A, split, Stage B per hall", self_call=True)
    msg(4, 3, "placements (or plain-language reasons)", dashed=True)
    msg(3, 4, "validate(); roll-order baseline")
    msg(4, 3, "scorecard", dashed=True)
    msg(3, 5, "save plan, seats, invigilators, audit(seed, hashes)")
    msg(3, 1, "201 plan + scorecard", dashed=True)
    msg(1, 0, "shows scorecard (0 same-paper pairs)", dashed=True)
    y -= 1.0
    c.ax.plot([2, 108], [y + 2.6, y + 2.6], color="#c3c9d6", lw=0.8)
    msg(0, 1, "Publish")
    msg(1, 2, "POST /api/plans/{id}/publish")
    msg(2, 5, "previous version -> archived; status = published; audit")
    y -= 0.6
    c.ax.plot([2, 108], [y + 2.6, y + 2.6], color="#c3c9d6", lw=0.8)
    msg(6, 1, "enter candidate ID on /lookup")
    msg(1, 2, "GET /api/public/lookup/{id}  (rate-limited)")
    msg(2, 5, "published seats of the candidate")
    msg(5, 6, "hall, seat, hall map (via API and UI)", dashed=True)
    c.text(55, 2.0, "Sequence diagram: generate a plan, publish it, and a candidate finds the seat.", fs=7.0, italic=True)
    c.save(out)
