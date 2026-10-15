"""Architecture, workflow, DFD level 0/1/2 diagrams for PhishGuard (drawn from phishguard/ and backend/)."""
from __future__ import annotations

import math

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 7.4)
    c.zone(2, 61, 100, 11.5, "Users", fc="#f4f5fb")
    users = [("Analyst / end user\ncheck one URL or a batch,\nreport a URL", 5),
             ("Maintainer\nsync public feeds, retrain,\ncompare models", 37.5),
             ("Command line\nrun.py check / report /\ntrain / retrain / sync", 70)]
    for t, x in users:
        c.box(x, 62.2, 29, 7.4, t, fc="white", fs=7.4)
    c.zone(2, 45, 100, 14, "Frontend - React 18 + Vite   (port 5103; proxies /api to 8103)", fc="#eef4fe")
    c.box(5, 46.5, 29, 8, "Seven pages\nLanding, Check URL, Report,\nThreat intelligence, Models,\nActivity, Not found", fc="white", fs=7.1)
    c.box(37.5, 46.5, 29, 8, "Interface components\nrecharts, three.js hero,\nframer-motion, lucide icons", fc="white", fs=7.1)
    c.box(70, 46.5, 29, 8, "API client (fetch)\nJSON over HTTP, error and\n'backend unreachable' states", fc="white", fs=7.1)
    for x in (19.5, 52, 84.5):
        c.arrow((x, 62.2), (x, 54.5), both=True)
    c.zone(2, 17, 100, 26, "Backend - Python 3.11, Flask   (port 8103)   backend/server.py wraps phishguard.webapp", fc="#eef8f2")
    c.box(5, 35, 94, 4.4, "JSON API:  /api/check - /api/report - /api/stats - /api/retrain - /api/sync - /api/health - /api/config - /api/checks - /api/intel - /api/intel/lookup",
          fc=INDIGO_L, ec=INDIGO, fs=7.0, bold=True)
    c.arrow((52, 45), (52, 39.4), label="HTTP + JSON", both=True, loff=(8, 0))
    mods = ["Train\nRF, XGBoost, LR\nevaluate + save", "Features\n47 offline\nlexical, structural,\ndomain features",
            "Detector\ndecision order:\ncommunity, then\nML model", "Retrain\nbase data + confirmed\nURLs (x3 weight)",
            "Original pages\nFlask templates\n/, /report, /community,\n/models", "ThreatIntel\nreports, consensus,\nfeed sync"]
    xs = [5 + i * 15.8 for i in range(6)]
    for t, x in zip(mods, xs):
        c.box(x, 19, 14.6, 13.5, t, fc="white", fs=6.8)
        c.arrow((x + 7.3, 35), (x + 7.3, 32.5))
    c.zone(2, 1.5, 100, 14, "Storage (local files) and external feeds", fc="#fff8e8")
    c.box(4, 3, 23, 8.2, "models/\nbest_model.joblib, three\nmodel files, metrics.json", fc="white", fs=6.9)
    c.box(29, 3, 23, 8.2, "data/urls_sample.csv\n40,000 labelled URLs\n(url, label)", fc="white", fs=6.9)
    c.box(54, 3, 21, 8.2, "Public threat feeds\nOpenPhish, URLhaus\n(optional, internet)", fc=ROSE_L, fs=6.9)
    c.box(77, 3, 23, 8.2, "SQLite\ndata/threat_intel.db\nreports, intel, checks", fc="white", fs=6.9)
    c.arrow((12.3, 19), (12.3, 11.2), both=True)
    c.arrow((60.5, 19), (45, 11.2), label="reads", loff=(-3, 0.5))
    c.arrow((91.5, 19), (91.5, 11.2), both=True)
    c.path([(64.5, 11.2), (64.5, 15.3), (96.5, 15.3), (96.5, 19)], label="trusted reports", seg=1, loff=(-8, 1.6))
    c.text(52, 0.6, "The Detector loads models/best_model.joblib and queries ThreatIntel; Retrain writes new model files.", fs=6.8, italic=True)
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 5.8)
    top = [("1  Collect data", "40,000 labelled URLs\n(20,000 phishing,\n20,000 legitimate)", BLUE_L),
           ("2  Extract features", "47 offline signals:\nlexical, structural,\ndomain", BLUE_L),
           ("3  Train + compare", "Random Forest, XGBoost,\nLogistic Regression,\nsame 80/20 split", INDIGO_L),
           ("4  Select + deploy", "best F1 model saved\nas best_model.joblib,\nloaded by the detector", INDIGO_L)]
    bot = [("5  Check a URL", "community verdict first,\nthen model score,\nthresholds 0.35 / 0.60", GREEN_L),
           ("6  Community reports", "phishing or safe votes;\nnet 2 confirms; trusted\nfeeds confirm at once", AMBER_L),
           ("7  Refine", "retrain on base data +\nconfirmed URLs (x3),\nnew model version", AMBER_L),
           ("8  Hot reload", "detector swaps in the new\nmodel without a\nrestart", ROSE_L)]
    bw, bh, gap = 21, 14, 4.2
    xs = [3 + i * (bw + gap) for i in range(4)]
    r1 = [c.box(x, 32, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, top)]
    r2 = [c.box(x, 10, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, bot)]
    for b, (h, t, _) in zip(r1 + r2, top + bot):
        c.text(b["x"] + bw / 2, b["y"] + bh - 3.0, h, fs=8.6, bold=True)
        c.text(b["x"] + bw / 2, b["y"] + 5.2, t, fs=7.1)
    for r in (r1, r2):
        for a, b in zip(r[:-1], r[1:]):
            c.arrow(anchor(a, "r"), anchor(b, "l"))
    last, first = anchor(r1[-1], "b"), anchor(r2[0], "t")
    c.path([last, (last[0], 28), (first[0], 28), first])
    rb, tb = r2[-1], r1[3]
    c.path([(rb["x"] + rb["w"], rb["y"] + rb["h"] / 2), (102.3, rb["y"] + rb["h"] / 2), (102.3, tb["y"] + tb["h"] / 2),
            (tb["x"] + tb["w"], tb["y"] + tb["h"] / 2)], ls="--")
    c.text(52, 5.0, "Dashed arrow: the refined model serves the next check, so the cycle repeats.", fs=7.2, italic=True)
    c.box(3, 50.5, 97, 4.4, "Offline by design: no DNS, WHOIS or page download, so training and real-time checking run the identical feature code.",
          fc=GREY_L, ec="#9aa5ba", fs=7.2, r=1.5)
    c.save(out)


CX, CY, A, B = 52, 28, 14.5, 19


def _edge_x(y, side):
    dx = A * math.sqrt(max(0.0, 1 - ((y - CY) / B) ** 2))
    return CX - dx if side == "l" else CX + dx


def dfd0(out):
    c = Canvas(10.4, 5.8)
    c.ellipse(CX, CY, 2 * A, 2 * B, "0\nPhishGuard\nphishing URL\ndetection system", fc=INDIGO_L, ec=INDIGO, fs=9.5)
    c.box(1, 36, 17, 10, "Analyst / user", fc=BLUE_L, fs=8.5, bold=True)
    c.box(1, 9, 17, 10, "Maintainer", fc=GREEN_L, fs=8.5, bold=True)
    c.box(86, 36, 17, 10, "Community\nreporter", fc=AMBER_L, fs=8.5, bold=True)
    c.box(86, 9, 17, 10, "Public threat feeds\n(OpenPhish, URLhaus)", fc=ROSE_L, fs=7.8, bold=True)
    y1, y2 = 44, 37.5
    c.arrow((18, y1), (_edge_x(y1, "l"), y1))
    c.text(29, y1 + 4.4, "URL to check (single or batch)", fs=6.7)
    c.arrow((_edge_x(y2, "l"), y2), (18, y2), ls="--")
    c.text(29, y2 - 4.6, "verdict, probability, red flags,\nreason, 47 features, activity", fs=6.7)
    y1, y2 = 17.5, 11
    c.arrow((18, y1), (_edge_x(y1, "l"), y1))
    c.text(29, y1 + 4.0, "retrain / sync commands", fs=6.7)
    c.arrow((_edge_x(y2, "l"), y2), (18, y2), ls="--")
    c.text(29, y2 - 4.4, "model metrics, confusion\nmatrices, retrain status", fs=6.7)
    y1, y2 = 44, 37.5
    c.arrow((86, y1), (_edge_x(y1, "r"), y1))
    c.text(75, y1 + 4.4, "report: URL, phishing / safe,\nreporter, note", fs=6.7)
    c.arrow((_edge_x(y2, "r"), y2), (86, y2), ls="--")
    c.text(75, y2 - 4.4, "vote tally and consensus status", fs=6.7)
    y1 = 17
    c.arrow((86, y1), (_edge_x(y1, "r"), y1))
    c.text(75, y1 + 4.0, "newly listed phishing URLs", fs=6.7)
    c.text(52, 3.2, "Context diagram (level 0). Solid arrows: data in. Dashed arrows: data out.", fs=7.6, italic=True)
    c.save(out)


def _proc(c, cx, cy, num, name, w=17, h=11, fc=INDIGO_L):
    c.ellipse(cx, cy, w, h, f"{num}\n{name}", fc=fc, ec=INDIGO, fs=6.9)
    return {"x": cx - w / 2, "y": cy - h / 2, "w": w, "h": h}


def _store(c, x, y, w, h, tag, label):
    c.box(x, y, w, h, "", fc="#fff8e8", r=0.6, lw=1.0)
    c.line((x + 4.2, y), (x + 4.2, y + h), lw=1.0)
    c.text(x + 2.1, y + h / 2, tag, fs=6.6, bold=True)
    c.text(x + 4.8 + (w - 4.8) / 2, y + h / 2, label, fs=6.4)


def dfd1(out):
    c = Canvas(11.0, 8.0)
    c.box(1, 62, 14, 8, "Analyst / user", fc=BLUE_L, fs=7.4, bold=True)
    c.box(1, 40, 14, 8, "Community\nreporter", fc=AMBER_L, fs=7.4, bold=True)
    c.box(1, 14, 14, 12, "Maintainer", fc=GREEN_L, fs=7.4, bold=True)
    c.box(95, 38, 14, 8, "Public threat\nfeeds", fc=ROSE_L, fs=7.2, bold=True)
    _proc(c, 32, 66, "1.0", "Normalise URL +\nextract features")
    _proc(c, 58, 66, "2.0", "Score with\nML model")
    _proc(c, 84, 66, "3.0", "Decide verdict\n+ explain")
    _proc(c, 32, 44, "4.0", "Record report +\ncompute consensus")
    _proc(c, 84, 44, "5.0", "Sync public feeds\n(maintainer starts)")
    _proc(c, 58, 22, "6.0", "Retrain +\nhot-reload model")
    _proc(c, 32, 10, "7.0", "Present metrics,\nactivity, stats")
    _store(c, 46, 52, 24, 5, "D4", "model files")
    _store(c, 46, 40, 24, 5, "D1", "reports + intel")
    _store(c, 90, 52, 18, 5, "D2", "checks log")
    _store(c, 78, 28, 26, 5, "D3", "dataset CSV")
    _store(c, 78, 14, 26, 5, "D4", "model files")
    _store(c, 78, 4, 26, 5, "D5", "metrics.json")
    c.arrow((15, 66), (23.5, 66), label="URL", loff=(0, 2.2))
    c.arrow((40.5, 66), (49.5, 66), label="47 features", loff=(0, 2.2))
    c.arrow((66.5, 66), (75.5, 66), label="probability", loff=(0, 2.2))
    c.arrow((58, 57), (58, 60.5), ls=":", label="model", loff=(4, 0))
    c.path([(84, 71.5), (84, 78), (8, 78), (8, 70)], label="verdict, probability, red flags, reason", seg=1, ls="--", loff=(0, 1.8))
    c.arrow((90, 60.5), (99, 57), label="log check", loff=(2.5, 3))
    c.arrow((70, 43), (78, 61), ls=":", label="community status", lpos=0.5, loff=(-9, 0))
    c.arrow((15, 44), (23.5, 44), label="report", loff=(0, 2.2))
    c.arrow((23.5, 41), (15, 41), ls="--", label="status", loff=(0, -2.2))
    c.arrow((40.5, 44), (46, 43), label="votes", loff=(0, 2.6))
    c.arrow((97, 42), (92.5, 42), label="URLs", loff=(0, 2.4))
    c.arrow((75.5, 44), (70, 43), label="trusted", loff=(0, 2.6))
    c.arrow((15, 22), (51.5, 23.5), label="retrain", lpos=0.45, loff=(0, 2.4))
    c.arrow((58, 40), (58, 27.5), ls=":", label="confirmed URLs", loff=(-8.5, 0))
    c.arrow((78, 30.5), (65.5, 25), ls=":", label="base data", loff=(4, 3))
    c.arrow((66.5, 21), (78, 17), label="new models", loff=(1, 2.4))
    c.arrow((64, 17), (78, 7.5), label="metrics", loff=(2.5, 1.8))
    c.arrow((78, 6.5), (40.2, 8.5), ls=":", label="metrics", loff=(0, -2.2))
    c.arrow((23.5, 12), (15, 17), ls="--", label="metrics, status", loff=(-3, -3.2))
    c.text(55, 1.0, "DFD level 1: seven processes and five data stores (D4 is drawn twice). Dotted arrows are reads, dashed arrows are data out.", fs=7.0, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(11.0, 7.6)
    c.zone(16, 5, 93, 70, "Processes 1.0, 2.0 and 3.0 expanded: the check path", fc="#fafaff", fs=8.2)
    c.box(1, 50, 12, 10, "Analyst\n/ user", fc=BLUE_L, fs=7.2, bold=True)
    for n, t, x, y in [("1.1", "Normalise\nURL", 30, 56), ("1.2", "Extract 47\nfeatures", 50, 56), ("2.1", "Score with\nbest model", 70, 56),
                       ("3.2", "Adjust: reputation\nx0.4, pending\nvotes +-0.15", 90, 56), ("3.1", "Look up\ncommunity\n(URL, host)", 70, 38),
                       ("3.3", "Apply\nthresholds\n0.35 / 0.60", 90, 14), ("3.4", "Explain\n(red flags,\nreason)", 70, 14), ("3.5", "Log\ncheck", 50, 14)]:
        _proc(c, x, y, n, t, w=16.5, h=14)
    _store(c, 58, 68, 24, 5, "D4", "model files")
    _store(c, 58, 24, 24, 5, "D1", "reports + intel")
    _store(c, 18, 10, 17, 5, "D2", "checks log")
    c.arrow((13, 55), (21.7, 55), label="URL", loff=(0, 2.4))
    c.arrow((38.3, 56), (41.7, 56), label="norm.", loff=(0, 2.8), fs=6.4)
    c.arrow((58.3, 56), (61.7, 56), label="x", loff=(0, 2.8))
    c.arrow((78.3, 56), (81.7, 56), label="p", loff=(0, 2.8))
    c.arrow((70, 68), (70, 63.2), ls=":", label="model", loff=(5, 0))
    c.path([(30, 49), (30, 38), (61.7, 38)], label="normalised URL", seg=1, loff=(0, 1.8))
    c.arrow((78.3, 38), (86, 49.5), ls="--", label="intel", loff=(-1, -3))
    c.arrow((70, 29), (70, 31), ls=":")
    c.arrow((92, 49), (92, 21), label="p'", loff=(2.5, 0))
    c.arrow((81.7, 14), (78.3, 14))
    c.arrow((61.7, 14), (58.3, 14), label="result", loff=(0, 2.8), fs=6.4)
    c.arrow((41.7, 14), (35, 12.5), label="log row", loff=(0, 3))
    c.path([(70, 7), (70, 2.6), (7, 2.6), (7, 50)], label="verdict, probability, red flags, reason", seg=1, ls="--", loff=(0, 1.8))
    c.text(55, 0.6, "DFD level 2: the check path. Red flags in 3.4 are derived from the features produced by 1.2. Dotted arrows are reads.", fs=7.0, italic=True)
    c.save(out)
