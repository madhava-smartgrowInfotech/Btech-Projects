"""ER diagram, UML class diagram, use-case diagram, sequence diagram and the core-algorithm flowchart."""
from __future__ import annotations

from matplotlib.patches import Circle

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, ROSE_L, Canvas, anchor

PITCH = 2.5


# ------------------------------------------------------------------ ER
def _table(c, x, y_top, w, name, fields, fc="white", head=INDIGO_L):
    h = 4.8 + PITCH * len(fields) + 0.8
    y = y_top - h
    c.box(x, y, w, h, "", fc=fc, r=1.0, lw=1.1)
    c.box(x, y_top - 4.5, w, 4.5, name, fc=head, ec=INK, bold=True, fs=8, r=1.0, lw=1.1)
    for i, f in enumerate(fields):
        pk = f.startswith("*")
        c.text(x + 1.3, y_top - 4.9 - PITCH * (i + 0.55), f[1:] if pk else f, fs=6.9, ha="left", bold=pk)
    return {"x": x, "y": y, "w": w, "h": h}


def er(out):
    c = Canvas(11.0, 6.4)
    rep = _table(c, 2, 58, 30, "reports", ["*id  INTEGER", "url_norm  TEXT  (index)", "url  TEXT", "verdict  'phishing' | 'safe'", "reporter  TEXT", "source  TEXT", "note  TEXT", "created_at  TEXT"])
    intel = _table(c, 40, 58, 32, "intel", ["*url_norm  TEXT  (primary key)", "url  TEXT", "phishing_votes  INTEGER", "safe_votes  INTEGER",
                                            "status  pending | confirmed_phishing |", "              confirmed_safe", "source  TEXT", "first_seen, last_updated  TEXT", "used_in_training  INTEGER"])
    chk = _table(c, 80, 58, 28, "checks", ["*id  INTEGER", "url  TEXT", "verdict  TEXT", "probability  REAL", "decided_by  ml | community | none", "created_at  TEXT"])
    # relation reports -> intel
    y = rep["y"] + rep["h"] - 12
    c.line((32, y), (40, y), lw=1.2)
    c.text(34, y + 2, "N", fs=8, bold=True)
    c.text(38, y + 2, "1", fs=8, bold=True)
    c.text(36, y - 2.6, "same url_norm\n(logical link,\nno SQL foreign key)", fs=6.2, italic=True)
    c.text(76, 53, "no link: a log of every\ncheck, read by Activity", fs=6.2, italic=True)
    # file stores
    c.zone(2, 2, 105, 20, "File-based stores (not SQL tables)", fc="#fbfbfe")
    c.box(5, 4.5, 30, 12, "data/urls_sample.csv\nurl, label (1 = phishing)\n40,000 rows, balanced", fc="white", fs=7.2)
    c.box(39, 4.5, 32, 12, "models/*.joblib\nrandom_forest, xgboost,\nlogistic_regression, best_model", fc="white", fs=7.2)
    c.box(75, 4.5, 30, 12, "models/metrics.json\nversion, trained_at, per-model\nmetrics, confusion, importances", fc="white", fs=7.2)
    c.text(55, 0.5, "ER diagram: three SQLite tables (threat_intel.db) and the three file stores the pipeline reads and writes.", fs=7.2, italic=True)
    c.save(out)


# ------------------------------------------------------------------ UML
def _cls(c, x, y_top, w, name, attrs, methods, fc="white", stereo=None):
    lh = 2.35
    h = 4.6 + (1.7 if stereo else 0) + lh * (len(attrs) + len(methods)) + 2.4
    y = y_top - h
    c.box(x, y, w, h, "", fc=fc, r=0.8, lw=1.1)
    hh = 4.6 + (1.7 if stereo else 0)
    c.box(x, y_top - hh, w, hh, "", fc=INDIGO_L, r=0.8, lw=1.1)
    if stereo:
        c.text(x + w / 2, y_top - 1.9, f"<<{stereo}>>", fs=6.2, italic=True)
    c.text(x + w / 2, y_top - hh + 2.3, name, fs=8, bold=True)
    yy = y_top - hh - 1.4
    for a in attrs:
        c.text(x + 1.2, yy - lh / 2 + 0.3, a, fs=6.3, ha="left")
        yy -= lh
    c.line((x, yy + 0.4), (x + w, yy + 0.4), lw=0.8)
    yy -= 0.9
    for m in methods:
        c.text(x + 1.2, yy - lh / 2 + 0.6, m, fs=6.3, ha="left")
        yy -= lh
    return {"x": x, "y": y, "w": w, "h": h}


def uml(out):
    c = Canvas(11.6, 10.0)
    ti = _cls(c, 2, 97, 36, "ThreatIntel", ["db_path : str"],
              ["report(url, verdict, reporter, note, source, trusted) : dict", "lookup(url) : dict | None", "lookup_host(url) : dict | None",
               "recent(limit, status) : list", "training_examples(only_new) : list", "mark_trained() : int", "pending_training_count() : int",
               "log_check(url, verdict, probability, decided_by)", "recent_checks(limit) : list", "stats() : dict", "sync_feeds(feeds, limit) : dict",
               "_consensus(p_votes, s_votes, trusted) : str"])
    det = _cls(c, 43, 97, 34, "Detector", ["ti : ThreatIntel", "model, model_name, model_version", "_lock : Lock"],
               ["reload() : bool", "ready : bool", "ml_probability(url) : float", "check(url, log) : dict"])
    feat = _cls(c, 82, 97, 30, "features", ["FEATURE_NAMES : list[47]", "SUSPICIOUS_WORDS, BRAND_NAMES", "SUSPICIOUS_TLDS, POPULAR_DOMAINS"],
                ["normalize_url(url) : str", "extract_features(url) : dict", "features_to_vector(f) : ndarray", "featurize_urls(urls) : ndarray",
                 "explain_features(f) : list[str]", "split_host(host) : tuple"], stereo="module")
    tr = _cls(c, 43, 66, 34, "train", ["HAS_XGB : bool"], ["build_models() : dict", "evaluate(model, X, y) : dict", "feature_importances(model) : list",
                                                        "train_all(X, y, X_te, y_te, meta) : dict", "load_metrics() : dict"], stereo="module")
    rt = _cls(c, 82, 60, 30, "retrain", ["_retrain_lock : Lock"], ["retrain(ti, max_rows) : dict", "maybe_auto_retrain(ti, detector) : bool"], stereo="module")
    dt = _cls(c, 82, 38, 30, "data", [], ["load_dataset(path, max_rows)", "build_matrices(df)", "dataset_summary(df)", "download_full_dataset()"], stereo="module")
    web = _cls(c, 2, 54, 36, "webapp / backend.server", ["app : Flask"],
               ["create_app(ti, detector) : Flask", "build_app(ti, detector) : Flask", "GET /api/check, /api/stats, /api/health ...", "POST /api/report, /api/retrain, /api/sync",
                "pages: /, /report, /community, /models"], stereo="module")
    cfg = _cls(c, 2, 28, 36, "config", ["CONSENSUS_THRESHOLD = 2", "AUTO_RETRAIN_EVERY = 25", "CROWD_SAMPLE_WEIGHT = 3.0", "PHISHING_THRESHOLD = 0.60",
                                        "SUSPICIOUS_THRESHOLD = 0.35", "TEST_SIZE = 0.2, RANDOM_STATE = 42"], [], stereo="module")
    c.arrow((43, 91), (38, 91), label="uses", loff=(0, 1.8))
    c.arrow((77, 91), (82, 91), label="uses", loff=(0, 1.8))
    c.arrow((60, det["y"]), (60, 66), label="load_metrics", loff=(7, 0))
    c.arrow((82, 54), (77, 54), label="train_all", loff=(0, 1.8))
    c.arrow((97, rt["y"]), (97, 38), label="load_dataset", loff=(-8, 0))
    c.arrow((20, 54), (20, ti["y"]), label="owns", loff=(4, 0))
    c.path([(38, 48), (40.5, 48), (40.5, 77), (43, 77)], label="creates", seg=1, loff=(-3, 0))
    c.text(60, 33, "config is read by every module.\nretrain also calls ThreatIntel\n.training_examples() and mark_trained();\nDetector calls log_check().", fs=6.4, italic=True)
    c.text(55, 0.8, "UML class diagram: the modules and classes of phishguard/ and backend/. Python modules are shown as <<module>> classes.", fs=7.2, italic=True)
    c.save(out)


# ------------------------------------------------------------------ use cases
def _actor(c, x, y, label):
    c.ax.add_patch(Circle((x, y + 6.2), 1.6, fc="white", ec=INK, lw=1.3))
    c.line((x, y + 4.6), (x, y + 0.4), lw=1.3)
    c.line((x - 2.4, y + 3.2), (x + 2.4, y + 3.2), lw=1.3)
    c.line((x, y + 0.4), (x - 2.0, y - 2.6), lw=1.3)
    c.line((x, y + 0.4), (x + 2.0, y - 2.6), lw=1.3)
    c.text(x, y - 5.2, label, fs=7.8, bold=True)
    return (x, y + 3.2)


def usecase(out):
    c = Canvas(10.4, 8.4)
    c.rect(17, 2, 66, 80, fc="#fbfbfe", ec=INDIGO, lw=1.4)
    c.text(50, 79.4, "PhishGuard", fs=10, bold=True, color=INDIGO)
    user_cases = ["Check one URL", "Check a batch of URLs\n(file or pasted list)", "View red flags and\nthe reason for a verdict", "View check activity\nand verdict mix"]
    rep_cases = ["Report a URL as\nphishing or safe", "View threat-intelligence\nboard and vote tallies"]
    mnt_cases = ["Compare the three models", "Retrain models with\nconfirmed URLs", "Sync public feeds"]
    ys_u = [71, 62, 53, 44]
    ys_r = [34, 25]
    ys_m = [34, 25, 16]
    for t, y in zip(user_cases, ys_u):
        c.ellipse(36, y, 27, 7.4, t, fc=BLUE_L, ec=INDIGO, fs=6.6)
    for t, y in zip(rep_cases, ys_r):
        c.ellipse(32, y, 24, 7.4, t, fc=AMBER_L, ec=INDIGO, fs=6.6)
    for t, y in zip(mnt_cases, ys_m):
        c.ellipse(67, y, 24, 7.4, t, fc=GREEN_L, ec=INDIGO, fs=6.6)
    c.ellipse(67, 62, 24, 7.4, "Confirm a URL\n(consensus of 2 votes)", fc=ROSE_L, ec=INDIGO, fs=6.6)
    c.ellipse(67, 48, 24, 7.4, "Apply confirmed verdict\nover the model", fc=ROSE_L, ec=INDIGO, fs=6.6)
    user = _actor(c, 8, 50, "Analyst / user")
    rpt = _actor(c, 8, 20, "Community\nreporter")
    mnt = _actor(c, 93, 22, "Maintainer")
    feeds = _actor(c, 93, 58, "Public threat\nfeeds")
    for y in ys_u:
        c.line((user[0] + 2.8, user[1]), (22.5, y), lw=0.8)
    for y in ys_r:
        c.line((rpt[0] + 2.8, rpt[1]), (20, y), lw=0.8)
    for y in ys_m:
        c.line((mnt[0] - 2.8, mnt[1]), (79, y), lw=0.8)
    c.line((feeds[0] - 2.8, feeds[1]), (79, 50), lw=0.8)
    c.line((rpt[0], rpt[1] + 3.3), (user[0], user[1] - 8), lw=0.8, ls=":")
    c.text(11.2, 36, "also a user", fs=6, italic=True, ha="left")
    c.arrow((44, 36), (57, 47), ls="--", lw=0.9)
    c.text(47.5, 44.5, "<<include>>", fs=5.8, italic=True)
    c.arrow((49.5, 69), (55, 67), ls="--", lw=0.9)
    c.text(53, 71.5, "<<include>>", fs=5.8, italic=True)
    c.text(50, 4, "Anyone with access to the web interface can use it: there is no sign-in (see Limitations).", fs=6.6, italic=True)
    c.text(50, 0.7, "Use-case diagram.", fs=7.0, italic=True)
    c.save(out)


# ------------------------------------------------------------------ sequence
def sequence(out):
    c = Canvas(11.0, 12.4)
    names = ["User", "Web UI\n(React)", "Flask API\n(8103)", "Detector", "ThreatIntel\n(SQLite)", "Model /\nRetrain"]
    xs = [8, 28, 48, 67, 86, 103]
    fills = [AMBER_L, BLUE_L, INDIGO_L, INDIGO_L, "#fff8e8", GREEN_L]
    for n, x, f in zip(names, xs, fills):
        c.box(x - 7, 116.5, 14, 7.2, n, fc=f, fs=7.2, bold=True)
        c.ax.plot([x, x], [116.5, 4], color="#8a93a8", lw=0.9, ls=(0, (4, 3)), zorder=0)
    y = 112.0

    def msg(i, j, text, dy=4.2, dashed=False, self_call=False):
        nonlocal y
        if self_call:
            x = xs[i]
            c.line((x, y), (x + 5, y), lw=1.1)
            c.line((x + 5, y), (x + 5, y - 3.2), lw=1.1)
            c.arrow((x + 5, y - 3.2), (x, y - 3.2), lw=1.1)
            c.text(x - 1, y - 1.6, text, fs=6.3, ha="right")
            y -= dy + 1.2
            return
        c.arrow((xs[i], y), (xs[j], y), ls="--" if dashed else "-", lw=1.1)
        c.text((xs[i] + xs[j]) / 2, y + 1.5, text, fs=6.3)
        y -= dy

    def rule(label):
        nonlocal y
        y -= 0.3
        c.ax.plot([2, 108], [y + 2.2, y + 2.2], color="#c3c9d6", lw=0.8)
        c.text(4, y + 3.4, label, fs=6.4, ha="left", bold=True, color=INDIGO)
        y -= 1.2

    rule("A. Check a URL")
    msg(0, 1, "paste URL, press Check")
    msg(1, 2, "GET /api/check?url=...")
    msg(2, 3, "check(url)")
    msg(3, 3, "normalise, extract 47 features", self_call=True)
    msg(3, 4, "lookup(url), lookup_host(url)")
    msg(4, 3, "entry or none", dashed=True)
    msg(3, 5, "predict_proba(features)")
    msg(5, 3, "p", dashed=True)
    msg(3, 3, "alt: confirmed -> community verdict; else p x0.4 / +-0.15, thresholds", self_call=True)
    msg(3, 4, "log_check(url, verdict, p, decided_by)")
    msg(3, 2, "result: verdict, p, red flags, reason", dashed=True)
    msg(2, 1, "200 JSON", dashed=True)
    msg(1, 0, "verdict card, gauge, red flags", dashed=True)
    rule("B. Report a URL")
    msg(0, 1, "Report as phishing / safe")
    msg(1, 2, "POST /api/report")
    msg(2, 4, "report(url, verdict, reporter, note)")
    msg(4, 4, "insert report; update votes; consensus >= 2", self_call=True)
    msg(4, 2, "entry (status)", dashed=True)
    msg(2, 1, "maybe_auto_retrain(): at 25 new confirmations", dashed=True)
    rule("C. Retrain (maintainer or auto)")
    msg(1, 2, "POST /retrain")
    msg(2, 5, "retrain(): base data + confirmed URLs x3")
    msg(5, 5, "fit RF, XGBoost, LR; save; version + 1", self_call=True)
    msg(5, 3, "detector.reload(): hot swap", dashed=True)
    c.text(55, 1.6, "Sequence diagram: check a URL, report it, and refine the model.", fs=7.0, italic=True)
    c.save(out)


# ------------------------------------------------------------------ flowchart
def flowchart(out):
    c = Canvas(9.6, 10.2)
    cx = 38
    c.terminal(cx, 98, 24, 5, "Start: URL submitted")
    c.diamond(cx, 89, 26, 7.5, "URL empty?")
    c.box(66, 86, 28, 6, "Reject: HTTP 400\n'Please enter a URL'", fc=ROSE_L, fs=7)
    c.box(cx - 17, 77, 34, 6, "Normalise: add scheme, lower-case host,\nstrip www., keep port and credentials", fc="white", fs=7)
    c.box(cx - 17, 68, 34, 6, "Extract 47 features (23 lexical, 9 structural,\n15 domain) and the red flags", fc="white", fs=7)
    c.diamond(cx, 58, 32, 8, "Community entry for the URL\nor its host confirmed?")
    c.box(62, 52, 36, 12, "Use the community verdict\nconfirmed phishing -> PHISHING, p = max(0.97, model)\nconfirmed safe -> SAFE, p = min(0.03, model)", fc=ROSE_L, fs=6.6)
    c.box(cx - 17, 44, 34, 5.2, "p = model.predict_proba(features)", fc=INDIGO_L, ec=INDIGO, fs=7.2, bold=True)
    c.diamond(cx, 35, 30, 7.2, "popular domain and\ncommon / long TLD?")
    c.box(66, 32.3, 30, 5.4, "p = p x 0.4   (reputation)", fc=AMBER_L, fs=7)
    c.box(cx - 17, 20.5, 34, 5.2, "pending votes: p = clip(p + 0.15 x (phish - safe), 0, 1)", fc=AMBER_L, fs=6.9)
    c.diamond(cx, 10, 30, 8, "compare p with\n0.60 and 0.35")
    c.box(68, 15, 15, 5, "PHISHING", fc=ROSE_L, fs=7, bold=True)
    c.box(68, 8, 15, 5, "SUSPICIOUS", fc=AMBER_L, fs=6.8, bold=True)
    c.box(68, 1, 15, 5, "SAFE", fc=GREEN_L, fs=7, bold=True)
    c.arrow((cx, 95.5), (cx, 92.75))
    c.arrow((cx, 85.25), (cx, 83), label="no", loff=(2.2, 0))
    c.arrow((cx + 13, 89), (66, 89), label="yes", loff=(0, 1.8))
    c.arrow((cx, 77), (cx, 74))
    c.arrow((cx, 68), (cx, 62))
    c.arrow((cx + 16, 58), (62, 58), label="yes", loff=(0, 1.8))
    c.arrow((cx, 54), (cx, 49.2), label="no", loff=(2.2, 0))
    c.arrow((cx, 44), (cx, 38.6))
    c.arrow((cx + 15, 35), (66, 35), label="yes", loff=(0, 1.8))
    c.path([(81, 32.3), (81, 23.1), (cx + 17, 23.1)])
    c.arrow((cx, 31.4), (cx, 25.7), label="no", loff=(2.2, 0))
    c.arrow((cx, 20.5), (cx, 14))
    c.arrow((cx + 15, 10.8), (68, 17.5), label=">= 0.60", loff=(1, 2.6))
    c.arrow((cx + 15, 10), (68, 10.5), label="0.35 to 0.60", loff=(1, 1.9))
    c.arrow((cx + 15, 9.2), (68, 3.5), label="< 0.35", loff=(1, -2.6))
    c.text(cx, 3.2, "Then: log the check; return verdict,\nprobability, decided_by, reason, red flags.", fs=6.7, italic=True)
    c.save(out)
