"""Mosaic design diagrams (matplotlib, 150 dpi) -> docs/diagrams/.\n\n    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; writes all eleven\nEvery diagram mirrors the code: backend/app (main, routers/*, deps, security, models, ml/*) and frontend/src.\n"""
from __future__ import annotations

from pathlib import Path

from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 01 architecture
def architecture():
    fig, ax = canvas(9.6, 7.6, 100, 79)
    ax.text(40, 77, "Mosaic: browser, FastAPI service, ML modules, local files - one process, CPU only", ha="center", fontsize=8, color=ORANGE, fontweight="bold")
    panel(ax, 1, 62, 72, 13.5, "TIER 1 - BROWSER (Next.js 16 + React 19, TypeScript, port 3000)", fc=PALE_BLUE, fs=8.4)
    box(ax, 19.5, 67.6, 32, 7, "Pages: Landing (Three.js canvas, GSAP),\nLogin, Register, Analyze (upload / webcam),\nHistory, History detail", BLUE, fs=6.9)
    box(ax, 55, 67.6, 32, 7, "lib/api.ts (fetch + Bearer token)\nzustand store 'mosaic-auth' (persisted)\nRecharts bar chart + compound bars", BLUE, fs=6.9)
    panel(ax, 1, 41, 72, 19, "TIER 2 - FastAPI application (app/main.py, uvicorn, port 8000 by default)", fc=PALE_PURPLE, fs=8.4)
    box(ax, 19.5, 49.2, 32, 11.5, "Routers (8 endpoints + static thumbs)\n/api/auth: register login me\n/api/analyze   /api/history (list, get, delete)\n/api/health   CORS: localhost:3000", PURPLE, fs=6.6)
    box(ax, 55, 49.2, 32, 11.5, "deps.py: optional / required Bearer user\nsecurity.py: bcrypt hash, HS256 JWT (7 days)\nschemas.py: pydantic request / response\nstartup: load_model() once", PURPLE, fs=6.6)
    panel(ax, 1, 14, 72, 25, "TIER 3 - ML modules (app/ml, PyTorch CPU + OpenCV)", fc=PALE_TEAL, fs=8.4)
    mods = [(10.5, 31, "face.py\nHaar cascade\nlargest face\n-> grayscale crop"), (28.5, 31, "inference.py\nresize 64, scale\n[-1, 1], CNN,\nsigmoid, sort"), (46.5, 31, "classifier_model\nEmotionCNN\n4 conv + 2 FC\n(7 or 18 out)"), (64, 31, "gan_model\nGenerator /\nDiscriminator\n(train time only)")]
    for x, y, t in mods:
        box(ax, x, y, 16.5, 9.5, t, TEAL, fs=6.5)
    box(ax, 19.5, 20, 34, 6.5, "taxonomy.py: 7 basic + 11 compound = 18 labels", NAVY, fs=6.7)
    box(ax, 55.5, 20, 34, 6.5, "train_*.py + run_pipeline: backbone -> cEmoGAN -> final", NAVY, fs=6.7)
    panel(ax, 1, 1, 72, 11.5, "TIER 4 - local files and SQLite", fc=LIGHT, fs=8.4)
    box(ax, 15, 5.6, 25, 6.2, "mosaic.db (SQLite)\nusers, analyses", GREY, fs=6.4)
    box(ax, 42, 5.6, 24, 6.2, "checkpoints/\nclassifier_final.pt, stage1_backbone.pt,\ngenerator.pt, training_log.txt", GREY, fs=5.9)
    box(ax, 63, 5.6, 17, 6.2, "media/thumbs/\n<id>.jpg", GREY, fs=6.4)
    panel(ax, 76, 14, 23, 61, "OUTSIDE THE PROCESS", fc=PALE_ORANGE, ec=ORANGE, fs=8.4, tc=ORANGE)
    box(ax, 87.5, 65, 19, 9, "User's browser\n(upload / webcam\nframe as JPEG)", ORANGE, fs=6.6)
    box(ax, 87.5, 53, 19, 9, "FER2013 pickles\n(Hugging Face mirror;\ntraining only)", ORANGE, fs=6.6)
    box(ax, 87.5, 41, 19, 9, "OpenCV bundled\nhaarcascade_frontal-\nface_default.xml", ORANGE, fs=6.2)
    box(ax, 87.5, 29, 19, 9, "No external API,\nno cloud call at\nrun time", ORANGE, fs=6.4)
    box(ax, 87.5, 18.5, 19, 7.5, "End user", NAVY, fs=6.6)
    arrow(ax, (40, 62), (40, 60.5), "HTTP + JSON / multipart", color=NAVY, lw=1.6, lo=(12, 0), fs=6.8)
    arrow(ax, (40, 41), (40, 39.5), "import / call", color=NAVY, lw=1.6, lo=(8, 0), fs=6.8)
    arrow(ax, (40, 14), (40, 12.7), "read / write", color=NAVY, lw=1.6, lo=(8, 0), fs=6.8)
    arrow(ax, (73, 66), (77.5, 66), "", color=ORANGE, lw=1.4)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------- 02 high-level workflow
def workflow():
    fig, ax = canvas(9.8, 6.4, 100, 65.3)
    ax.text(50, 63.3, "Offline training once (three stages), then one online pass per uploaded image", ha="center", fontsize=8.4, color=NAVY, fontweight="bold")
    panel(ax, 1, 38, 98, 22, "STAGE 1 - OFFLINE (python -m app.ml.run_pipeline)", fc=PALE_BLUE, fs=8.6)
    xs = [10, 29, 48, 67, 86]
    items = [("1 LOAD", "FER2013 pickles\n28,709 train /\n7,178 test, 48x48"), ("2 BACKBONE", "7-class softmax CNN,\nAdam 1e-3,\n5 epochs"),
             ("3 cEmoGAN", "conditional GAN,\n2,800 faces,\n10 epochs"), ("4 SYNTHESISE", "11 compound classes x 200:\ncondition 0.5 / 0.5 on the\ntwo component emotions"),
             ("5 FINAL CNN", "18 sigmoid outputs, BCE,\ninit from backbone,\n5 epochs -> .pt")]
    for x, (t, b) in zip(xs, items):
        box(ax, x, 48.5, 17, 12.5, f"{t}\n\n{b}", BLUE if x < 60 else NAVY, fs=6.4)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.5, 48.5), (b - 8.5, 48.5), color=NAVY, lw=1.5)
    ax.text(50, 36.0, "classifier_final.pt is loaded once at API start-up and reused for every request", ha="center", fontsize=7, color=GREY, style="italic")
    panel(ax, 1, 1, 98, 32, "STAGE 2 - ONLINE: one pass per image (POST /api/analyze)", fc=PALE_TEAL, fs=8.6)
    xs2 = [10, 29, 48, 67, 86]
    it2 = [("A UPLOAD", "browser sends JPEG /\nPNG (file or webcam\nframe), optional token"), ("B DETECT", "Haar cascade finds the\nlargest face, crops it\nto grayscale"),
           ("C CLASSIFY", "resize 64x64, scale to\n[-1, 1], CNN forward,\nsigmoid on 18 outputs"), ("D RANK", "7 basic + 11 compound\nsorted; dominant =\nargmax of all 18"), ("E STORE + SHOW", "signed-in user: row in\nSQLite + face thumbnail;\nUI draws bars")]
    for x, (t, b) in zip(xs2, it2):
        box(ax, x, 19, 17, 13.5, f"{t}\n\n{b}", TEAL if x < 60 else PURPLE, fs=6.4)
    for a, b in zip(xs2[:-1], xs2[1:]):
        arrow(ax, (a + 8.5, 19), (b - 8.5, 19), color=NAVY, lw=1.5)
    ax.text(50, 5.5, "no face found: the API answers 200 with face_detected = false and empty lists; a row is still stored for signed-in users", ha="center", fontsize=7, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


# ------------------------------------------------------------------ 03-05 DFDs
def dfd0():
    fig, ax = canvas(9.2, 4.7, 100, 51)
    ax.text(2, 48.8, "Level 0 data flow diagram (context)", fontsize=9, fontweight="bold", color=NAVY)
    box(ax, 12, 36, 18, 9, "End user\n(browser)", NAVY, fs=8.5)
    box(ax, 12, 10, 18, 9, "Developer\n(training run)", PURPLE, fs=8)
    box(ax, 88, 36, 18, 9, "OpenCV Haar\ncascade file", ORANGE, fs=8)
    box(ax, 88, 10, 18, 9, "FER2013 pickles\n(offline)", ORANGE, fs=8)
    circle(ax, 50, 26, 13.5, "0\nMosaic\nEmotion\nAnalysis\nService", BLUE, fs=8.4)
    store(ax, 50, 4.5, 30, 6, "D1  SQLite + checkpoints + thumbs", fs=7.6)
    arrow(ax, (21, 38), (38, 31), "photo, credentials,\nhistory requests", lo=(0, 4.2), fs=7)
    arrow(ax, (38.5, 23), (21, 33.5), "token, basic + compound\nscores, dominant, history", lo=(0, -4.5), fs=7, color=TEAL)
    arrow(ax, (21, 10), (38, 19.5), "run pipeline", lo=(-1, -3), fs=7)
    arrow(ax, (79, 36), (62, 30), "face detector", lo=(1, 4.2), fs=7)
    arrow(ax, (79, 10), (62, 19.5), "labelled faces", lo=(2, -3), fs=7)
    arrow(ax, (46, 12.5), (46, 7.6), "", color=NAVY)
    arrow(ax, (54, 7.6), (54, 12.5), "", color=NAVY)
    save(fig, OUT / "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(9.8, 7.6, 100, 77.5)
    ax.text(2, 75.2, "Level 1 data flow diagram", fontsize=9, fontweight="bold", color=NAVY)
    box(ax, 8, 66, 13, 8, "End user", NAVY, fs=7.6)
    box(ax, 8, 24, 13, 8, "Developer", PURPLE, fs=7.6)
    box(ax, 8, 9, 13, 8, "FER2013\npickles", ORANGE, fs=7.2)
    circle(ax, 30, 66, 7.4, "1.0\nAccount &\ntoken", BLUE, fs=7)
    circle(ax, 54, 66, 7.4, "2.0\nDetect\nface", TEAL, fs=7)
    circle(ax, 78, 66, 7.4, "3.0\nClassify\n(CNN)", TEAL, fs=7)
    circle(ax, 78, 38, 7.4, "4.0\nRank &\nrespond", TEAL, fs=7)
    circle(ax, 54, 38, 7.4, "5.0\nStore\nanalysis", BLUE, fs=7)
    circle(ax, 30, 38, 7.4, "6.0\nHistory\nmanager", BLUE, fs=7)
    circle(ax, 32, 9, 7.4, "7.0\nTrain\npipeline", PURPLE, fs=7)
    store(ax, 30, 52, 18, 5.0, "D1 users", fs=7.4)
    store(ax, 42, 22, 20, 5.0, "D2 analyses", fs=7.4)
    store(ax, 68, 22, 22, 5.0, "D3 thumbnails", fs=7.4)
    store(ax, 62, 9, 24, 5.0, "D4 checkpoints", fs=7.4)
    arrow(ax, (14.5, 67.5), (22.6, 67.5), "register / login", lo=(0, 1.8), fs=6.2)
    arrow(ax, (22.6, 64.5), (14.5, 64.5), "JWT", lo=(0, -1.8), fs=6.2, color=TEAL)
    arrow(ax, (30, 58.6), (30, 54.6), "", color=NAVY)
    arrow(ax, (37.4, 66), (46.6, 66), "photo (+ token)", lo=(0, 2.0), fs=6.0)
    arrow(ax, (61.4, 66), (70.6, 66), "face crop", lo=(0, 2.0), fs=6.0)
    arrow(ax, (78, 58.6), (78, 45.4), "18 scores", lo=(4.5, 0), fs=6.0)
    arrow(ax, (70.6, 38), (61.4, 38), "result", lo=(0, 2.0), fs=6.0)
    arrow(ax, (46.6, 38), (37.4, 38), "record", lo=(0, 2.0), fs=6.0)
    arrow(ax, (50, 31), (44, 24.6), "insert", lo=(-3, 1.4), fs=6.0)
    arrow(ax, (58, 31), (66, 24.6), "face crop .jpg", lo=(5.5, 1.4), fs=6.0)
    arrow(ax, (34, 31), (40, 24.6), "query", lo=(-3.5, 0), fs=6.0)
    arrow(ax, (13, 62), (24, 42.6), "history requests", lo=(-4, 3), fs=6.0)
    arrow(ax, (12, 14), (24.6, 9), "", color=NAVY)
    arrow(ax, (14.5, 22), (26, 15), "run", lo=(-1, 2.4), fs=6.2)
    arrow(ax, (39.4, 9), (50, 9), "weights", lo=(0, 2.0), fs=6.0)
    ax.plot([74, 95, 95], [9, 9, 66], color=NAVY, lw=1.3, ls="--", zorder=3)
    arrow(ax, (95, 66), (85.6, 66), "", ls="--")
    ax.text(93.4, 40, "weights loaded once at API start-up", rotation=90, fontsize=6.0, color=GREY, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.6))
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(9.8, 6.4, 100, 65.3)
    ax.text(2, 63.3, "Level 2 data flow diagram: process 3.0 (classify) and 4.0 (rank and respond) expanded", fontsize=8.8, fontweight="bold", color=NAVY)
    box(ax, 9, 46, 15, 10, "From 2.0\ngrayscale\nface crop", NAVY, fs=6.8)
    circle(ax, 29, 46, 6.6, "3.1\nResize\n64x64", TEAL, fs=6.4)
    circle(ax, 48, 46, 6.6, "3.2\nScale\nto [-1, 1]", TEAL, fs=6.2)
    circle(ax, 68, 46, 7.2, "3.3\nCNN forward\n(4 conv,\n2 FC)", TEAL, fs=5.8)
    circle(ax, 88, 46, 6.8, "3.4\nSigmoid\non 18\nlogits", TEAL, fs=6)
    circle(ax, 88, 24, 7.2, "4.1\nSplit 7 basic\n/ 11 compound", PURPLE, fs=5.8)
    circle(ax, 62, 24, 7.0, "4.2\nSort each\nlist by\nconfidence", PURPLE, fs=5.8)
    circle(ax, 36, 24, 7.0, "4.3\nArgmax of\nall 18 =\ndominant", PURPLE, fs=5.8)
    box(ax, 12, 24, 15, 9, "To 5.0\nJSON result", NAVY, fs=6.8)
    store(ax, 58, 35, 34, 5.0, "D4 classifier_final.pt (loaded at start-up)", fs=6.4)
    arrow(ax, (16.5, 46), (22.4, 46), "", color=NAVY)
    arrow(ax, (35.6, 46), (41.4, 46), "uint8", lo=(0, 2.0), fs=5.8)
    arrow(ax, (54.6, 46), (60.8, 46), "float tensor", lo=(0, 2.2), fs=5.8)
    arrow(ax, (75.2, 46), (81.2, 46), "logits", lo=(0, 2.2), fs=5.8)
    arrow(ax, (88, 39.2), (88, 31.2), "18 probs", lo=(-5, 0), fs=5.8)
    arrow(ax, (80.8, 24), (69, 24), "two lists", lo=(0, 2.2), fs=5.8)
    arrow(ax, (55, 24), (43, 24), "sorted", lo=(0, 2.2), fs=5.8)
    arrow(ax, (29, 24), (19.6, 24), "result", lo=(0, 2.2), fs=5.8)
    arrow(ax, (66, 37.5), (67, 39.3), "", color=NAVY, ls="--")
    save(fig, OUT / "05_dfd_level2.png")


# ------------------------------------------------------------------ 06 class diagram
def classes():
    fig, ax = canvas(9.8, 10.0, 100, 102)
    ax.text(1.5, 100.2, "UML class diagram (classes and module-level interfaces actually present in the code)", fontsize=8.6, fontweight="bold", color=NAVY)
    uml_class(ax, 1.5, 97, 30, "User (models.py)", ["id: str (uuid) PK", "name: str", "email: str unique", "password_hash: str", "created_at: datetime"], ["analyses -> Analysis[]"], fs=6.3)
    uml_class(ax, 35, 97, 30, "Analysis (models.py)", ["id: str (uuid) PK", "user_id: FK users.id", "created_at: datetime", "face_detected: bool", "basic_emotions: JSON", "compound_emotions: JSON", "dominant: JSON", "thumbnail_path: str"], ["user -> User"], fs=6.1)
    uml_class(ax, 68.5, 97, 30, "security / deps", [],
              ["hash_password(pw)", "verify_password(pw, hash)", "create_access_token(sub)", "decode_access_token(tok)", "get_current_user()", "get_current_user_optional()"], fs=6.1, hdr=BLUE, stereotype="module")
    uml_class(ax, 1.5, 64, 30, "EmotionCNN (nn.Module)", ["features: 4 x (Conv-BN-ReLU-Pool)", "classifier: Flatten, FC 2048-256,", "   ReLU, Dropout 0.4, FC 256-out", "IMG_SIZE = 64"], ["forward(x) -> logits"], fs=6.1, hdr=TEAL)
    uml_class(ax, 35, 64, 30, "ConditionalGenerator", ["net: 5 x ConvTranspose2d", "NOISE_DIM = 100", "cond_dim = 7"], ["forward(z, cond) -> 64x64 image"], fs=6.1, hdr=TEAL)
    uml_class(ax, 68.5, 64, 30, "ConditionalDiscriminator", ["img_net: 4 x Conv + LeakyReLU", "cond_proj: Linear(7, 16)", "out: Linear(4112, 1)"], ["forward(img, cond) -> logit"], fs=6.1, hdr=TEAL)
    uml_class(ax, 1.5, 30, 30, "inference (module)", ["_model: EmotionCNN | None"],
              ["load_model()", "model_is_loaded()", "analyze_image_bytes(bytes)", "    -> (found, basic, compound,", "       dominant, face_crop)"], fs=6.1, hdr=BLUE, stereotype="module")
    uml_class(ax, 35, 30, 30, "face / taxonomy", ["BASIC_EMOTIONS (7)", "COMPOUND_EMOTIONS (11)", "COMPOUND_COMPONENTS", "ALL_LABELS (18)"],
              ["detect_largest_face(bgr)", "display_label(key)"], fs=6.1, hdr=BLUE, stereotype="module")
    uml_class(ax, 68.5, 30, 30, "routers (FastAPI)", [],
              ["POST /api/auth/register, /login", "GET  /api/auth/me", "POST /api/analyze", "GET  /api/history, /history/{id}", "DELETE /api/history/{id}", "GET  /api/health"], fs=6.0, hdr=PURPLE, stereotype="module")
    arrow(ax, (31.5, 90), (35, 90), "1 : N", lo=(0, 1.4), fs=6, color=NAVY)
    arrow(ax, (16, 30), (16, 47.6), "uses", lo=(3, 0), fs=6)
    arrow(ax, (31.5, 24), (35, 24), "uses", lo=(0, 1.4), fs=6)
    arrow(ax, (68.5, 24), (65, 24), "calls", lo=(0, 1.4), fs=6)
    ax.text(50, 6.0, "inference.analyze_image_bytes() uses face.detect_largest_face(), EmotionCNN (18 outputs) and taxonomy; routers use security, deps, models and inference.", ha="center", fontsize=6.2, color=GREY, style="italic")
    ax.text(50, 3.2, "Generator and Discriminator are used only by the training scripts (train_gan.py, synthesize_compound.py); they are not loaded by the API.", ha="center", fontsize=6.2, color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")


# ------------------------------------------------------------------ 07 sequence
def sequence():
    fig, ax = canvas(9.2, 8.0, 100, 87)
    ax.text(2, 85.3, "Sequence diagram: signed-in user uploads a photo and receives a result", fontsize=8.4, fontweight="bold", color=NAVY)
    names = ["User", "Next.js UI", "FastAPI\nrouter", "deps /\nsecurity", "inference", "face\n(Haar)", "EmotionCNN", "SQLite", "media/\nthumbs"]
    xs = [6, 16.5, 28, 40, 51.5, 62.5, 73.5, 84, 94.5]
    for x, n in zip(xs, names):
        box(ax, x, 80, 9.6, 5.5, n, NAVY, fs=6.0)
        ax.plot([x, x], [77, 3], color="#9AA7B8", lw=0.9, ls="--", zorder=1)
    msgs = [
        (0, 1, 74.5, "choose / drop image", False), (1, 2, 71.5, "POST /api/analyze  multipart image + Bearer token", False), (2, 3, 68.5, "get_current_user_optional()", False),
        (3, 7, 66, "SELECT user by id from JWT 'sub'", False), (3, 2, 63.6, "User or None", True), (2, 4, 60.8, "analyze_image_bytes(bytes)", False),
        (4, 5, 58.0, "detect_largest_face(bgr)", False), (5, 4, 55.6, "grayscale crop or None", True), (4, 6, 52.8, "resize 64, scale, forward", False),
        (6, 4, 50.4, "18 logits -> sigmoid", True), (4, 2, 47.6, "found, basic[7], compound[11], dominant, crop", True), (2, 7, 44.8, "INSERT Analysis (JSON lists, dominant)", False),
        (2, 8, 42.0, "cv2.imwrite(<id>.jpg)", False), (2, 7, 39.2, "UPDATE thumbnail_path", False), (2, 1, 36.4, "200 AnalysisResponse", True),
        (1, 0, 33.6, "bars, dominant card, 6 compound rows", True),
    ]
    for a, b, y, t, ret in msgs:
        x1, x2 = xs[a], xs[b]
        arrow(ax, (x1, y), (x2, y), None, color=GREY if ret else NAVY, lw=1.2, ls="--" if ret else "-")
        ax.text((x1 + x2) / 2, y + 1.15, t, fontsize=6.2, ha="center", va="bottom", color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9), zorder=6)
    panel(ax, 2, 4, 96, 25, "ALTERNATIVE FLOWS", fc=PALE_ORANGE, ec=ORANGE, fs=7.6, tc=ORANGE)
    alts = ["- No Bearer token (or invalid token): the user is None, the result is returned with id = null and nothing is stored.",
            "- No face detected: face_detected = false, empty lists, dominant = null; for signed-in users a row is still inserted, no thumbnail.",
            "- Model file missing at start-up: /api/health reports model_loaded = false and the first analyze with a face raises FileNotFoundError (HTTP 500).",
            "- Undecodable or empty upload: PIL raises inside analyze_image_bytes and the request ends with HTTP 500 (no handler).",
            "- History: GET /api/history and /history/{id} require the token; another user's id returns 404; DELETE returns 204."]
    for i, t in enumerate(alts):
        ax.text(4, 24.5 - i * 4.2, t, fontsize=6.0, va="center")
    save(fig, OUT / "07_sequence_main_flow.png")


# ------------------------------------------------------------------ 08 use case
def usecase():
    fig, ax = canvas(8.4, 6.8, 100, 81)
    ax.text(2, 78.5, "Use-case diagram", fontsize=9, fontweight="bold", color=NAVY)
    ax.add_patch(Rectangle((24, 3), 52, 72, fc="#FBFCFE", ec=NAVY, lw=1.4, zorder=0))
    ax.text(50, 73, "Mosaic", ha="center", fontsize=8.6, fontweight="bold", color=NAVY)
    cases = ["Register an account", "Log in / log out", "Upload a face photo", "Capture a webcam frame", "View basic-emotion chart",
             "View compound-emotion scores", "View dominant emotion", "Browse analysis history", "Delete a history entry", "Open a saved result (route only)",
             "Analyse without an account (API)", "Run the training pipeline (command line)"]
    ys = [67 - i * 5.3 for i in range(len(cases))]
    for t, y in zip(cases, ys):
        ellipse(ax, 50, y, 38, 4.2, t, fs=6.6)
    box(ax, 10, 40, 14, 10, "End user", NAVY, fs=8)
    for y in ys[:-1]:
        arrow(ax, (17, 40), (31, y), "", color=GREY, lw=0.7, style="-")
    box(ax, 90, 24, 15, 9, "Developer", PURPLE, fs=7.6)
    arrow(ax, (82.5, 24), (69, ys[11]), "", color=PURPLE, lw=0.9, style="-")
    box(ax, 90, 46, 15, 9, "Other client\n(API consumer)", ORANGE, fs=7)
    arrow(ax, (82.5, 46), (69, ys[10]), "", color=ORANGE, lw=0.9, style="-")
    ax.text(50, 1, "The webcam tab needs a browser camera permission; 'Open a saved result' is implemented as /app/history/[id] but no link in the UI points to it", ha="center", fontsize=6.0, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")


# ------------------------------------------------------------------ 09 ER diagram
def er():
    fig, ax = canvas(9.6, 5.0, 100, 52)
    ax.text(2, 49.5, "Entity-relationship diagram of mosaic.db (SQLite, 2 tables)", fontsize=8.8, fontweight="bold", color=NAVY)

    def table(x, y, w, name, cols, color=NAVY):
        lh = 2.7
        h = 3.8 + lh * len(cols) + 0.6
        ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
        ax.add_patch(Rectangle((x, y - 3.8), w, 3.8, fc=color, ec=NAVY, lw=1.3, zorder=3))
        ax.text(x + w / 2, y - 1.9, name, ha="center", va="center", color=WHITE, fontsize=8.6, fontweight="bold", zorder=4)
        for i, c in enumerate(cols):
            ax.text(x + 0.9, y - 3.8 - 1.7 - i * lh, c, fontsize=6.6, va="center", family="DejaVu Sans Mono", zorder=4)
        return h

    table(3, 45, 36, "users", ["PK id VARCHAR (uuid4)", "name VARCHAR NOT NULL", "email VARCHAR UNIQUE, INDEX", "password_hash VARCHAR", "created_at DATETIME"], BLUE)
    table(58, 45, 40, "analyses", ["PK id VARCHAR (uuid4)", "FK user_id -> users.id, INDEX", "created_at DATETIME", "face_detected BOOLEAN", "basic_emotions JSON  (7 items)", "compound_emotions JSON (11 items)", "dominant JSON (key, label,", "   confidence, kind) | NULL", "thumbnail_path VARCHAR | NULL"], PURPLE)
    arrow(ax, (39, 35), (58, 35), "1 : N", lo=(0, 1.8), fs=7.4, color=NAVY, lw=1.6)
    ax.text(41, 32, "cascade 'all, delete-orphan'\nin the ORM relationship", fontsize=6.4, color=GREY)
    box(ax, 28, 9.5, 48, 15, "", PALE_ORANGE, ec=ORANGE)
    ax.text(28, 15.5, "Design notes", ha="center", fontsize=7.2, fontweight="bold", color=ORANGE)
    ax.text(28, 8.6, "Emotion lists are stored as JSON documents, not as a normalised table:\none row per analysis keeps history reads to a single query.\nUploaded photos are never stored; only the cropped grayscale face is\nwritten to media/thumbs/<id>.jpg when a face was found.", ha="center", va="center", fontsize=6.2, linespacing=1.4)
    save(fig, OUT / "09_er_diagram.png")


# ------------------------------------------------------------------ 10 flowchart of the core algorithm
def flowchart():
    fig, ax = canvas(8.4, 9.8, 100, 117)
    ax.text(2, 114.5, "Flowchart: analyze_image_bytes() - the core inference algorithm", fontsize=8.8, fontweight="bold", color=NAVY)
    cx = 42
    steps = [
        (108, "box", "Image bytes received (multipart field 'image')", NAVY),
        (98, "box", "PIL decode -> RGB array -> BGR for OpenCV", BLUE),
        (88, "box", "Haar cascade: scaleFactor 1.1, minNeighbors 5, minSize 40x40", BLUE),
        (77, "dia", "any face found?", None),
        (66, "box", "keep the largest box (w*h); crop grayscale face", TEAL),
        (57, "box", "resize to 64x64; x/255; (x - 0.5)/0.5; shape 1x1x64x64", TEAL),
        (48, "box", "EmotionCNN(18) forward -> logits; sigmoid -> p[0..17]", TEAL),
        (39, "box", "basic list = p[0..6], compound list = p[7..17], each sorted desc", TEAL),
        (30, "box", "dominant = argmax p over all 18; kind = basic if index < 7", TEAL),
    ]
    for y, kind, t, col in steps:
        if kind == "box":
            box(ax, cx, y, 56, 6.2, t, col, fs=6.2)
        else:
            diamond(ax, cx, y, 34, 9, t, fs=6.8)
    ys = [s[0] for s in steps]
    kinds = [s[1] for s in steps]
    for i in range(len(steps) - 1):
        top = ys[i] - (3.1 if kinds[i] == "box" else 4.5)
        bot = ys[i + 1] + (3.1 if kinds[i + 1] == "box" else 4.5)
        arrow(ax, (cx, top), (cx, bot), "", color=NAVY, lw=1.1)
    ax.text(cx + 1.5, 71.6, "yes", fontsize=6.4, color=NAVY)
    box(ax, 86, 77, 24, 9, "no: return\nface_detected = false,\nempty lists, dominant null", ORANGE, fs=6.0)
    arrow(ax, (59, 77), (74, 77), "no", lo=(0, 1.4), fs=6.4, color=ORANGE)
    box(ax, cx, 19, 56, 8, "return (True, basic, compound, dominant, face crop)\nrouter builds AnalysisResponse; stores row + thumbnail if signed in", NAVY, fs=6.2)
    arrow(ax, (cx, 26.9), (cx, 23.0), "", color=NAVY, lw=1.1)
    arrow(ax, (86, 72.4), (70, 22), "", color=ORANGE, lw=1.1, rad=-0.15)
    box(ax, cx, 6, 56, 6.2, "UI: dominant card, basic bar chart, top-6 compound bars", PURPLE, fs=6.2)
    arrow(ax, (cx, 15), (cx, 9.1), "", color=NAVY, lw=1.1)
    save(fig, OUT / "10_flowchart_core_algorithm.png")


# ------------------------------------------------------------------ 11 flowchart of the training pipeline
def training():
    fig, ax = canvas(9.4, 8.6, 100, 91)
    ax.text(2, 88.5, "Flowchart: training pipeline (run_pipeline.py) - analysis by synthesis", fontsize=8.8, fontweight="bold", color=NAVY)
    box(ax, 50, 82, 46, 6, "Load FER2013 train (28,709) and test (7,178); decode, grayscale, resize 64", NAVY, fs=6.4)
    box(ax, 22, 68, 38, 10, "STAGE 1 backbone\nEmotionCNN(7), softmax CE with class weights\nAdam 1e-3, batch 256, 5 epochs\n-> stage1_backbone.pt (test acc 50.56 %)", BLUE, fs=6.1)
    box(ax, 78, 68, 38, 10, "STAGE 2 cEmoGAN\n400 real faces per class (2,800), one-hot condition\nAdam 2e-4, batch 64, 10 epochs, real label 0.9\n-> generator.pt", BLUE, fs=6.1)
    box(ax, 78, 50, 38, 10, "STAGE 3a synthesise compounds\n11 pairs x 200 faces, condition 0.5 / 0.5\ntarget = both basics + the compound bit\n= 2,200 images, 3 bits set each", TEAL, fs=6.1)
    box(ax, 50, 32, 52, 10, "STAGE 3b final classifier EmotionCNN(18)\nfeatures.* copied from the backbone; training set = 28,709 real\n(one basic bit) + 2,200 synthetic; BCEWithLogits, Adam 5e-4, 5 epochs", PURPLE, fs=6.2)
    diamond(ax, 50, 16, 34, 9, "classifier_final.pt\nsaved + log line", fs=6.5)
    box(ax, 50, 3.5, 56, 5, "API start-up loads the checkpoint; /api/health model_loaded = true", NAVY, fs=6.2)
    arrow(ax, (42, 79), (28, 73.2), "", color=NAVY)
    arrow(ax, (58, 79), (72, 73.2), "", color=NAVY)
    arrow(ax, (78, 62.8), (78, 55.2), "", color=NAVY)
    arrow(ax, (78, 44.8), (66, 37.2), "", color=NAVY)
    arrow(ax, (22, 62.8), (36, 37.2), "backbone init", lo=(-6, 2), fs=6.2)
    arrow(ax, (50, 26.8), (50, 20.6), "", color=NAVY)
    arrow(ax, (50, 11.4), (50, 6.1), "", color=NAVY)
    ax.text(3, 58, "Real faces are\nadded in 3b as\nbasic-only targets;\nthe test set has no\ncompound labels", fontsize=6.2, color=GREY, style="italic", va="center")
    save(fig, OUT / "11_flowchart_training.png")


if __name__ == "__main__":
    architecture(); workflow(); dfd0(); dfd1(); dfd2(); classes(); sequence(); usecase(); er(); flowchart(); training()
