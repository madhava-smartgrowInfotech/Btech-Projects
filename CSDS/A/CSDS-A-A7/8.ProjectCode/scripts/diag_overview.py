"""System architecture, high-level workflow and DFD level 0 for SHEGUARD (drawn from the real routers, services and screens)."""
from __future__ import annotations

import math

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 8.4)
    # ---------------------------------------------------------------- browser
    c.zone(1, 63, 79, 19, "Browser  (React 19 + TypeScript + Vite PWA, port 5107; proxy /api, /ws -> 8107)", fc="#eef4fe")
    fe = [("React SPA\n9 screens + public\n/track/{token} page", 2.5), ("Leaflet map\nOSM tiles, route lines,\nrisk circles, live path", 18.2),
          ("Web Speech API\nSafePhrase matcher\n(lib/safephrase.ts)", 33.9), ("Geolocation, camera /\nfile input, MediaRecorder,\nBattery API", 49.6),
          ("localStorage\ntoken, SafePhrases,\nactive session, log", 65.3)]
    for t, x in fe:
        c.box(x, 64.6, 14.2, 10.6, t, fc="white", fs=6.2)
    # ---------------------------------------------------------------- backend
    c.zone(1, 20, 79, 38.5, "Backend - FastAPI 0.115 + Python 3.11  (port 8107)", fc="#eef8f2")
    c.box(3, 47.4, 75, 6.2, "REST routers /api:  auth - guardians - risk - routes - places - sos - evidence - track - ai          WebSocket /ws/track/{share_token}",
          fc=INDIGO_L, ec=INDIGO, fs=6.7, bold=True)
    svc = [("Security (auth.py)\nJWT HS256, bcrypt,\nget_current_user", 3.0), ("Risk scorer\nhaversine, tier weights\n1 / 2.5 / 5, night x1.6", 15.2),
           ("OSRM client\nroute alternatives,\n15 s timeout", 27.4), ("Gemini client\nsafety system prompt,\n20 s timeout", 39.6),
           ("Alerts\ntelegram.py, email.py\n(not configured here)", 51.8), ("Evidence + live push\nSHA-256 (hashing.py),\nws_manager broadcast", 64.0)]
    for t, x in svc:
        fc = ROSE_L if "not configured" in t else "white"
        c.box(x, 32.5, 11.8, 11.8, t, fc=fc, ec="#c98a8a" if fc == ROSE_L else "#1b2238", fs=5.9)
        c.arrow((x + 5.9, 47.4), (x + 5.9, 44.3))
    c.box(3, 22, 75, 7.6, "SQLAlchemy 2 ORM (6 models) - Pydantic schemas - CORS allow-all - StaticFiles /evidence-files - district table seeded at start-up",
          fc=AMBER_L, ec="#c9a45a", fs=6.4)
    for x in (9, 21, 33, 45, 57, 70):
        c.arrow((x, 32.5), (x, 29.6), ls=":")
    c.arrow((40.5, 63), (40.5, 53.6), both=True)
    c.text(42.5, 60.2, "HTTP / JSON (Bearer JWT) and WebSocket", fs=6.4, italic=True, ha="left")
    # ---------------------------------------------------------------- storage
    c.zone(1, 1, 79, 16.5, "Storage  (backend runs on one machine; no separate database server)", fc="#fff8e8")
    c.box(3, 2.4, 28, 10.6, "SQLite  data/app.db\nusers, guardians, emergency_sessions,\nlocation_pings, evidence, district_risk", fc="white", fs=6.2)
    c.box(33, 2.4, 25, 10.6, "Model and data files\nmodels/risk_model.joblib\ndata/district_risk.csv (467 rows)\ndata/districts_geocoded.csv", fc="white", fs=6.0)
    c.box(60, 2.4, 18, 10.6, "data/evidence/\n{session}/{sha16}.ext\n(photo, audio files)", fc="white", fs=6.2)
    c.arrow((17, 22), (17, 17.5), both=True)
    c.arrow((45, 22), (45, 17.5))
    c.arrow((69, 22), (69, 17.5), both=True)
    # ---------------------------------------------------------------- external services
    c.zone(83, 1, 20.5, 81, "External services", fc="#f6f6f9")
    ex = [("OpenStreetMap\ntile server\n(map images)", 67, "white"), ("Nominatim\nplace search; one-off\ndistrict geocoding", 55, "white"),
          ("OSRM public demo\ndriving route\nalternatives", 43, "white"), ("Gemini API\ngenerateContent\n(AI assistant)", 31, "white"),
          ("Telegram Bot API\nNOT configured\nin this run", 19, ROSE_L), ("Gmail SMTP\nNOT configured\nin this run", 7, ROSE_L)]
    for t, y, fc in ex:
        c.box(85, y, 16.5, 9.6, t, fc=fc, ec="#c98a8a" if fc == ROSE_L else "#1b2238", fs=6.1)
    c.arrow((79.2, 72), (85, 72), label="tiles", fs=5.8, loff=(0, 1.8))
    c.arrow((78, 50.5), (85, 60), ls="--")
    c.text(81.6, 57.4, "places", fs=5.6, rot=60)
    c.arrow((78, 41), (85, 48), ls="--")
    c.arrow((78, 38), (85, 36), ls="--")
    c.arrow((78, 35), (85, 24), ls="--")
    c.arrow((78, 34), (85, 12), ls="--")
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 5.8)
    steps = [("1  Register / log in", "name, email, password;\nbcrypt hash; JWT\n(7-day expiry)", BLUE_L),
             ("2  Add guardians", "name, phone, email,\nTelegram chat id;\nowner-scoped CRUD", BLUE_L),
             ("3  Plan a safe route", "Nominatim search -> OSRM\nalternatives -> district\nrisk score; safest first", INDIGO_L),
             ("4  SafePhrase listening", "Web Speech API, word-\nwindow matcher; phrases\nkept in the browser", INDIGO_L),
             ("5  Trigger SOS", "one tap, or phrase\nmatched; POST\n/api/sos/start", ROSE_L)]
    steps2 = [("6  Alert + share link", "Telegram / Gmail,\nbest effort; unguessable\ntracking URL", AMBER_L),
              ("7  Live tracking", "position every ~4 s;\nWebSocket push to the\nguardian's map", AMBER_L),
              ("8  Evidence", "photo or audio, time,\nlocation, SHA-256\nhash stored", AMBER_L),
              ("9  Cancel", "hold 3 seconds; status\ncancelled; guardians\nsee 'ended'", GREEN_L),
              ("AI Guardian", "ask Gemini a safety\nquestion; available\nat any time", GREY_L)]
    bw, bh, gap = 16.6, 14, 3.9
    xs = [3 + i * (bw + gap) for i in range(5)]
    row1 = [c.box(x, 33, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, steps)]
    row2 = [c.box(x, 10, bw, bh, "", fc=f, ls="-" if i < 4 else "--") for i, (x, (_, _, f)) in enumerate(zip(xs, steps2))]
    for b, (h, t, _) in zip(row1 + row2, steps + steps2):
        c.text(b["x"] + bw / 2, b["y"] + bh - 3.0, h, fs=7.8, bold=True)
        c.text(b["x"] + bw / 2, b["y"] + 5.4, t, fs=6.3)
    for r, n in ((row1, 4), (row2, 3)):
        for a, b in zip(r[:n], r[1:n + 1]):
            c.arrow(anchor(a, "r"), anchor(b, "l"))
    last, first = anchor(row1[-1], "b"), anchor(row2[0], "t")
    c.path([last, (last[0], 28.5), (first[0], 28.5), first])
    c.box(3, 51, 97.6, 4.6, "Steps 1-4 prepare; step 5 starts an emergency session; steps 6-9 run while it is active. Every API call after step 1 carries the JWT; guardians never log in - they open the tracking link.",
          fc=AMBER_L, ec="#c9a45a", fs=6.5, r=1.5)
    c.box(3, 2.2, 97.6, 4.6, "In this run the Telegram and Gmail channels were not configured (alerts report 'not sent') and the Gemini key had exhausted its quota; the tracking link and the in-app status still work.",
          fc=GREY_L, ec="#9aa5ba", fs=6.5, r=1.5)
    c.save(out)


CX, CY, A, B = 52, 34, 15, 19


def edge_pt(px, py):
    dx, dy = px - CX, py - CY
    t = 1.0 / math.sqrt((dx / A) ** 2 + (dy / B) ** 2)
    return (CX + dx * t, CY + dy * t)


def dfd0(out):
    c = Canvas(10.4, 6.6)
    c.ellipse(CX, CY, 2 * A, 2 * B, "0\nSHEGUARD\nroutes, SOS, live\ntracking, evidence,\nAI assistant", fc=INDIGO_L, ec=INDIGO, fs=8.2)
    c.box(1, 46, 17, 11, "User", fc=BLUE_L, fs=8.5, bold=True)
    c.box(86, 46, 17, 11, "Guardian\n(viewer, no account)", fc=BLUE_L, fs=7.6, bold=True)
    c.box(1, 11, 17, 11, "OSRM +\nNominatim", fc=GREY_L, fs=8, bold=True)
    c.box(86, 11, 17, 11, "Gemini API", fc=GREY_L, fs=8, bold=True)
    c.box(36, 1.2, 32, 6.4, "Telegram Bot API + Gmail SMTP\n(not configured in this run)", fc=ROSE_L, ec="#c98a8a", fs=7.0, bold=True)

    # user (left): in solid, out dashed
    c.arrow((18, 53), edge_pt(36, 53), label="register / login, guardians, destination,\nSafePhrase SOS, location, photo / audio, question", fs=6.0, loff=(-1, 3.4))
    c.arrow(edge_pt(36, 48), (18, 48), ls="--", label="JWT, risk areas, ranked routes, tracking\nlink, evidence hashes, assistant answer", fs=6.0, loff=(-1, -3.8))
    # guardian (right)
    c.arrow((86, 53), edge_pt(68, 53), label="open tracking link\n(share token)", fs=6.0, loff=(2, 3.0))
    c.arrow(edge_pt(68, 48), (86, 48), ls="--", label="read-only page: path,\nstatus, live pushes", fs=6.0, loff=(0, -3.2))
    # OSRM + Nominatim (bottom left): alternatives in (solid), request out (dashed)
    c.arrow((18, 18), edge_pt(36, 18), label="route alternatives,\nplace matches", fs=6.0, loff=(0, 3.0))
    c.arrow(edge_pt(36, 13), (18, 13), ls="--", label="route request (coordinates),\nplace query", fs=6.0, loff=(0, -3.2))
    # Gemini (bottom right)
    c.arrow((86, 18), edge_pt(68, 18), label="answer text", fs=6.0, loff=(0, 2.6))
    c.arrow(edge_pt(68, 13), (86, 13), ls="--", label="question + location", fs=6.0, loff=(0, -2.6))
    c.arrow((52, CY - B + 0.2), (52, 7.6), ls="--")
    c.text(53.5, 11.0, "alert text with\ntracking link", fs=6.2, ha="left")
    c.text(52, 63.3, "Context diagram (level 0).  Solid arrows: data in.  Dashed arrows: data out.", fs=7.0, italic=True)
    c.save(out)
