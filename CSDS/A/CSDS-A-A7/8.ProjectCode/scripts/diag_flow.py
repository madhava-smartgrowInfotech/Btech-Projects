"""DFD level 1 and 2 and the core-algorithm flowcharts for SHEGUARD."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def store(c, x, y, w, h, label, fc="#fff8e8", fs=6.2):
    """Open-ended rectangle: a data store (id | name)."""
    c.rect(x, y, w, h, fc=fc, ec="#44506b", lw=1.1)
    c.line((x + 5, y), (x + 5, y + h))
    parts = label.split(" ", 1)
    c.text(x + 2.5, y + h / 2, parts[0], fs=7, bold=True)
    c.text(x + 5 + (w - 5) / 2, y + h / 2, parts[1], fs=fs)


def dfd1(out):
    c = Canvas(10.4, 7.8)
    c.box(3, 68.5, 70, 7, "User (browser): credentials, guardians, destination, location, SafePhrase SOS, photo / audio, question", fc=BLUE_L, fs=6.8, bold=True)
    store(c, 76, 68.5, 26, 7, "D5 browser localStorage", fs=5.8)
    c.text(89, 66.6, "token, SafePhrases, active session", fs=5.6, italic=True)
    xa = [12, 33, 54, 75]
    pa = ["1.0\nAuthenticate and\nmanage guardians", "2.0\nPlan safe route\n(OSRM, Nominatim)", "3.0\nServe risk\nareas", "4.0\nSOS session\n(alerts: Telegram, Gmail)"]
    for x, t in zip(xa, pa):
        c.ellipse(x, 58, 19.6, 11.6, t, fc=INDIGO_L, ec=INDIGO, fs=6.3)
        c.arrow((x, 68.5), (x, 63.8), both=True)
    store(c, 3, 41, 19, 5.6, "D1 users, guardians", fs=5.8)
    store(c, 28, 41, 36, 5.6, "D2 district_risk (467 rows)", fs=5.8)
    store(c, 67, 41, 35, 5.6, "D3 sessions + location pings", fs=5.8)
    c.arrow((12, 52.2), (12, 46.6), both=True, ls=":")
    c.arrow((33, 52.2), (33, 46.6), ls=":")
    c.arrow((54, 52.2), (54, 46.6), ls=":")
    c.arrow((75, 52.2), (75, 46.6), both=True, ls=":")
    xb = [15, 45, 75]
    pb = ["7.0\nAI assistant\n(Gemini)", "6.0\nCapture\nevidence", "5.0\nLive tracking\n(WebSocket)"]
    for x, t in zip(xb, pb):
        c.ellipse(x, 24, 19.6, 11.6, t, fc=INDIGO_L, ec=INDIGO, fs=6.3)
    # request bus on the left for 7.0 and 6.0
    c.line((3, 72), (1.2, 72)); c.line((1.2, 72), (1.2, 34.5)); c.line((1.2, 34.5), (15, 34.5))
    c.arrow((15, 34.5), (15, 29.9), both=True)
    c.line((15, 34.5), (45, 34.5)); c.arrow((45, 34.5), (45, 29.9), both=True)
    c.text(22, 36.2, "requests and responses", fs=5.8, italic=True)
    c.arrow((75, 29.9), (75, 41), ls=":")
    store(c, 33, 3, 24, 5.6, "D4 evidence + files", fs=5.6)
    c.arrow((45, 18.1), (45, 8.6), both=True, ls=":")
    c.box(60, 3, 42, 6.6, "Guardian (viewer, no account): opens /track/{share_token}\nand receives WebSocket pushes", fc=BLUE_L, fs=6.2, bold=True)
    c.arrow((75, 9.6), (75, 18.1), both=True)
    c.text(52, 0.6, "DFD level 1: 7 processes, 5 data stores. 1.0 issues the JWT and the owner is checked in 2.0 and 4.0-7.0; 3.0 is public; 7.0 keeps no store. 5.0 reads D3 written by 4.0.", fs=5.8, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(10.4, 6.8)
    c.box(0.5, 40, 8.5, 12, "User\n(browser)", fc=BLUE_L, fs=7.2, bold=True)
    xs = [21, 39, 57, 75, 93]
    r1, r2 = 46, 23
    row1 = ["2.1\nValidate request\n(origin, destination\ncoordinates, JWT)", "2.2\nFetch alternatives\nfrom OSRM\n(overview = full)", "2.3\nLoad all 467\ndistrict rows\nfrom D2",
            "2.4\nSample every\n8th point of\neach polyline", "2.5\nNearest district\n(haversine over\nall 467)"]
    row2 = ["2.6\nTier weight\n1.0 / 2.5 / 5.0;\nnight x 1.6", "2.7\nMean weight =\nscore (3 dp),\ntier counts", "2.8\nSort ascending;\nfirst = recommended", "2.9\nReturn routes,\nsafest_index = 0"]
    for x, t in zip(xs, row1):
        c.ellipse(x, r1, 16.2, 13.2, t, fc=INDIGO_L, ec=INDIGO, fs=5.9)
    for x, t in zip(xs[::-1][:4], row2):
        c.ellipse(x, r2, 16.2, 13.2, t, fc=INDIGO_L, ec=INDIGO, fs=5.9)
    c.arrow((9, 46), (12.8, 46))
    c.text(5.5, 55.2, "origin, destination\n(lat, lng)", fs=6.0)
    for a, b in zip(xs[:-1], xs[1:]):
        c.arrow((a + 8.1, r1), (b - 8.1, r1))
    c.arrow((93, 39.4), (93, 29.6))
    c.text(98.5, 34.5, "point\nlist", fs=5.8, ha="center")
    r2x = xs[::-1][:4]
    for a, b in zip(r2x[:-1], r2x[1:]):
        c.arrow((a - 8.1, r2), (b + 8.1, r2))
    c.path([(30.9, r2), (4.5, r2), (4.5, 39.8)], ls="--")
    c.text(17, r2 - 2.9, "routes: distance, duration, polyline,\nrisk_score, risk_tiers, is_night, recommended", fs=5.8)
    c.box(66, 58, 36, 7.5, "OSRM failure -> HTTP 502;  no route -> HTTP 404.\nNight = UTC hour >= 15 (about 20:30-05:30 IST)", fc=AMBER_L, ec="#c9a45a", fs=6.0)
    c.arrow((39, 52.8), (80, 58), ls=":")
    c.box(10, 58, 31, 7.5, "OSRM public demo server\n(driving profile, alternatives = true)", fc=GREY_L, ec="#9aa5ba", fs=6.0)
    c.arrow((39, 52.8), (26, 58), both=True, ls=":")
    store(c, 43, 58, 21, 5.6, "D2 district_risk", fs=6.0)
    c.arrow((57, 52.8), (53, 58), ls=":")
    c.text(52, 1.0, "No data is written: route planning only reads D2.  Per route cost about 305 ms of pure-Python distance loops; whole request about 1.6 s with the live OSRM call.", fs=5.9, italic=True)
    c.save(out)


def flowchart(out):
    c = Canvas(10.4, 8.8)
    cx, rx = 24, 75
    c.text(2, 87, "Algorithm 1: score_route()  (POST /api/routes/plan)", fs=7.6, bold=True, ha="left")
    c.text(58, 87, "Algorithm 2: matchSafePhrase()  (lib/safephrase.ts)", fs=7.6, bold=True, ha="left")
    # ---------------- algorithm 1
    c.terminal(cx, 82, 36, 4.4, "Start: OSRM route (list of lat,lng), districts", fs=6.4)
    c.diamond(cx, 74, 30, 7.4, "route has\ncoordinates ?", fs=6.4)
    c.box(cx - 17, 62.5, 34, 5.4, "sampled = coordinates[::8];  night = UTC hour >= 15", fc=BLUE_L, fs=6.2)
    c.box(cx - 17, 53, 34, 5.6, "next sample: nearest district by haversine\n(no distance limit); none -> 'medium'", fc=BLUE_L, fs=6.1)
    c.box(cx - 17, 44.4, 34, 5, "w = weight[tier]  (1.0 / 2.5 / 5.0);\nif night: w x 1.6;  count tier", fc=INDIGO_L, fs=6.2)
    c.diamond(cx, 35, 28, 7.2, "more samples ?", fs=6.4)
    c.box(cx - 17, 23.5, 34, 5.4, "score = total weight / samples (3 dp);\ntiers = counts; night flag", fc=INDIGO_L, fs=6.2)
    c.box(cx - 17, 14.6, 34, 5.4, "plan: sort routes by score ascending;\nfirst route = recommended", fc=GREEN_L, fs=6.2)
    c.terminal(cx, 7, 30, 4.2, "End: routes with risk scores", fc=GREEN_L, fs=6.4)
    c.arrow((cx, 79.8), (cx, 77.7))
    c.arrow((cx, 70.3), (cx, 67.9), label="yes", loff=(2.5, 0), fs=6.0)
    c.arrow((cx, 62.5), (cx, 58.6))
    c.arrow((cx, 53), (cx, 49.4))
    c.arrow((cx, 44.4), (cx, 38.6))
    c.arrow((cx, 31.4), (cx, 28.9), label="no", loff=(2.5, 0), fs=6.0)
    c.arrow((cx, 23.5), (cx, 20))
    c.arrow((cx, 14.6), (cx, 9.1))
    c.path([(cx + 14, 35), (47, 35), (47, 55.8), (cx + 17, 55.8)], label="yes", seg=0, loff=(0, 1.8), fs=6.0)
    c.box(44, 70.5, 13, 6.2, "score 0.0, no tiers\n(empty route)", fc=ROSE_L, ec="#c98a8a", fs=6.0)
    c.arrow((cx + 15, 74), (44, 74), label="no", loff=(0, 1.6), fs=6.0)
    c.text(24, 2.0, "Night x 1.6 multiplies every route equally, so it changes the number, not the order.", fs=5.8, italic=True)
    # ---------------- algorithm 2
    c.terminal(rx, 82, 34, 4.4, "Start: transcript, SafePhrases, sensitivity", fs=6.0)
    c.box(rx - 17, 72.5, 34, 6.2, "spoken = lower-case, keep a-z 0-9 and spaces,\ncollapse blanks;  threshold = 1 / .85 / .75 / .60", fc=BLUE_L, fs=5.8)
    c.diamond(rx, 63.4, 26, 7.4, "spoken empty ?", fs=6.2)
    c.diamond(rx, 51.5, 30, 8.4, "enabled phrase\nstill to check ?", fs=6.2)
    c.diamond(rx, 38.5, 32, 8.4, "spoken contains\nthe whole phrase ?", fs=6.0)
    c.box(rx - 17, 25, 34, 6.4, "slide a window of len(phrase) words;\nbest = max share of phrase words in a window", fc=BLUE_L, fs=5.8)
    c.diamond(rx, 15, 32, 8.4, "best >= threshold and\nbetter than earlier ?", fc=AMBER_L, fs=5.9)
    c.terminal(rx, 4.2, 34, 4.2, "Return best match (or none)", fc=GREEN_L, fs=6.2)
    c.arrow((rx, 79.8), (rx, 78.7))
    c.arrow((rx, 72.5), (rx, 67.1))
    c.arrow((rx, 59.7), (rx, 55.7), label="no", loff=(2.5, 0), fs=6.0)
    c.arrow((rx, 47.3), (rx, 42.7), label="yes", loff=(2.5, 0), fs=6.0)
    c.arrow((rx, 34.3), (rx, 31.4), label="no", loff=(2.5, 0), fs=6.0)
    c.arrow((rx, 25), (rx, 19.2))
    c.arrow((rx, 10.8), (rx, 6.3), label="yes: keep", loff=(5, 0), fs=5.8)
    c.box(92, 59.5, 11.5, 7.5, "return none", fc=ROSE_L, ec="#c98a8a", fs=5.8)
    c.arrow((rx + 13, 63.4), (92, 63.4), label="yes", loff=(0, 1.6), fs=5.8)
    c.box(92, 33, 11.5, 11, "match,\nconfidence 1\n(SOS starts)", fc=GREEN_L, fs=5.6)
    c.arrow((rx + 16, 38.5), (92, 38.5), label="yes", loff=(0, 1.6), fs=5.8)
    c.path([(rx - 15, 51.5), (60, 51.5), (60, 15), (rx - 16, 15)], head=False, ls=":")
    c.text(58.2, 33.5, "loop over phrases", fs=5.6, rot=90)
    c.save(out)
