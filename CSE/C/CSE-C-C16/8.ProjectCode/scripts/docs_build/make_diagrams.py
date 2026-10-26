"""Draw every design diagram for the AgriVision documents into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: backend/main.py (routes), agrivision/inference.py, agrivision/disease_db.py,
agrivision/app.py (init_db, tables), agrivision/train.py and frontend/src/pages.
    python scripts/docs_build/make_diagrams.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)
GREEN = "#2F8F4E"
PALE_GREEN = "#DFF1E4"


# --------------------------------------------------------------------------------------------------
def system_architecture():
    fig, ax = canvas(10, 8.0, 100, 80)
    panel(ax, 2, 60, 96, 18, "Presentation tier - browser (React 18 + TypeScript + Vite + Tailwind, port 5416)", PALE_BLUE, BLUE, tc=NAVY)
    box(ax, 17, 66.5, 28, 9.5, "12 page components\nLanding - Login - Register - Dashboard\nDetect - Result - History - Analytics\nProfile - Disease guide", BLUE, fs=7.4)
    box(ax, 48, 66.5, 28, 9.5, "Data layer\naxios client on /api\nTanStack Query hooks\nbearer token in localStorage", BLUE, fs=7.6)
    box(ax, 79, 66.5, 28, 9.5, "UI kit (Aurora Glass)\nRecharts charts - GSAP\nlight / dark theme\nEN / HI / MR interface strings", BLUE, fs=7.6)

    panel(ax, 2, 33, 96, 24, "Application tier - FastAPI (backend/main.py, port 8416, all routes under /api)", PALE_GREEN, GREEN, tc=NAVY)
    box(ax, 15, 46.5, 24, 10.5, "Account\nPOST /auth/register\nPOST /auth/login\nGET /auth/me - PUT /profile", GREEN, fs=7.2)
    box(ax, 40.5, 46.5, 24, 10.5, "Diagnosis\nPOST /detect/upload\n(image + crop_type)\nvalidate, predict, store", GREEN, fs=7.2)
    box(ax, 66, 46.5, 24, 10.5, "History and reports\nGET /history, /history/{id}\nDELETE /history/{id}\nexport CSV / PDF", GREEN, fs=7.2)
    box(ax, 90, 46.5, 15, 10.5, "Insight\n/dashboard\n/analytics/\ndashboard", GREEN, fs=7.2)
    box(ax, 28, 36.5, 50, 4.2, "Public: GET /health, /diseases, /diseases/{name}, /uploads/{name}   -   HMAC bearer token (7 days)", WHITE, tc=INK, ec=GREEN, fs=7.2)
    box(ax, 77, 36.5, 38, 4.2, "Error handler: one JSON shape for 400 / 401 / 404 / 409 / 413", WHITE, tc=INK, ec=GREEN, fs=7.2)

    panel(ax, 2, 13, 96, 17, "Domain tier - agrivision/ (original Flask product, imported unchanged by the API)", PALE_ORANGE, ORANGE, tc=NAVY)
    box(ax, 17, 20.5, 26, 9.5, "inference.py\npredict(): colour/texture\nheuristic, or Keras / ONNX\nmodel when one is installed", ORANGE, fs=7.2)
    box(ax, 45, 20.5, 26, 9.5, "disease_db.py\n38 classes, 26 curated cards\ntreatments: chemical, organic,\ncultural + prevention", ORANGE, fs=7.2)
    box(ax, 73, 20.5, 26, 9.5, "app.py / config.py\ninit_db(): tables + demo user\nlimits: 10 MB, jpg/png/webp\n(Flask pages on port 5000)", ORANGE, fs=7.2)
    box(ax, 93.5, 20.5, 9, 9.5, "train.py\noffline\nCNN", WHITE, tc=INK, ec=ORANGE, fs=7.0, ls="--")

    store(ax, 24, 6.0, 40, 6.0, "SQLite agrivision.db: users, results", PALE_TEAL, TEAL, fs=7.8)
    store(ax, 62, 6.0, 30, 6.0, "static/uploads/<uuid>.jpg|png", PALE_TEAL, TEAL, fs=7.8)
    store(ax, 87, 6.0, 20, 6.0, "models/ (empty)\ndatasets/ (PlantDoc)", PALE_TEAL, TEAL, fs=6.8)
    arrow(ax, (45, 60), (45, 57), "HTTP + JSON + multipart (Vite proxies /api)", lo=(26, 0), fs=7.4, color=NAVY)
    arrow(ax, (45, 33), (45, 30), "Python imports", lo=(10, 0), fs=7.4, color=NAVY)
    arrow(ax, (24, 13), (24, 9.0), None, color=NAVY)
    arrow(ax, (62, 13), (62, 9.0), None, color=NAVY)
    arrow(ax, (88, 13), (88, 9.0), None, color=NAVY, ls="--")
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 6.4, 100, 64)
    ax.text(50, 61.5, "A. Diagnosis path (every scan)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    steps = [("Farmer picks a\nleaf photo and\na crop", BLUE), ("Upload checks\nformat, size,\nsign-in", GREEN), ("Decode, resize\nto 256 px,\ncolour features", GREEN),
             ("Candidate\nclasses for\nthe crop", GREEN), ("Score, rank,\ntop-3 + confidence", ORANGE), ("Knowledge card:\nsymptoms, 3\ntreatments", PURPLE), ("Save scan,\nshow result,\nexport", NAVY)]
    xs = [7.5 + i * 14.2 for i in range(7)]
    for x, (t, c) in zip(xs, steps):
        box(ax, x, 49, 12.6, 14, t, c, fs=7.4)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 6.4, 49), (b - 6.4, 49), None, color=NAVY)

    ax.text(50, 33.5, "B. Offline learning path (scripts/run_experiments.py, agrivision/train.py)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    steps2 = [("PlantDoc\nfolders\n(2,342 train)", BLUE), ("Resize 224,\nuint8 cache", GREEN), ("10% stratified\nvalidation\nsplit", GREEN), ("Train compact CNN\nor MobileNetV2\n(3 seeds)", ORANGE),
              ("Evaluate on\n236 test photos", PURPLE), ("Metrics JSON,\nconfusion matrix,\nfigures", NAVY)]
    xs2 = [8.5 + i * 16.6 for i in range(6)]
    for x, (t, c) in zip(xs2, steps2):
        box(ax, x, 21, 14.6, 14, t, c, fs=7.6)
    for a, b in zip(xs2[:-1], xs2[1:]):
        arrow(ax, (a + 7.5, 21), (b - 7.5, 21), None, color=NAVY)
    box(ax, 50, 5.0, 92, 6.2, "The trained network is NOT copied into agrivision/models/, so the web app keeps using the heuristic engine; dropping plantdoc_cnn.h5 + labels.json there switches it on", WHITE, tc=INK, ec=NAVY, fs=7.4)
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    import math
    fig, ax = canvas(10, 5.4, 100, 54)
    circle(ax, 50, 27, 14.5, "0\nAgriVision\ncrop disease\nsystem", GREEN, fs=9.6)
    box(ax, 11, 27, 18, 34, "Farmer /\nuser", NAVY, fs=10, bold=True)
    box(ax, 89, 36, 18, 18, "Model owner\n(offline training)", NAVY, fs=9, bold=True)
    box(ax, 89, 12, 18, 14, "PlantDoc\nphoto dataset", GREY, fs=9, bold=True)

    def edge(y, side):
        dx = math.sqrt(max(14.5 ** 2 - (y - 27) ** 2, 0))
        return 50 - dx if side == "L" else 50 + dx

    def hflow(y, x1, x2, text, color, fwd=True):
        a, b = (x1, x2) if fwd else (x2, x1)
        arrow(ax, (a, y), (b, y), text, color=color, lo=(0, 1.9), fs=7.4)
    hflow(39, 20, edge(39, "L"), "sign-up / sign-in details", BLUE)
    hflow(33, 20, edge(33, "L"), "leaf photo + crop choice", BLUE)
    hflow(21, 20, edge(21, "L"), "diagnosis, top-3, severity,\ntreatments, prevention", GREEN, fwd=False)
    hflow(15, 20, edge(15, "L"), "history, analytics,\nCSV / PDF reports", GREEN, fwd=False)
    hflow(39, edge(39, "R"), 80, "trained weights\n(optional, offline)", ORANGE, fwd=False)
    arrow(ax, (80, 16), (61, 19.2), "labelled leaf photos", color=BLUE, lo=(4.5, -2.4), fs=7.4)
    ax.text(50, 3, "The model owner works outside the web app: scripts/run_experiments.py and agrivision/train.py read the dataset and write metrics and weights.", ha="center", fontsize=6.8, color=GREY)
    save(fig, OUT / "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(10, 8.0, 100, 80)
    box(ax, 9, 40, 14, 68, "Farmer /\nuser", NAVY, fs=10, bold=True)
    ys = {"1": 70, "2": 58, "3": 46, "4": 34, "5": 22, "6": 10}
    names = {"1": "1.0\nAuthenticate\n+ register", "2": "2.0\nManage\nprofile", "3": "3.0\nDiagnose\nleaf photo", "4": "4.0\nBrowse\ndisease guide", "5": "5.0\nHistory, delete\n+ export", "6": "6.0\nDashboard +\nanalytics"}
    for k, y in ys.items():
        circle(ax, 44, y, 5.7, names[k], GREEN, fs=6.0)
    ins = {"1": ("credentials", "token"), "2": ("name, region,\nlanguage, crops", "saved profile"), "3": ("leaf photo + crop", "diagnosis,\ntreatments"), "4": ("browse / search", "disease cards"),
           "5": ("filter, delete,\nexport request", "list, CSV, PDF"), "6": ("open page", "totals, charts")}
    for k, y in ys.items():
        arrow(ax, (16.2, y + 1.6), (38.4, y + 1.6), ins[k][0], color=BLUE, lo=(0, 2.7), fs=6.2)
        arrow(ax, (38.4, y - 1.8), (16.2, y - 1.8), ins[k][1], color=GREEN, lo=(0, -2.9), fs=6.2)
    store(ax, 86, 64, 17, 6, "D1 users", PALE_TEAL, TEAL, fs=8)
    store(ax, 86, 52, 17, 6, "D3 uploads (image files)", PALE_TEAL, TEAL, fs=6.8)
    store(ax, 86, 40, 17, 6, "D4 knowledge base\n(38 cards, in code)", PALE_ORANGE, ORANGE, fs=6.6)
    store(ax, 86, 22, 17, 6, "D2 results (scans)", PALE_TEAL, TEAL, fs=7.4)
    arrow(ax, (49.7, 70), (77.5, 65), "check / create user", color=GREY, ls="--", lo=(1, 3.0), fs=6.2)
    arrow(ax, (49.7, 58), (77.5, 63), "read / update profile", color=GREY, ls="--", lo=(0, -3.2), fs=6.2)
    arrow(ax, (49.7, 47), (77.5, 52), "image file", color=ORANGE, ls="--", lo=(0, 2.6), fs=6.2)
    arrow(ax, (49.7, 45), (77.5, 41), "class card", color=GREY, ls="--", lo=(-1, 2.0), fs=6.2)
    arrow(ax, (49.2, 43), (77.5, 23.5), "new scan row", color=ORANGE, ls="--", lo=(-2, 5.5), fs=6.2)
    arrow(ax, (49.7, 34), (77.5, 39), "card text", color=GREY, ls="--", lo=(2, -2.6), fs=6.2)
    arrow(ax, (49.7, 22), (77.5, 22), "scan rows", color=GREY, ls="--", lo=(0, 2.0), fs=6.2)
    arrow(ax, (49.2, 12), (77.5, 20.5), "counts, severity,\ntimeline", color=GREY, ls="--", lo=(5, -3.2), fs=6.2)
    ax.text(50, 2.0, "D4 is Python data (disease_db.py), not a table. 5.0 delete also removes the image file from D3. Process 3.0 is decomposed in the level-2 diagram.", ha="center", fontsize=6.6, color=GREY)
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 7.0, 100, 70)
    ax.text(50, 67.5, "DFD level 2 - process 3.0 'Diagnose leaf photo' decomposed (backend/main.py detect + agrivision/inference.py)", ha="center", fontsize=9.2, color=NAVY, fontweight="bold")
    box(ax, 8, 50, 13, 8, "Farmer", NAVY, fs=9, bold=True)
    pos = {"1": (30, 56), "2": (54, 56), "3": (78, 56), "4": (78, 34), "5": (54, 34), "6": (30, 34), "7": (30, 14)}
    lab = {"1": "3.1\nValidate upload\n(ext, size, empty)", "2": "3.2\nDecode, resize\n256 px, RGB", "3": "3.3\nColour / texture\nfeatures", "4": "3.4\nSelect candidate\nclasses by crop",
           "5": "3.5\nScore + rank\nclasses", "6": "3.6\nCalibrate top-3\nconfidence", "7": "3.7\nAttach card,\nsave scan"}
    for k, (x, y) in pos.items():
        circle(ax, x, y, 8.0, lab[k], GREEN, fs=6.9)
    arrow(ax, (14.5, 51.5), (22.2, 54.5), "photo + crop", color=BLUE, lo=(-1, 3.2), fs=7.2)
    arrow(ax, (38.1, 56), (45.9, 56), None, color=NAVY)
    arrow(ax, (62.1, 56), (69.9, 56), "pixels", color=NAVY, lo=(0, 1.9), fs=7)
    arrow(ax, (78, 48), (78, 42.1), "6 features", color=NAVY, lo=(7, 0), fs=7)
    arrow(ax, (69.9, 34), (62.1, 34), "candidates", color=NAVY, lo=(0, 1.9), fs=7)
    arrow(ax, (45.9, 34), (38.1, 34), "scores", color=NAVY, lo=(0, 1.9), fs=7)
    arrow(ax, (30, 26), (30, 22.1), "top-3", color=NAVY, lo=(5, 0), fs=7)
    circle_y = 14
    store(ax, 70, 24, 18, 5.5, "D3 uploads", PALE_TEAL, TEAL, fs=7.6)
    store(ax, 70, 15, 18, 5.5, "D2 results", PALE_TEAL, TEAL, fs=7.6)
    store(ax, 70, 7.5, 22, 5.5, "D4 knowledge base", PALE_ORANGE, ORANGE, fs=7.6)
    arrow(ax, (37.0, 17.5), (61.0, 23.5), "image file", color=ORANGE, ls="--", lo=(1, 2.4), fs=7)
    arrow(ax, (38.0, 14.0), (61.0, 15.0), "scan row", color=ORANGE, ls="--", lo=(0, 1.9), fs=7)
    arrow(ax, (59.0, 7.5), (36.0, 10.0), "class card", color=GREY, ls="--", lo=(0, -2.0), fs=7)
    arrow(ax, (25.0, 19.5), (9.5, 46.0), "result id, top-3,\nseverity, treatments", color=GREEN, lo=(-8.5, 0), fs=7.0)
    arrow(ax, (24.6, 50.6), (14.6, 48.0), "400 / 413 errors", color="#B03A2E", lo=(-4.0, -3.4), fs=7.0)
    ax.text(50, 1.5, "3.1 answers HTTP 400 / 413 immediately for a bad file; 3.4 stops with HTTP 400 when a crop has fewer than 3 candidate classes (defect D1, Chapter 7).", ha="center", fontsize=6.8, color=GREY)
    save(fig, OUT / "05_dfd_level2.png")


# --------------------------------------------------------------------------------------------------
def uml_diagram():
    fig, ax = canvas(10, 9.0, 100, 90)
    ax.text(50, 88.5, "UML class diagram - the code is function-based: boxes are modules (<<module>>) and the two table-backed entities (<<entity>>)", ha="center", fontsize=7.6, color=NAVY, fontweight="bold")
    uml_class(ax, 1, 84, 29, "inference", ["MODEL: keras | onnx | None", "MODEL_KIND: str", "MODEL_LABELS: list | None", "PLANTDOC_MAP: dict[28]", "CROP_ALIASES: dict[19]"],
              ["predict(bytes, crop)", "_heuristic_predict(...)", "_features(Image)", "_candidates(crop)", "try_load_model()"], hdr=ORANGE, stereotype="module", fs=7.0)
    uml_class(ax, 35.5, 84, 29, "backend.main (FastAPI)", ["app: FastAPI", "SECRET: bytes", "TOKEN_TTL = 7 days", "CROP_OPTIONS: list[18]"],
              ["register(), login(), me()", "update_profile()", "detect(image, crop_type)", "history(), history_one()", "history_delete(), export_*()", "dashboard(), analytics()", "make_token(), read_token()", "current_user(request)"], hdr=GREEN, stereotype="module", fs=7.0)
    uml_class(ax, 70, 84, 29, "disease_db", ["CLASSES: list[38]", "_OVERRIDES: dict[26]", "_GENERIC_TREATMENTS: dict[5]"],
              ["get_disease_info(cls)", "display_name(cls)", "_kind_of(cls)", "_crop_of(cls)"], hdr=ORANGE, stereotype="module", fs=7.0)
    uml_class(ax, 1, 48, 29, "User  (table users)", ["id: TEXT  <<PK>>", "email: TEXT  <<unique>>", "password_hash: TEXT", "role, region, language", "crops: JSON text", "created_at, is_active"], [], hdr=TEAL, stereotype="entity", fs=7.0)
    uml_class(ax, 35.5, 48, 29, "Result  (table results)", ["id: TEXT  <<PK>>", "user_id: TEXT  <<FK>>", "image_path, image_size", "predicted: class label", "confidence: REAL", "top3: JSON text", "severity, crop_hint", "latency_ms, created_at"], [], hdr=TEAL, stereotype="entity", fs=7.0)
    uml_class(ax, 70, 48, 29, "app + config (Flask)", ["DB_PATH, UPLOAD_DIR", "MAX_CONTENT_LENGTH = 10 MB", "ALLOWED_EXT: jpg png webp"], ["init_db(): tables + demo user", "login_required(fn)"], hdr=GREY, stereotype="module", fs=7.0)
    uml_class(ax, 70, 24, 29, "train (offline script)", ["DATA: datasets/plantdoc-images", "MODEL_DIR: agrivision/models"], ["build_model(n, size)", "main(): writes .h5 + labels"], hdr="#7A8797", stereotype="script", fs=7.0)
    arrow(ax, (35.5, 76), (30, 76), "imports", color=NAVY, fs=7, lo=(0, 1.5))
    arrow(ax, (64.5, 76), (70, 76), "imports", color=NAVY, fs=7, lo=(0, 1.5))
    arrow(ax, (50, 51.0), (50, 48.2), "sqlite3 (SQL)", color=NAVY, fs=7, lo=(8, 0))
    arrow(ax, (35.5, 38), (30, 38), "N : 1", color=TEAL, fs=7, lo=(0, 1.6))
    arrow(ax, (70, 38), (64.5, 40), "init_db()", color=GREY, fs=7, lo=(0, 1.6))
    arrow(ax, (84, 48), (84, 63), "uses", color=GREY, fs=7, lo=(3.5, 0))
    ax.text(50, 4.5, "train.py writes models/plantdoc_cnn.h5 + labels.json, which inference.try_load_model() would load (the folder is empty in the shipped product).\nbackend.main uses sqlite3 directly (row_factory = Row); there are no ORM classes. Knowledge cards are plain dicts returned by get_disease_info().",
            ha="center", fontsize=6.5, color=GREY, va="center")
    save(fig, OUT / "06_uml_class_diagram.png")


# --------------------------------------------------------------------------------------------------
def sequence():
    fig, ax = canvas(10, 8.2, 100, 82)
    actors = [("Farmer\n(browser)", 7, BLUE), ("React SPA\nDetect + Result", 24, BLUE), ("FastAPI\nbackend.main", 42, GREEN), ("inference.py", 60, ORANGE), ("disease_db.py", 74, ORANGE), ("SQLite +\nuploads/", 90, TEAL)]
    for t, x, c in actors:
        box(ax, x, 77, 13, 7, t, c, fs=7.4)
        ax.plot([x, x], [73, 3], color="#9AA8BA", lw=1, ls=(0, (4, 3)), zorder=1)

    def msg(y, x1, x2, text, ret=False, color=NAVY):
        arrow(ax, (x1, y), (x2, y), None, color=color, ls="--" if ret else "-")
        ax.text((x1 + x2) / 2, y + 1.15, text, ha="center", fontsize=6.8, color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9), zorder=6)
    y = 69
    steps = [
        (7, 24, "choose leaf photo + crop"), (24, 42, "POST /api/v1/detect/upload (multipart, Bearer)"), (42, 42, None), (42, 92, "SELECT user by token uid"),
        (92, 42, "user row"), (42, 42, None), (42, 60, "predict(bytes, crop)"), (60, 60, None), (60, 42, "top-3 + confidence + latency_ms"),
        (42, 76, "get_disease_info(top-1)"), (76, 42, "card: severity, treatments"), (42, 92, "write uploads/<uuid>.jpg, INSERT results"), (42, 24, "200 JSON: result_id, top-3, treatments"),
        (24, 42, "GET /api/v1/history/{id}"), (42, 92, "SELECT result (owner check)"), (42, 24, "200 detail + card + engine name"), (24, 7, "result screen"),
    ]
    notes = {2: "verify HMAC + expiry; check ext, size, empty", 5: "401 if token bad", 7: "decode, resize 256, features,\nscore, rank, calibrate"}
    for i, (a, b, t) in enumerate(steps):
        if a == b:
            ax.add_patch(Rectangle((a + 0.8, y - 1.2), 17 if i in (2, 5) else 15.5, 4.2, fc=PALE_ORANGE if i == 7 else PALE_BLUE, ec="#B7C3D3", zorder=2))
            ax.text(a + 1.6, y + 0.9, notes.get(i, ""), fontsize=6.4, va="center", color=INK, zorder=3)
            y -= 3.4
            continue
        ret = (b < a) and i not in (13,)
        msg(y, a, b, t, ret=(b < a))
        y -= 3.3
    box(ax, 50, 1.8, 96, 3.2, "alt: image bad (400 INVALID_IMAGE_FORMAT / NO_IMAGE), > 10 MB (413), crop with < 3 candidate classes (400 UNREADABLE_IMAGE: defect), no token (401)", WHITE, tc=INK, ec=GREY, fs=6.6)
    save(fig, OUT / "07_sequence_diagram.png")


# --------------------------------------------------------------------------------------------------
def use_case():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.add_patch(FancyBboxPatch((22, 3), 56, 68, boxstyle="round,pad=0,rounding_size=1.5", fc="#F8FAFC", ec=NAVY, lw=1.3, zorder=1))
    ax.text(50, 68.5, "AgriVision system boundary", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    ucs = [("Browse disease guide", 50, 62, 26), ("Register / sign in", 50, 55, 26), ("Upload leaf photo and\nchoose crop", 50, 48, 30), ("View diagnosis, top-3,\nseverity, treatments", 50, 41, 30),
           ("Search / filter scan history", 50, 34, 30), ("Export scan as\nCSV / PDF", 38, 27, 21), ("Delete a scan", 62, 27, 21), ("View dashboard and analytics", 50, 20.5, 32),
           ("Edit profile (language, crops)", 50, 14, 32), ("Switch theme / interface language", 50, 7.5, 34)]
    left = {}
    for t, x, y, w in ucs:
        ellipse(ax, x, y, w, 5.4, t, PALE_GREEN, GREEN, fs=6.9)
        left[t] = (x - w / 2, y)
    box(ax, 9, 44, 14, 14, "Farmer\n(registered)", NAVY, fs=8.6, bold=True)
    box(ax, 9, 66, 14, 8, "Visitor\n(guest)", GREY, fs=8.6, bold=True)
    box(ax, 91, 40, 15, 14, "Model owner\n(offline: train.py,\nrun_experiments.py)", WHITE, tc=INK, ec=ORANGE, fs=7.2, ls="--")
    for t in ("Browse disease guide", "Register / sign in", "Switch theme / interface language"):
        x, y = left[t]
        ax.plot([16, x], [66, y], color=GREY, lw=1, zorder=1)
    for t, (x, y) in left.items():
        if t != "Register / sign in":
            ax.plot([16, x], [46, y], color=NAVY, lw=1, zorder=1)
    ax.text(50, 0.8, "Dashed actor: works outside the web application (no use case inside the boundary). Delete and export require ownership of the scan (404 otherwise).", ha="center", fontsize=6.6, color=GREY)
    ax.text(91, 28, "trains CNNs,\nmeasures accuracy;\nweights can be\ndropped into models/", ha="center", fontsize=6.6, color=GREY)
    save(fig, OUT / "08_use_case_diagram.png")


# --------------------------------------------------------------------------------------------------
def er():
    fig, ax = canvas(10, 6.4, 100, 64)

    def table(x, y, w, title, cols, color, note=None):
        lh = 3.0
        h = 4.2 + lh * len(cols) + 1
        ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
        ax.add_patch(Rectangle((x, y - 4.2), w, 4.2, fc=color, ec=NAVY, lw=1.3, zorder=3))
        ax.text(x + w / 2, y - 2.1, title, ha="center", va="center", color=WHITE, fontsize=9.2, fontweight="bold", zorder=4)
        for i, (n, t, k) in enumerate(cols):
            yy = y - 4.2 - 1.8 - i * lh
            ax.text(x + 1, yy, (k + " ") if k else "", fontsize=6.8, color=ORANGE, fontweight="bold", va="center", zorder=4)
            ax.text(x + 5.4, yy, n, fontsize=7.2, color=INK, va="center", zorder=4, family="DejaVu Sans Mono")
            ax.text(x + w - 1, yy, t, fontsize=6.6, color=GREY, va="center", ha="right", zorder=4, family="DejaVu Sans Mono")
        return h
    h1 = table(3, 60, 34, "users", [("id", "TEXT", "PK"), ("email", "TEXT UNIQUE NN", ""), ("phone", "TEXT", ""), ("full_name", "TEXT", ""), ("password_hash", "TEXT NN", ""), ("role", "'farmer'", ""),
                                    ("region", "TEXT ''", ""), ("language", "'en' (en/hi/mr)", ""), ("crops", "JSON text '[]'", ""), ("created_at", "TEXT", ""), ("is_active", "INT 1", "")], TEAL)
    table(55, 60, 40, "results", [("id", "TEXT", "PK"), ("user_id", "TEXT NN", "FK"), ("image_path", "TEXT", ""), ("image_size", "INT", ""), ("predicted", "class label", ""), ("confidence", "REAL", ""),
                                  ("top3", "JSON text", ""), ("severity", "high|medium|none", ""), ("crop_hint", "TEXT", ""), ("latency_ms", "INT", ""), ("created_at", "TEXT", ""), ("bookmarked", "INT 0", "")], TEAL)
    arrow(ax, (37, 36), (55, 36), None, color=NAVY, style="-|>")
    ax.text(46, 38.2, "1 : N\nuser_id -> users.id", ha="center", fontsize=7.4, color=INK)
    ax.add_patch(Rectangle((3, 3.5), 34, 11.5, fc=PALE_ORANGE, ec=ORANGE, lw=1.2, ls="--", zorder=2))
    ax.text(20, 12.8, "Disease knowledge base (not a table)", ha="center", fontsize=8, color=NAVY, fontweight="bold")
    ax.text(20, 8.3, "disease_db.py: 38 class labels, 26 curated cards\nresults.predicted holds one of these 38 labels", ha="center", fontsize=6.9, color=INK, va="center")
    ax.add_patch(Rectangle((55, 3.5), 40, 11.5, fc=PALE_TEAL, ec=TEAL, lw=1.2, ls="--", zorder=2))
    ax.text(75, 12.8, "Upload files (not a table)", ha="center", fontsize=8, color=NAVY, fontweight="bold")
    ax.text(75, 8.3, "static/uploads/<uuid>.<ext>; results.image_path points to it\nDELETE /history/{id} removes row and file", ha="center", fontsize=6.9, color=INK, va="center")
    arrow(ax, (75, 15.2), (75, 20.0), None, color=GREY, ls="--")
    arrow(ax, (37, 11), (55, 40), "predicted", color=GREY, ls="--", lo=(-3, 8), fs=7, rad=-0.15)
    ax.text(50, 0.8, "SQLite, created by init_db() in agrivision/app.py; shared by the Flask and FastAPI front ends. A demo farmer is seeded on first start.", ha="center", fontsize=6.6, color=GREY)
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------------------------------------------
def algo_flow():
    fig, ax = canvas(10, 9.0, 100, 90)
    ax.text(50, 88, "Core algorithm - predict() in agrivision/inference.py (heuristic engine, as shipped)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    box(ax, 50, 82, 36, 4.6, "Start: image bytes + crop hint", NAVY, fs=8)
    diamond(ax, 50, 74, 38, 7.6, "Trained model loaded?\n(models/*.h5, .keras, .onnx)", fs=7.4)
    box(ax, 18, 74, 24, 8.6, "CNN branch: resize to the\nmodel input, /255, predict,\nmap PlantDoc labels to\n38 classes, top-3", PALE_PURPLE, tc=INK, ec=PURPLE, fs=6.8)
    ax.text(32.5, 75.6, "yes", fontsize=7.4, color=INK)
    ax.text(51.5, 69.0, "no (shipped state)", fontsize=7.4, color=INK)
    box(ax, 50, 63, 46, 5.4, "Open image, convert to RGB, resize to 256 x 256, scale to [0, 1]", GREEN, fs=7.6)
    box(ax, 50, 55, 58, 7.0, "Features: green share (g > r+0.03 and g > b+0.01), brown share, yellow share,\ndark share (mean < 0.25), white share (min > 0.72), global std", GREEN, fs=7.2)
    box(ax, 50, 47, 54, 5.6, "candidates = classes of the chosen crop (all 38 if 'general' or unknown)", GREEN, fs=7.6)
    diamond(ax, 50, 38.5, 40, 8, "fewer than 3 candidates?\n(10 of 19 crop options)", PALE_ORANGE, ORANGE, fs=7.4)
    box(ax, 83, 38.5, 24, 8.6, "IndexError -> API answers\nHTTP 400 UNREADABLE_IMAGE\n(defect, Chapter 7)", "#F9DAD6", tc="#8A2B20", ec="#B03A2E", fs=6.8)
    ax.text(70.5, 40.0, "yes", fontsize=7.4, color=INK)
    ax.text(51.5, 32.2, "no", fontsize=7.4, color=INK)
    box(ax, 50, 26, 66, 8.6, "score(class) = healthy: 3*green - 4*(brown+yellow) - 1.5*dark + (0.25 - |std - 0.18|)\ndiseased: 3.2*brown + 2.4*yellow + 1.2*dark + 1.6*white + 1.5*max(0, 0.5 - green)\n+ name bonuses (mildew/mold, rust, blight/spot, mosaic/curl, mite) + 0.35*hash jitter", ORANGE, fs=6.8)
    box(ax, 50, 15.5, 58, 7.0, "rank by score, keep top-3; confidence_1 = clamp(0.62 + min(1.6, s) * 0.22, 0.62, 0.99);\nconfidence_2, confidence_3 = fractions of confidence_1 from the image hash", ORANGE, fs=7)
    box(ax, 50, 6.5, 60, 5.4, "return top-3, predicted class, confidence, engine name, latency_ms (+40 constant)", NAVY, fs=7.4)
    for a, b in [((50, 79.7), (50, 77.8)), ((50, 70.2), (50, 65.7)), ((50, 60.3), (50, 58.5)), ((50, 51.5), (50, 49.8)), ((50, 44.2), (50, 42.5)),
                 ((50, 34.5), (50, 30.3)), ((50, 21.7), (50, 19.0)), ((50, 12.0), (50, 9.2))]:
        arrow(ax, a, b, None, color=NAVY)
    arrow(ax, (31, 74), (30, 74), None, color=NAVY)
    arrow(ax, (18, 69.7), (18, 6.5), None, color=PURPLE, ls="--", rad=0.0)
    arrow(ax, (18, 6.5), (20, 6.5), None, color=PURPLE, ls="--")
    arrow(ax, (70, 38.5), (71, 38.5), None, color="#B03A2E")
    save(fig, OUT / "10_core_algorithm_flowchart.png")


# --------------------------------------------------------------------------------------------------
def train_flow():
    fig, ax = canvas(10, 6.6, 100, 66)
    ax.text(50, 63.5, "Offline experiment protocol (scripts/run_experiments.py) - how every accuracy in this report was measured", ha="center", fontsize=9, color=NAVY, fontweight="bold")
    box(ax, 14, 52, 22, 9, "PlantDoc train folder\n2,342 photos, 28 classes", BLUE, fs=7.6)
    box(ax, 14, 33, 22, 9, "PlantDoc test folder\n236 photos, 27 classes", BLUE, fs=7.6)
    box(ax, 42, 52, 22, 9, "Resize 224x224\n(uint8 cache)", GREEN, fs=7.6)
    box(ax, 42, 33, 22, 9, "Resize 224x224\n(never used for fitting\nor model selection)", GREEN, fs=7.2)
    box(ax, 70, 56, 24, 11, "90 % fit / 10 % validation\n(stratified, per seed)\nearly stopping on validation", ORANGE, fs=7.2)
    box(ax, 70, 40, 24, 11, "Models (3 seeds each):\ncompact CNN 189,655 params\nMobileNetV2 2.29 M (ImageNet)", PURPLE, fs=7.2)
    box(ax, 91, 48, 16, 14, "Heuristic\nengine\n(5 hash seeds)", GREY, fs=7.6)
    box(ax, 56, 14, 60, 11, "Test metrics: accuracy, top-3, macro-F1, per-class P / R / F1, confusion matrix,\ncrop-level and healthy-vs-diseased accuracy, CPU latency per image", NAVY, fs=7.4)
    arrow(ax, (25, 52), (31, 52), None, color=NAVY)
    arrow(ax, (25, 33), (31, 33), None, color=NAVY)
    arrow(ax, (53, 52), (58, 54), None, color=NAVY)
    arrow(ax, (70, 50.5), (70, 45.5), None, color=NAVY)
    arrow(ax, (70, 34.5), (62, 20), "fitted model", color=NAVY, lo=(7, 2), fs=7)
    arrow(ax, (53, 31), (40, 20.5), "test images", color=NAVY, lo=(-6, 1), fs=7)
    arrow(ax, (91, 41), (80, 20), "same test images", color=GREY, ls="--", lo=(9, 2), fs=7)
    ax.text(50, 3.2, "The shipped train.py instead validates on the test folder (and mislabels the two grape classes there); the numbers in this report avoid that.", ha="center", fontsize=6.8, color=GREY)
    save(fig, OUT / "11_experiment_protocol.png")


def deploy():
    fig, ax = canvas(10, 4.6, 100, 46)
    panel(ax, 2, 4, 96, 38, "Local deployment (run.bat) - one PC, two processes", LIGHT, "#B7C3D3", tc=NAVY)
    box(ax, 17, 22, 24, 14, "Browser\nChrome / Edge\nhttp://localhost:5416", BLUE, fs=8)
    box(ax, 47, 22, 24, 14, "Vite dev server\nnode 20+, port 5416\nproxy /api -> 8416", PURPLE, fs=8)
    box(ax, 77, 22, 24, 14, "uvicorn + FastAPI\n.venv, port 8416\nPYTHONHASHSEED=0", GREEN, fs=8)
    store(ax, 77, 8.5, 30, 6, "agrivision.db + uploads/", PALE_TEAL, TEAL, fs=8)
    arrow(ax, (29, 22), (35, 22), None, color=NAVY)
    arrow(ax, (59, 22), (65, 22), "/api/*", color=NAVY, lo=(0, 2.2), fs=7.5)
    arrow(ax, (77, 15), (77, 11.6), None, color=NAVY)
    ax.text(30, 8.5, "Optional: Flask original on port 5000\n(shares the same database and uploads)", fontsize=7.2, color=GREY, ha="center", va="center")
    save(fig, OUT / "12_deployment.png")


if __name__ == "__main__":
    from matplotlib.patches import Rectangle, FancyBboxPatch  # noqa: F401
    for fn in (system_architecture, high_level_workflow, dfd0, dfd1, dfd2, uml_diagram, sequence, use_case, er, algo_flow, train_flow, deploy):
        fn()
