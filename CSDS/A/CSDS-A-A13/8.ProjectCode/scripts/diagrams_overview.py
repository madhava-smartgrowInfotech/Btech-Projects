"""System architecture and high-level workflow diagrams."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 7.2)
    c.zone(2, 57, 100, 13, "Users and browsers (PC, tablet, phone)", fc="#f4f5fb")
    users = [("Administrator console\nimport, plan, swap, export,\nanalytics, audit, team", 6),
             ("Invigilator console (tablet)\nmy halls, scan or tap\nattendance, submit register", 37),
             ("Public pages\nhome, \"where do I sit?\",\nQR seat slip", 68)]
    ub = [c.box(x, 58.5, 30, 7, t, fc="white", fs=7.5) for t, x in users]
    c.zone(2, 42, 100, 13, "Frontend - React 18 + TypeScript + Vite   (port 5113)", fc="#eef4fe")
    fe = [c.box(6, 43.5, 30, 7, "Pages and routing\nReact Router, role guards,\nshadcn/ui + Tailwind CSS", fc="white", fs=7.5),
          c.box(37, 43.5, 30, 7, "Seat map and charts\ndnd-kit drag and drop,\nRecharts, Motion", fc="white", fs=7.5),
          c.box(68, 43.5, 30, 7, "Data layer\nTanStack Query + Axios,\nJWT in the Authorization header", fc="white", fs=7.5)]
    for u, f in zip(ub, fe):
        x = anchor(u, "b")[0] + 9
        c.arrow((x, 58.5), (x, 50.5), both=True)
    c.zone(2, 15, 100, 25, "Backend - FastAPI + Python 3.11   (port 8113; Vite proxies /api)", fc="#eef8f2")
    c.box(6, 31.2, 92, 4.4, "REST API:  auth - users - imports - data - plans - exports - attendance - analytics - audit - public - settings   (JWT, roles, rate limit)",
          fc=INDIGO_L, ec=INDIGO, fs=7.6, bold=True)
    c.arrow((92, 43.5), (92, 35.6), label="/api (HTTP, JSON)", both=True, loff=(-9.5, 0))
    svc = ["Importer\nparse, validate,\ncommit", "Seating engine\nOR-Tools CP-SAT\nStage A + Stage B", "Validator\nplain Python,\nno solver", "Swap\nchecker\nsame rules",
           "Exports\nReportLab, openpyxl,\nqrcode", "Attendance\nmark, scan,\nsubmit, lock", "Analytics\nplan + engine\nfigures", "Audit\nappend-only\nevent log"]
    for i, t in enumerate(svc):
        c.box(5 + i * 12, 17.5, 11, 11.5, t, fc="white", fs=6.9)
        c.arrow((10.5 + i * 12, 31.2), (10.5 + i * 12, 29))
    c.zone(2, 1.5, 100, 12, "Storage", fc="#fff8e8")
    c.box(6, 2.8, 68, 7, "SQLite   data/app.db   (SQLAlchemy 2)\n16 tables: users, courses, candidates, halls, exam_sessions, plans,\nseat_assignments, attendance, audit_events, settings ...", fc="white", fs=7.3)
    c.box(77, 2.8, 21, 7, "engine_profile.json\nexperiments/ benchmark\nmetrics and charts", fc="white", fs=7.0)
    for x in (13.5, 25.5, 49.5, 61.5, 73.5):
        c.arrow((x, 17.5), (x, 9.8), both=True)
    c.arrow((82.5, 17.5), (87, 9.8), label="read", loff=(3.5, 0))
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 5.6)
    steps = [("1  Import data", "Excel / CSV: courses,\nhalls, candidates,\ntimetable", BLUE_L),
             ("2  Validate", "row-by-row checks,\nclashes, preview;\nnothing saved yet", BLUE_L),
             ("3  Set rules", "8 / 4 neighbours,\nroll gap, department\nmix, hall usage", INDIGO_L),
             ("4  Generate plan", "CP-SAT engine with a\nrecorded random seed", INDIGO_L),
             ("5  Validate plan", "independent checker,\nscorecard, roll-order\nbaseline", INDIGO_L)]
    steps2 = [("6  Review", "seat map, drag to\nswap, every move\nchecked live", GREEN_L),
              ("7  Publish", "previous version\narchived; seeds and\nhashes stored", GREEN_L),
              ("8  Outputs", "charts, hall lists,\ninvigilator sheets,\nQR seat slips", AMBER_L),
              ("9  On the day", "seat lookup, tablet\nattendance, submit\nand lock register", AMBER_L),
              ("10  Analyse", "analytics, audit trail,\nVerify (re-run with\nthe stored seed)", ROSE_L)]
    bw, bh, gap = 16.6, 14, 3.9
    xs = [3 + i * (bw + gap) for i in range(5)]
    row1 = [c.box(x, 31, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps)]
    row2 = [c.box(x, 8, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps2)]
    for b, (h, t, _) in zip(row1 + row2, steps + steps2):
        c.text(b["x"] + bw / 2, b["y"] + bh - 3.0, h, fs=8.2, bold=True)
        c.text(b["x"] + bw / 2, b["y"] + 5.4, t, fs=6.9)
    for r in (row1, row2):
        for a, b in zip(r[:-1], r[1:]):
            c.arrow(anchor(a, "r"), anchor(b, "l"))
    last, first = anchor(row1[-1], "b"), anchor(row2[0], "t")
    c.path([last, (last[0], 26.5), (first[0], 26.5), first])
    c.box(3, 49, 97.6, 4.6, "Impossible request? The pre-check explains why (not enough seats, too few accessible seats, one paper too large) and suggests a fix.",
          fc=AMBER_L, ec="#c9a45a", fs=7.2, r=1.5)
    c.arrow((xs[3] + bw / 2, 49), (xs[3] + bw / 2, 45), ls=":", head=True)
    c.box(3, 2.2, 97.6, 3.8, "Every step writes to the append-only audit trail: plan seeds, hashes, manual moves, publications, downloads, imports, attendance.",
          fc=GREY_L, ec="#9aa5ba", fs=7.1, r=1.5)
    c.save(out)
