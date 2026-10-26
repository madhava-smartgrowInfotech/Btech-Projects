"""Draw the VeriVision AI design diagrams into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: app/routes.py + app/api.py (routes), app/inference.py, app/ensemble.py,
app/explainability.py, app/robustness.py, app/preprocessing.py, app/models.py, scripts/common.py (training) and
scripts/evaluate.py. VeriVision has no relational database: its persisted state is model checkpoints, a metadata JSON
file and evaluation JSON/PNG artifacts, and the ER diagram shows exactly those.

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
    fig, ax = canvas(10, 8.6, 100, 86)
    panel(ax, 2, 68, 96, 17, "Presentation tier - React + Vite web app (port 5414)", PALE_BLUE, BLUE)
    box(ax, 17, 74, 26, 10, "Pages\nLanding - Login - Analyze\nInsights - Models - Status", BLUE, fs=7.6)
    box(ax, 44, 74, 24, 10, "lib/api.js, auth.jsx\nbearer token in browser,\nproxy /api /health /artifacts", BLUE, fs=7.4)
    box(ax, 68, 74, 20, 10, "UI kit\nRecharts - Framer Motion\nlight and dark theme", BLUE, fs=7.4)
    box(ax, 89, 74, 17, 10, "Classic pages\n/ /predict /insights\n(Jinja templates)", GREY, fs=7.2)

    panel(ax, 2, 47, 96, 19, "Application tier - Flask (port 8414, app/routes.py and app/api.py)", PALE_TEAL, TEAL)
    box(ax, 15, 54, 24, 11, "Status\nGET /health\nGET /api/config\nGET /api/insights", TEAL, fs=7.4)
    box(ax, 41, 54, 24, 11, "Demo sign-in\nPOST /api/auth/login\nGET /api/auth/me\nsigned 12 h token", TEAL, fs=7.4)
    box(ax, 67, 54, 24, 11, "Analysis\nPOST /api/analyze (token)\nPOST /api/predict (JSON)\nPOST /predict (HTML)", TEAL, fs=7.4)
    box(ax, 89, 54, 17, 11, "Guards\npng jpg jpeg webp\n10 MB, RGB decode\nJSON error handler", TEAL, fs=7.0)

    panel(ax, 2, 20, 96, 25, "Inference tier - PyTorch on CPU or GPU (app/inference.py, ensemble.py, explainability.py, robustness.py)", PALE_ORANGE, ORANGE)
    br = [("A1", "EfficientNet-B0\n224 px - CE"), ("A2", "EfficientNet-B0\n224 px - CE\ndistortion-hardened"),
          ("B", "ResNet50\n320 px - CE\nflip TTA"), ("C", "MobileNetV3-L\n224 px - focal")]
    for i, (n, d) in enumerate(br):
        box(ax, 11 + i * 16, 33.5, 14.5, 11.5, f"Route {n}\n{d}", ORANGE, fs=6.8)
    box(ax, 84, 36, 25, 6.5, "Logit fusion + dual gates\napp/ensemble.py", NAVY, fs=7.4)
    box(ax, 84, 27.5, 25, 6.5, "Grad-CAM + robustness variants\nexplainability.py, robustness.py", PURPLE, fs=7.0)
    ax.text(50, 23.0, "four logit pairs -> weighted sum -> softmax -> verdict, confidence, per-route votes, three Grad-CAM overlays, four robustness variants",
            ha="center", fontsize=7.4, color=INK)

    panel(ax, 2, 1.5, 96, 16.5, "Data tier - local files only (no relational database, nothing leaves the machine)", LIGHT, "#B7C3D3")
    store(ax, 15, 8, 25, 9, "models/*.pt\nefficientnet_a1 / a2\nresnet50_b, mobilenetv3_c", fs=7.0)
    store(ax, 41, 8, 22, 9, "models/\nmodel_metadata.json", fs=7.2)
    store(ax, 66, 8, 26, 9, "artifacts/metrics/\nmodel, ensemble, robustness\nJSON + confusion_matrix.png", fs=7.0)
    store(ax, 89, 8, 17, 9, "data/{train,val,test}\n/{real,fake}", fs=7.0)

    arrow(ax, (50, 68), (50, 66), "HTTP + JSON, multipart image upload", lo=(21, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 47), (50, 45), "Python calls", lo=(8, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 20), (50, 17.2), "load at start / read", lo=(11, 0), fs=7.2, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------------------------------------------------
def high_level_workflow():
    fig, ax = canvas(10, 5.8, 100, 58)
    ax.text(50, 55.3, "One image analysis, end to end (POST /api/analyze)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    top = [("Upload image", "drag and drop,\nbearer token", BLUE), ("Validate", "extension, 10 MB,\nnon-empty, decodes", BLUE),
           ("Preprocess", "RGB, resize to\n224 and 320 px", TEAL), ("Four routes", "A1, A2, B (+flip),\nC give logits", TEAL),
           ("Fuse", "weighted logit sum\n+ gate 1 + gate 2", TEAL)]
    xs = [10 + i * 20 for i in range(5)]
    for x, (t, d, c) in zip(xs, top):
        box(ax, x, 43, 16.5, 12, f"{t}\n{d}", c, fs=8)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.4, 43), (b - 8.4, 43), color=NAVY)
    bot = [("Verdict", "REAL / AI_GENERATED,\nconfidence word", PURPLE), ("Grad-CAM", "A1, B, C overlays\non the predicted class", PURPLE),
           ("Robustness", "original + JPEG,\nresize, blur re-run", PURPLE), ("Assemble JSON", "votes, gates,\nweights, device", NAVY),
           ("Show", "verdict card, tabs,\nheat-map selector", ORANGE)]
    bx = [90 - i * 20 for i in range(5)]
    for x, (t, d, c) in zip(bx, bot):
        box(ax, x, 15, 16.5, 12, f"{t}\n{d}", c, fs=8)
    for a, b in zip(bx[:-1], bx[1:]):
        arrow(ax, (a - 8.4, 15), (b + 8.4, 15), color=NAVY)
    arrow(ax, (xs[-1], 37), (bx[0], 21), color=NAVY)
    ax.text(50, 30, "the uploaded image never leaves the process; only RAM buffers are used", ha="center", fontsize=8, color=GREY, style="italic")
    ax.text(26, 5.2, "Models missing: /api/analyze answers 503 and the\nStatus page shows the missing checkpoints", ha="center", fontsize=7.6, color=ORANGE)
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------------------------------------------
def dfd0():
    fig, ax = canvas(10, 5.6, 100, 56)
    circle(ax, 50, 28, 13, "VeriVision AI\n(single process)", NAVY, fs=10)
    box(ax, 12, 40, 17, 9, "User\n(investigator, editor,\nstudent)", WHITE, tc=INK, ec=BLUE, fs=8, bold=True)
    box(ax, 12, 14, 17, 9, "Developer /\nadministrator", WHITE, tc=INK, ec=BLUE, fs=8, bold=True)
    box(ax, 88, 40, 17, 9, "Model files and\nmetric artifacts", WHITE, tc=INK, ec=TEAL, fs=8, bold=True)
    box(ax, 88, 14, 17, 9, "Image dataset\n(CIFAKE subset)", WHITE, tc=INK, ec=TEAL, fs=8, bold=True)
    arrow(ax, (20.5, 42), (38, 33), "image + demo login", lo=(-2, 3.5), fs=7.4, color=NAVY)
    arrow(ax, (38, 25), (20.5, 38), "verdict, confidence, votes,\nGrad-CAM, robustness", lo=(-9, -5.5), fs=7.4, color=ORANGE)
    arrow(ax, (20.5, 13), (38, 22), "training and evaluation\ncommands, settings", lo=(-5, -3), fs=7.4, color=NAVY)
    arrow(ax, (38, 20), (20.5, 11), "checkpoints, metrics", lo=(3, -3.2), fs=7.4, color=ORANGE)
    arrow(ax, (79.5, 40), (62, 33), "weights, metadata,\nevaluation JSON", lo=(2, 3.5), fs=7.4, color=TEAL)
    arrow(ax, (62, 22), (79.5, 15), "images in, trained\nmodels out", lo=(2, -3.5), fs=7.4, color=TEAL)
    ax.text(50, 4.5, "Context diagram (level 0). The only persisted state is files; there is no database.", ha="center", fontsize=8, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(10, 6.6, 100, 66)
    box(ax, 8, 55, 13, 8, "User", WHITE, tc=INK, ec=BLUE, fs=9, bold=True)
    box(ax, 8, 6, 13, 8, "Developer", WHITE, tc=INK, ec=BLUE, fs=9, bold=True)
    circle(ax, 30, 55, 7.2, "1.0\nValidate +\nauthenticate", BLUE, fs=7.4)
    circle(ax, 55, 55, 7.2, "2.0\nPreprocess +\nroute logits", TEAL, fs=7.4)
    circle(ax, 80, 55, 7.2, "3.0\nFuse and\ngate", TEAL, fs=7.4)
    circle(ax, 80, 32, 7.2, "4.0\nExplain\n(Grad-CAM)", PURPLE, fs=7.4)
    circle(ax, 55, 32, 7.2, "5.0\nRobustness\nre-check", PURPLE, fs=7.4)
    circle(ax, 30, 32, 7.2, "6.0\nReport\ninsights", ORANGE, fs=7.4)
    circle(ax, 55, 8.5, 7.0, "7.0\nTrain and\nevaluate", NAVY, fs=7.4)
    store(ax, 92, 8.5, 14, 7, "D1 model files", fs=7.0)
    store(ax, 92, 19, 14, 7, "D2 metadata", fs=7.0)
    store(ax, 30, 14, 20, 7, "D3 metric artifacts", fs=7.4)
    ax.text(50, 63.5, "Process 2.0 loads D1 weights and D2 metadata once, on the first request", ha="center", fontsize=7.6, color=GREY, style="italic")
    arrow(ax, (14.5, 55), (22.8, 55), "image, login", color=NAVY, lo=(0, 2.4), fs=7)
    arrow(ax, (37.2, 55), (47.8, 55), "RGB image", color=NAVY, lo=(0, 2.4), fs=7)
    arrow(ax, (62.2, 55), (72.8, 55), "4 logit pairs", color=NAVY, lo=(0, 2.4), fs=7)
    arrow(ax, (80, 47.8), (80, 39.2), "predicted class", color=NAVY, lo=(8, 0), fs=7)
    arrow(ax, (72.8, 32), (62.2, 32), "variants", color=NAVY, lo=(0, 2.4), fs=7)
    arrow(ax, (47.8, 32), (37.2, 32), "outcomes", color=NAVY, lo=(0, 2.4), fs=7)
    arrow(ax, (27, 39.2), (11, 50), "result JSON", color=ORANGE, lo=(-3, 2.2), fs=7)
    arrow(ax, (62, 9.5), (85, 9.2), "checkpoints", color=TEAL, lo=(0, 2.4), fs=7)
    arrow(ax, (62, 11.5), (85, 18), "metadata", color=TEAL, lo=(-2, 2.2), fs=7)
    arrow(ax, (47.8, 9.5), (40, 12.5), "metrics", color=TEAL, lo=(0, 2.2), fs=7)
    arrow(ax, (30, 17.5), (30, 24.8), "read", color=TEAL, lo=(3, 0), fs=7)
    arrow(ax, (14.5, 6.5), (47.8, 7.5), "commands", color=NAVY, lo=(0, -2.2), fs=7)
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(10, 6.4, 100, 64)
    ax.text(50, 61.2, "DFD level 2 - process 2.0 and 3.0 expanded (app/inference.py, app/ensemble.py)", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    circle(ax, 10, 47, 6.6, "2.1\nDecode and\nresize", BLUE, fs=6.8)
    circle(ax, 30, 47, 6.6, "2.2\nNormalise\n(ImageNet)", BLUE, fs=6.8)
    for i, (n, y) in enumerate((("2.3a  A1", 55), ("2.3b  A2", 47), ("2.3c  B + flip", 39), ("2.3d  C", 31))):
        circle(ax, 52, y, 4.6, n, TEAL, fs=6.0)
    circle(ax, 76, 47, 6.6, "3.1\nGate 1:\noutlier B", ORANGE, fs=6.8)
    circle(ax, 76, 25, 6.6, "3.2\nWeighted\nlogit sum", ORANGE, fs=6.8)
    circle(ax, 50, 12, 6.6, "3.3\nGate 2:\nB+C check", ORANGE, fs=6.8)
    circle(ax, 22, 12, 6.6, "3.4\nSoftmax\n+ wording", PURPLE, fs=6.8)
    box(ax, 12, 57, 14, 6.5, "D1 model files\n+ D2 metadata", TEAL, fs=6.8)
    box(ax, 92, 25, 12, 7, "config\nweights", GREY, fs=7)
    arrow(ax, (16.6, 47), (23.4, 47), "RGB", lo=(0, 2.3), fs=6.8, color=NAVY)
    for y in (55, 47, 39, 31):
        arrow(ax, (36.6, 47), (47.4, y), color=NAVY)
    for y in (55, 47, 39, 31):
        arrow(ax, (56.6, y), (70, 47 if y > 40 else 45), color=NAVY)
    ax.text(64, 55.5, "logit pairs", fontsize=7, color=INK)
    arrow(ax, (19, 57), (47.4, 55.5), "weights loaded once", lo=(-2, 2.2), fs=6.8, color=TEAL, ls="--")
    arrow(ax, (76, 40.4), (76, 31.6), "active\nbranches", lo=(6, 0), fs=6.8, color=NAVY)
    arrow(ax, (86, 25), (82.6, 25), color=GREY)
    arrow(ax, (71, 20), (55, 15), "fused logits", lo=(0, 2.6), fs=6.8, color=NAVY)
    arrow(ax, (43.4, 12), (28.6, 12), "adjusted\nlogits", lo=(0, 3.0), fs=6.8, color=NAVY)
    arrow(ax, (22, 5.4), (22, 2.2), color=ORANGE)
    ax.text(22, 0.6, "to 4.0 and the response: label, probabilities, confidence", fontsize=7.2, ha="center", color=ORANGE)
    save(fig, OUT / "05_dfd_level2.png")


# --------------------------------------------------------------------------------------------------
def uml_class_diagram():
    fig, ax = canvas(10, 9.6, 100, 96)
    uml_class(ax, 2, 94, 28, "FlaskApp", ["secret_key", "MAX_CONTENT_LENGTH"], ["create_app()", "errorhandler(413)"], hdr=NAVY, stereotype="factory")
    uml_class(ax, 35, 94, 30, "Routes (Blueprint main)", ["BRANCH_DISPLAY", "HEATMAP_NOTE"],
              ["index(), health()", "predict(), api_predict()", "insights(), confusion_png()", "_run_analysis()"], hdr=TEAL)
    uml_class(ax, 70, 94, 28, "Api (Blueprint /api)", ["BRANCH_INFO", "TOKEN_MAX_AGE"],
              ["login(), me()", "get_config(), insights()", "analyze()", "login_required()"], hdr=TEAL)
    uml_class(ax, 2, 68, 28, "Preprocessing", ["PreprocessingError"], ["allowed_extension()", "validate_upload()", "decode_image()", "save_temp_file()"], hdr=BLUE)
    uml_class(ax, 35, 68, 30, "Inference", ["_BRANCH_MODELS", "_DEVICE, _LOCK"],
              ["ensure_models_loaded()", "branch_logits()", "predict_image()", "predict_with_robustness()", "confidence_word()"], hdr=ORANGE)
    uml_class(ax, 70, 68, 28, "Ensemble", ["(pure functions)"],
              ["normalize_weights()", "fuse_logits()", "apply_gate1(), apply_gate2()", "ensemble_predict()", "softmax()"], hdr=ORANGE)
    uml_class(ax, 2, 40, 28, "Models", ["BUILDERS {a1,a2,b,c}"],
              ["build_efficientnet_b0()", "build_resnet50()", "build_mobilenetv3_large()", "load_branch_model()"], hdr=PURPLE)
    uml_class(ax, 35, 40, 30, "Explainability", ["target layer per branch"],
              ["generate_gradcam_overlay()", "pil_to_data_url()", "png_bytes_to_data_url()"], hdr=PURPLE)
    uml_class(ax, 70, 40, 28, "Robustness", ["(variants)"], ["make_variants()  jpeg q60,", "resize 1/2, blur 5x5"], hdr=PURPLE)
    uml_class(ax, 2, 18, 28, "Config", ["CLASS_NAMES, MODEL_FILES", "ENSEMBLE_WEIGHTS", "GATE_TAU_B/C, CORRECTION", "CONF_HIGH, CONF_MODERATE"], [], hdr=GREY, stereotype="module")
    uml_class(ax, 35, 18, 30, "Training (scripts)", ["FocalLoss, JpegCompress", "ImageFolderList"],
              ["train_one_model()", "evaluate.py main()"], hdr=GREY)
    ax.text(70, 17, "Arrows: uses (depends on).\nEvery module also reads Config.\nModules are Python files of functions,\ndrawn as classes to show their\nresponsibilities.", fontsize=7.4, color=GREY, va="top")
    ar = dict(color=NAVY, lw=1.1)
    arrow(ax, (30, 88), (35, 88), **ar)           # FlaskApp -> Routes
    arrow(ax, (70, 88), (65, 88), **ar)           # Api -> Routes (imports _run_analysis)
    arrow(ax, (50, 75.3), (50, 69.5), **ar)       # Routes -> Inference
    arrow(ax, (75, 75.3), (65, 70.5), **ar)       # Api -> Inference
    arrow(ax, (35, 59), (30, 59), **ar)           # Inference -> Preprocessing
    arrow(ax, (65, 59), (70, 59), **ar)           # Inference -> Ensemble
    arrow(ax, (50, 48.0), (50, 41.5), **ar)       # Inference -> Explainability
    arrow(ax, (38, 47.5), (28, 41.5), **ar)       # Inference -> Models
    arrow(ax, (62, 47.5), (72, 41.5), **ar)       # Inference -> Robustness
    arrow(ax, (40, 18), (22, 23.6), **ar)           # Training -> Models (reuses builders)
    save(fig, OUT / "06_uml_class.png")


def sequence_diagram():
    fig, ax = canvas(10, 8.2, 100, 82)
    ax.text(50, 79.5, "Sequence: analysing one image (POST /api/analyze)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    actors = [("Browser\n(React)", 8, BLUE), ("Flask\napi.py", 25, TEAL), ("Preprocessing", 42, BLUE), ("Inference", 59, ORANGE), ("Ensemble", 74, ORANGE), ("Grad-CAM +\nRobustness", 90, PURPLE)]
    for n, x, c in actors:
        box(ax, x, 73, 14, 6.5, n, c, fs=7.4)
        ax.plot([x, x], [69.5, 3], color="#B7C3D3", lw=1.2, ls="--", zorder=1)
    X = {n: x for n, x, _ in actors}
    steps = [
        ("Browser\n(React)", "Flask\napi.py", 65, "POST image + Bearer token", 0),
        ("Flask\napi.py", "Flask\napi.py", 61, "verify signed token", 1),
        ("Flask\napi.py", "Inference", 57.5, "ensure_models_loaded()", 0),
        ("Flask\napi.py", "Preprocessing", 53.5, "validate_upload(), decode_image()", 0),
        ("Flask\napi.py", "Inference", 49.5, "predict_image(rgb)", 0),
        ("Inference", "Inference", 46, "4 forward passes (B + flip)", 1),
        ("Inference", "Ensemble", 41, "ensemble_predict(logits)", 0),
        ("Ensemble", "Inference", 37.5, "fused logits, gates, probs", 2),
        ("Flask\napi.py", "Grad-CAM +\nRobustness", 33.5, "overlay for A1, B, C", 0),
        ("Flask\napi.py", "Grad-CAM +\nRobustness", 29, "predict on jpeg, resize, blur", 0),
        ("Grad-CAM +\nRobustness", "Flask\napi.py", 24.5, "overlays, consistency k/n", 2),
        ("Flask\napi.py", "Browser\n(React)", 20, "200 JSON  (or 400/401/413/500/503)", 2),
        ("Browser\n(React)", "Browser\n(React)", 14.5, "render verdict, tabs, heat-map selector", 1),
    ]
    for a, b, y, label, kind in steps:
        xa, xb = X[a], X[b]
        if kind == 1:
            ax.add_patch(Rectangle((xa - 1.2, y - 2), 2.4, 4, fc=PALE_BLUE, ec=BLUE, zorder=2))
            ax.text(xa + 2.5, y, label, fontsize=7.2, va="center", color=INK)
        else:
            arrow(ax, (xa, y), (xb, y), label, color=NAVY if kind == 0 else ORANGE, ls="-" if kind == 0 else "--", lo=(0, 1.9), fs=7.0, bg=True)
    ax.text(50, 6.5, "Every step runs in one request thread; model loading is guarded by a lock and happens once.", ha="center", fontsize=7.8, color=GREY, style="italic")
    save(fig, OUT / "07_sequence_analyze.png")


def use_case():
    fig, ax = canvas(10, 7.2, 100, 72)
    ax.add_patch(Rectangle((24, 6), 54, 64, fc="#F7F9FC", ec=NAVY, lw=1.4, zorder=1))
    ax.text(51, 67.2, "VeriVision AI", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ucs = [("Sign in (demo account)", 61), ("Upload an image", 54.7), ("View verdict and confidence", 48.4), ("Inspect per-route votes", 42.1),
           ("View Grad-CAM heat map", 35.8), ("Check robustness consistency", 29.5), ("Read model insights", 23.2), ("Check system status", 16.9),
           ("Train and evaluate models (scripts)", 10.6)]
    for t, y in ucs:
        ellipse(ax, 51, y, 38, 5.0, t, fs=7.8)
    for (nm, x, y, c) in (("User", 10, 40, BLUE), ("Developer", 92, 28, TEAL)):
        ax.add_patch(Circle((x, y + 6), 2.2, fc="white", ec=c, lw=1.6, zorder=3))
        ax.plot([x, x], [y + 3.8, y - 2], color=c, lw=1.6, zorder=3)
        ax.plot([x - 3, x + 3], [y + 1.5, y + 1.5], color=c, lw=1.6, zorder=3)
        ax.plot([x, x - 2.5], [y - 2, y - 7], color=c, lw=1.6, zorder=3)
        ax.plot([x, x + 2.5], [y - 2, y - 7], color=c, lw=1.6, zorder=3)
        ax.text(x, y - 9.5, nm, ha="center", fontsize=8.5, color=c, fontweight="bold")
    for t, y in ucs[:8]:
        arrow(ax, (14, 40), (32, y), color=BLUE, lw=0.9, style="-")
    for t, y in ucs[6:]:
        arrow(ax, (88, 28), (70, y), color=TEAL, lw=0.9, style="-")
    ax.text(51, 2.6, "Verdict, votes, Grad-CAM and robustness all depend on 'Upload an image' (include relationship)", fontsize=7.4, ha="center", color=GREY)
    save(fig, OUT / "08_use_case.png")


def er_diagram():
    fig, ax = canvas(10, 6.4, 100, 64)
    ax.text(50, 61, "Persisted data model - files, because VeriVision uses no relational database", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    ent = [
        (3, 57, 28, "ModelCheckpoint", ["PK path  models/<name>.pt", "branch  a1|a2|b|c", "state_dict", "best_val_f1", "history", "route, resolution"], PURPLE),
        (36, 57, 28, "ModelMetadata", ["PK model_name", "branch", "training_dataset", "image_resolution", "class_mapping 0/1", "FK checkpoint_path", "validation {acc,f1,auc}"], TEAL),
        (69, 57, 28, "MetricsArtifact", ["PK file  (model|ensemble|", "   robustness)_metrics.json", "accuracy, precision, recall", "f1, roc_auc, balanced_acc", "confusion_matrix, n_samples", "dataset, seed"], ORANGE),
    ]
    boxes = {}
    for x, y, w, name, attrs, c in ent:
        boxes[name] = uml_class(ax, x, y, w, name, attrs, [], hdr=c, fs=7.4)
    e2 = [
        (3, 25, 28, "ImageSample", ["PK path  data/<split>/<cls>/", "split  train|val|test", "label  0 REAL | 1 FAKE"], BLUE),
        (36, 25, 28, "SessionToken", ["email", "iat (issue time)", "signed, 12 h max age", "(stateless, not stored)"], GREY),
        (69, 25, 28, "UploadBuffer", ["bytes (RAM only)", "ext, size <= 10 MB", "decoded RGB image", "(discarded after reply)"], GREY),
    ]
    for x, y, w, name, attrs, c in e2:
        boxes[name] = uml_class(ax, x, y, w, name, attrs, [], hdr=c, fs=7.4)
    arrow(ax, (31, 48), (36, 48), "1 : 1", lo=(0, 2), fs=7.4, color=NAVY, style="-")
    arrow(ax, (64, 48), (69, 48), "n : 1", lo=(0, 2), fs=7.4, color=NAVY, style="-")
    arrow(ax, (17, 24), (17, 33.5), "trains", lo=(5, 0), fs=7.4, color=NAVY, style="-|>")
    ax.text(50, 6.0, "ModelMetadata.checkpoint_path points at a ModelCheckpoint; MetricsArtifact rows are produced by evaluate.py from ImageSample test rows.\n"
            "SessionToken and UploadBuffer are runtime objects: they exist only inside a request and are never persisted.", ha="center", fontsize=7.4, color=GREY)
    save(fig, OUT / "09_er_diagram.png")


def flowchart():
    fig, ax = canvas(10, 9.0, 100, 90)
    ax.text(50, 87, "Core algorithm - logit fusion with dual gating (app/ensemble.py)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    box(ax, 50, 81, 36, 5.5, "Input: logit pairs z_a1, z_a2, z_b, z_c  (each [real, fake])", NAVY, fs=7.8)
    box(ax, 50, 73.5, 36, 5.5, "Normalise weights w = {0.35, 0.15, 0.25, 0.25}", BLUE, fs=7.8)
    diamond(ax, 50, 64.5, 40, 9, "Gate 1: B margin >= tau_b (2.5)\nand all 3 others disagree?", fs=7.6)
    box(ax, 86, 64.5, 23, 7.5, "Exclude route B,\nrenormalise remaining weights", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.4)
    box(ax, 50, 52.5, 36, 5.5, "fused = sum_i w_i * z_i   (still logits)", TEAL, fs=7.8)
    diamond(ax, 50, 42.5, 44, 9.5, "Gate 2: B and C agree, both margins >= 2.5,\nand fused direction differs?", fs=7.4)
    box(ax, 86, 42.5, 23, 8.5, "Nudge fused logits by 0.75\ntoward the B+C class\n(other class -0.375)", PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.2)
    box(ax, 50, 30, 36, 5.5, "probs = softmax(fused);  label = argmax", TEAL, fs=7.8)
    box(ax, 50, 22, 36, 5.5, "confidence = max(probs):  >=0.85 High, >=0.60 Moderate, else Low", PURPLE, fs=7.2)
    box(ax, 50, 14, 36, 5.5, "agreement = number of routes whose own label equals the final label", PURPLE, fs=7.2)
    box(ax, 50, 6, 36, 5.5, "Output: label, probs, confidence word, gate notes, active weights", NAVY, fs=7.6)
    for y1, y2 in ((78.2, 76.3), (70.7, 69.0), (60, 55.3), (49.7, 47.3), (37.7, 32.8), (27.2, 24.8), (19.2, 16.8), (11.2, 8.8)):
        arrow(ax, (50, y1), (50, y2), color=NAVY)
    arrow(ax, (70, 64.5), (74.5, 64.5), color=ORANGE)
    ax.text(71, 66.2, "yes", fontsize=7.4, color=ORANGE)
    ax.text(51.5, 59.2, "no / after exclusion", fontsize=7.2, color=GREY)
    arrow(ax, (86, 60.7), (63, 54.6), color=ORANGE)
    arrow(ax, (72, 42.5), (74.5, 42.5), color=ORANGE)
    ax.text(72.2, 44.2, "yes", fontsize=7.4, color=ORANGE)
    ax.text(51.5, 36.8, "no / after nudge", fontsize=7.2, color=GREY)
    arrow(ax, (86, 38.2), (68, 31.5), color=ORANGE)
    save(fig, OUT / "10_flowchart_ensemble.png")


def training_pipeline():
    fig, ax = canvas(10, 5.6, 100, 56)
    ax.text(50, 53.2, "Training and evaluation pipeline (scripts/)", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    row1 = [("prepare_dataset /\nprepare_cifake", "stratified train, val,\ntest folders", BLUE), ("train_a1/a2/b/c", "ImageNet weights,\nupper blocks unfrozen", TEAL),
            ("Augmentation", "route-specific: crop, flip,\nblur, noise, JPEG", TEAL), ("Optimiser", "AdamW, cosine decay,\nCE or focal loss", TEAL)]
    xs = [13, 37, 61, 85]
    for x, (t, d, c) in zip(xs, row1):
        box(ax, x, 38, 20, 12, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 10.2, 38), (b - 10.2, 38), color=NAVY)
    row2 = [("Early stopping", "best validation F1,\npatience 3", ORANGE), ("models/*.pt", "state_dict + history", NAVY),
            ("evaluate.py", "held-out test: branches,\nensemble, degraded", PURPLE), ("artifacts/metrics", "JSON + confusion matrix\nread by /api/insights", PURPLE)]
    xs2 = [85, 61, 37, 13]
    for x, (t, d, c) in zip(xs2, row2):
        box(ax, x, 14, 20, 12, f"{t}\n{d}", c, fs=7.6)
    for a, b in zip(xs2[:-1], xs2[1:]):
        arrow(ax, (a - 10.2, 14), (b + 10.2, 14), color=NAVY)
    arrow(ax, (85, 32), (85, 20), color=NAVY)
    save(fig, OUT / "11_training_pipeline.png")


if __name__ == "__main__":
    from matplotlib.patches import Circle, Rectangle  # noqa: F401  (used by use_case / sequence)
    for fn in (system_architecture, high_level_workflow, dfd0, dfd1, dfd2, uml_class_diagram, sequence_diagram, use_case, er_diagram, flowchart, training_pipeline):
        fn()
