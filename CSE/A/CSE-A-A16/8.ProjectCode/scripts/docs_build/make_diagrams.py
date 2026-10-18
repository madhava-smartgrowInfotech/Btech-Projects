"""Draw every design diagram for the SignSpeak documents into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: backend/main.py (routes), backend/train_job.py, and sign_language_app/*.
    python scripts/docs_build/make_diagrams.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------------------------------
def system_architecture():
    fig, ax = canvas(10, 7.4, 100, 74)
    panel(ax, 2, 55, 96, 18, "Presentation tier - browser (React 18 + TypeScript + Vite, port 5316)", PALE_BLUE, BLUE, tc=NAVY)
    box(ax, 15, 61, 25, 10, "Seven pages\nLanding - Dashboard - Recognize\nCollect - Train - Model - About", BLUE, fs=8.3)
    box(ax, 42, 61, 25, 10, "Camera hook (getUserMedia)\ncover-crop 16:9, mirror\n960x540 JPEG per frame", BLUE, fs=8.3)
    box(ax, 69, 61, 25, 10, "Data layer\nTanStack Query - axios\nsentence builder - charts", BLUE, fs=8.3)
    box(ax, 91, 61, 12, 10, "Browser\nvoice\nfallback", BLUE, fs=8.3)

    panel(ax, 2, 32, 96, 20, "Application tier - FastAPI (backend/, port 8316, all routes under /api)", PALE_TEAL, TEAL, tc=NAVY)
    box(ax, 13, 43.6, 20, 9.6, "Meta and data\n/health  /config\n/about  /dataset\n/dataset/{cls}/images", TEAL, fs=7.8)
    box(ax, 35, 43.6, 20, 9.6, "Capture\n/preview\n/collect/{cls}", TEAL, fs=7.8)
    box(ax, 57, 43.6, 20, 9.6, "Recognition\n/recognize/session\n/recognize/frame\n/recognize/reload", TEAL, fs=7.8)
    box(ax, 79, 43.6, 20, 9.6, "Training and report\n/train/start|stop|status\n/model   /tts/speak", TEAL, fs=7.8)
    box(ax, 28, 35.3, 46, 3.8, "Session store: up to 20 SignRecognizer objects + one model lock", WHITE, tc=INK, ec=TEAL, fs=7.8)
    box(ax, 76, 35.3, 40, 3.8, "TrainJob: background thread, stop flag, progress", WHITE, tc=INK, ec=TEAL, fs=7.8)

    panel(ax, 2, 12, 96, 17, "Domain tier - sign_language_app (the original desktop modules, reused unchanged)", PALE_ORANGE, ORANGE, tc=NAVY)
    mods = [("preprocessing", "ROI, gray, blur\nOtsu, 64x64"), ("model", "build_cnn()\n3 conv blocks"), ("dataset", "load, 70/15/15\nstratified split"),
            ("train", "Adam, augment\nearly stopping"), ("recognizer", "vote, stable\nauto-commit"), ("tts", "pyttsx3\n(SAPI5)"), ("config", "paths, sizes\nthresholds")]
    for i, (n, d) in enumerate(mods):
        box(ax, 9.5 + i * 13.5, 19.5, 12.3, 9, f"{n}\n{d}", ORANGE, fs=7.6)

    store(ax, 28, 4.2, 48, 5.2, "data/<CLASS>/*.png|jpg   (training images, 29 folders)", PALE_TEAL, TEAL, fs=7.8)
    store(ax, 76, 4.2, 40, 5.2, "models/  asl_cnn_model.keras - labels.json\ntraining_history - report - confusion matrix", PALE_TEAL, TEAL, fs=7.0)

    arrow(ax, (45, 55), (45, 52), "HTTP + JSON + multipart JPEG (Vite proxies /api)", lo=(24, 0), fs=7.8, color=NAVY)
    arrow(ax, (45, 32), (45, 29), "Python calls", lo=(9, 0), fs=7.8, color=NAVY)
    arrow(ax, (28, 12), (28, 7), None, color=NAVY)
    arrow(ax, (76, 12), (76, 7), None, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 5.6, 100, 56)
    top = [("Camera frame", "960x540,\nmirrored JPEG", BLUE), ("ROI crop", "300x300 box\nx 620-920, y 90-390", BLUE), ("Grayscale", "BGR to\nsingle channel", TEAL),
           ("Gaussian blur", "7x7 kernel\nnoise reduction", TEAL), ("Otsu threshold", "hand silhouette\n+ open / close", TEAL), ("Normalise", "resize 64x64\nscale to [0, 1]", TEAL)]
    xs = [8.6 + i * 16.5 for i in range(6)]
    for x, (t, d, c) in zip(xs, top):
        box(ax, x, 44, 14.4, 12, f"{t}\n{d}", c, fs=8.2)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.1, 44), (b - 7.1, 44), color=NAVY)
    ax.text(50, 53.5, "Per-frame image pipeline (identical for collection, training and live recognition)", ha="center", fontsize=10, color=NAVY, fontweight="bold")

    bot_x = [7.5 + i * 14.2 for i in range(7)]
    box(ax, bot_x[0], 14, 12.2, 12, "CNN\n3 conv blocks\n+ dense 256", PURPLE, fs=8)
    box(ax, bot_x[1], 14, 12.2, 12, "Softmax\n29 classes", PURPLE, fs=8.2)
    diamond(ax, bot_x[2], 14, 13.6, 14, "confidence\n>= 0.75 ?", fs=7.6)
    box(ax, bot_x[3], 14, 12.2, 12, "Majority vote\nlast 15\nframes", NAVY, fs=8)
    diamond(ax, bot_x[4], 14, 13.6, 14, "held for\n18 frames ?", fs=7.6)
    box(ax, bot_x[5], 14, 12.2, 12, "Commit\nletter / space\n/ del", NAVY, fs=8)
    box(ax, bot_x[6], 14, 12.2, 12, "Sentence\nthen speech\n(pyttsx3)", ORANGE, fs=8)
    # snake connector from end of row 1 to start of row 2
    ax.plot([xs[-1], xs[-1]], [38, 28], color=NAVY, lw=1.5, zorder=4)
    ax.plot([xs[-1], bot_x[0]], [28, 28], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (bot_x[0], 28), (bot_x[0], 20), color=NAVY)
    for a, b in zip(bot_x[:-1], bot_x[1:]):
        arrow(ax, (a + (6.9 if a in (bot_x[2], bot_x[4]) else 6.2), 14), (b - (6.9 if b in (bot_x[2], bot_x[4]) else 6.2), 14), color=NAVY)
    ax.text(bot_x[2], 4.2, "no: label becomes 'nothing'", ha="center", fontsize=7.8, color=ORANGE)
    ax.text(bot_x[4], 4.2, "no: keep counting", ha="center", fontsize=7.8, color=ORANGE)
    ax.text(50, 24.5, "Decision logic (SignRecognizer.predict_frame)", ha="right", fontsize=9.5, color=NAVY, fontweight="bold")
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(9, 5.6, 100, 62)
    circle(ax, 50, 31, 12.5, "0\nSignSpeak\nsystem", BLUE, fs=11)
    box(ax, 10, 31, 15, 9, "User", WHITE, tc=INK, ec=NAVY, fs=11, bold=True)
    box(ax, 50, 57, 21, 7, "Webcam (browser)", WHITE, tc=INK, ec=NAVY, fs=10, bold=True)
    box(ax, 90, 31, 15, 9, "Speaker", WHITE, tc=INK, ec=NAVY, fs=11, bold=True)
    box(ax, 50, 5, 30, 8, "Sample image source\n(own captures / public ASL set)", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    arrow(ax, (17.5, 34), (37.6, 33.5), "class choice, hyper-parameters,\ncommands, edits", lo=(0, 4.2), fs=8)
    arrow(ax, (37.6, 28.5), (17.5, 28), "letters, sentence, charts,\nreports, status messages", lo=(0, -4.6), fs=8)
    arrow(ax, (50, 53.4), (50, 43.5), "video frames", lo=(8, 0), fs=8.5)
    arrow(ax, (62.5, 31), (82.5, 31), "speech audio", lo=(0, 2.4), fs=8.5)
    arrow(ax, (50, 9), (50, 18.5), "labelled hand images", lo=(11, 0), fs=8.5)
    save(fig, OUT / "03_dfd_level0.png")


# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
def er_diagram():
    fig, ax = canvas(10, 6.2, 100, 62)
    ax.text(50, 59.5, "No SQL database: the data model is the file system (folders and files) plus in-memory sessions", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")

    def entity(cx, cy, w, title, rows, fc=NAVY):
        h = 5 + 3.0 * len(rows)
        ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc=WHITE, ec=NAVY, lw=1.4, zorder=2))
        ax.add_patch(Rectangle((cx - w / 2, cy + h / 2 - 5), w, 5, fc=fc, ec=NAVY, lw=1.4, zorder=3))
        ax.text(cx, cy + h / 2 - 2.5, title, ha="center", va="center", color=WHITE, fontsize=9.2, fontweight="bold", zorder=4)
        for i, r in enumerate(rows):
            ax.text(cx - w / 2 + 1.2, cy + h / 2 - 5 - 1.8 - 3.0 * i, r, ha="left", va="center", fontsize=7.6, zorder=4, family="DejaVu Sans Mono")
        return h

    entity(15, 40, 26, "CLASS_FOLDER", ["PK class_name  A-Z|space|del|nothing", "   path  data/<class_name>/", "   image_count (derived)"], BLUE)
    entity(50, 40, 28, "IMAGE_FILE", ["PK file_name   <C>_<ms>.png|.jpg", "FK class_name", "   format  PNG (own) | JPG (Kaggle)", "   size    200x200 colour"], BLUE)
    entity(85, 40, 28, "TRAINING_RUN", ["PK run (latest overwrites)", "   epochs, batch_size, lr", "   split 70 / 15 / 15, seed 42", "   test_accuracy, test_loss", "   history, report, confusion"], TEAL)
    entity(85, 12.5, 28, "MODEL_ARTEFACT", ["PK asl_cnn_model.keras", "   labels.json  (class order)", "   trained_at (file mtime)"], TEAL)
    entity(50, 12.5, 28, "RECOGNITION_SESSION", ["PK session_id (12 hex)", "   history  deque(15)", "   stable_label, stable_count", "   (memory only, max 20)"], PURPLE)
    entity(15, 12.5, 26, "PREDICTION", ["   label, confidence", "   stable_label", "   committed letter | None", "   (transient, per frame)"], PURPLE)

    arrow(ax, (28, 40), (36, 40), "1 : N", style="-", lo=(0, 1.8), fs=8.5, color=NAVY)
    arrow(ax, (64, 40), (71, 40), "N : 1", style="-", lo=(0, 1.8), fs=8.5, color=NAVY)
    ax.text(67.5, 36.9, "reads", ha="center", fontsize=7.8)
    arrow(ax, (85, 26.7), (85, 19.2), None, style="-", color=NAVY)
    ax.text(86, 23, "1 : 1  produces", fontsize=7.8, ha="left")
    arrow(ax, (64, 12.5), (71, 12.5), "N : 1  uses", style="-", lo=(0, 1.8), fs=7.8, color=NAVY)
    arrow(ax, (37, 12.5), (28, 12.5), "1 : N", style="-", lo=(0, 1.8), fs=8.5, color=NAVY)
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    from diagrams_more import all_more

    system_architecture()
    high_level_workflow()
    dfd0()
    er_diagram()
    all_more()
