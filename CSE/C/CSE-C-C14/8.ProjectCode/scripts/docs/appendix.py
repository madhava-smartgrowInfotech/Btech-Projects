"""Appendices A (important code), B (installation and user guide) and C (additional screens) of the VeriVision AI report."""

import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB

SH = F.shot


def src(rel, start, end):
    """Lines start..end (1-based, inclusive) of a project file, exactly as in the repository."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    return "\n".join(lines[start - 1:end])


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from `8.ProjectCode` in the state in which the results of this report were measured; docstrings and comments are unchanged and the line ranges are whole statements."),
        H2("A.1 Upload validation and decoding (`app/preprocessing.py`)"),
        P("An upload is rejected before any model runs if it has no name, an unsupported extension, no bytes or too many bytes; `decode_image` (same file) then verifies the file, converts it to RGB and refuses images under 8 pixels."),
        CODE(src("app/preprocessing.py", 28, 45), 7),
        H2("A.2 Running the four routes (`app/inference.py`)"),
        P("Route B averages the logits of the image and its horizontal flip; each route receives the image at its own resolution and returns raw logits, never probabilities."),
        CODE(src("app/inference.py", 69, 87), 7),
        H2("A.3 Weighted logit fusion and the two gates (`app/ensemble.py`)"),
        P("The core of the system. Gate 1 drops route B when it is confident and all other routes disagree; Gate 2 nudges the fused logits toward a confident B and C consensus. On the CIFAKE test set Gate 1 fired on 7 images and Gate 2 on none."),
        CODE(src("app/ensemble.py", 50, 70), 7),
        CODE(src("app/ensemble.py", 73, 102), 7),
        CODE(src("app/ensemble.py", 105, 129), 7),
        H2("A.4 Grad-CAM (`app/explainability.py`)"),
        CODE(src("app/explainability.py", 38, 57), 7),
        H2("A.5 Robustness variants (`app/robustness.py`)"),
        CODE(src("app/robustness.py", 9, 34), 7),
        H2("A.6 The analyze endpoint (`app/api.py`)"),
        CODE(src("app/api.py", 115, 140), 7),
        H2("A.7 The training loop (`scripts/common.py`)"),
        P("Every route is trained by this loop: AdamW with cosine decay, early stopping on the validation F1, and the best state restored at the end. Route C swaps the cross-entropy criterion for the focal loss of the same file."),
        CODE(src("scripts/common.py", 195, 243), 7),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11 (64-bit) with Python 3.10 or newer (3.11.9 was used for every measurement) and, for the web app, Node.js 20 or newer. About 3 GB of free disk space. No GPU is required: the application uses CUDA when it is available and the CPU otherwise.",
          "Python packages are pinned in `requirements.txt`: Flask 3.1.3, torch 2.14.1, torchvision 0.29.1, Pillow 13.0.0, numpy 2.4.6, pandas 3.0.6, scikit-learn 1.9.1, matplotlib 3.11.2, opencv-python-headless 5.0.0.93, grad-cam 1.5.7, pytest 9.1.1, requests 2.34.2.",
          "Docker Desktop is optional (`docker compose up --build`, or `run-docker.bat`); the trained files in `models/` and `artifacts/` must already exist because they are mounted into the container."),
        H2("B.2 One-click start"),
        N("Open the project folder and double-click `run.bat`.",
          "The script checks Python, creates `.venv`, installs `requirements.txt`, copies `.env.example` to `.env` if needed, installs the web packages (`frontend/node_modules`, one-time) and starts two windows: the API on `http://localhost:8414` and the web app on `http://localhost:5414`.",
          "If `models/efficientnet_a1.pt` is missing, `run.bat` prepares the data and trains the models first (one-time; slow on a CPU).",
          f"The browser opens the web app. Choose Sign in, then Use demo account (`{F.DEMO_EMAIL}` / `{F.DEMO_PASSWORD}`).",
          "To stop, close the two server windows."),
        H2("B.3 Manual commands"),
        P("To start the application by hand (Windows command prompt, from the project folder):"),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate.bat\npython -m pip install -r requirements.txt\n.venv\\Scripts\\python.exe run.py          (API, port 8414)\ncd frontend && npm install && npm run dev   (web app, port 5414)", 8.5),
        P("To reproduce the results of Chapter 8 on the CIFAKE subset (the data are downloaded from the Hugging Face mirror named in `scripts/prepare_cifake.py`; the cross-domain shards go into `data/xdomain_raw/` first):"),
        CODE("python scripts/prepare_cifake.py --train-per-class 3000 --val-per-class 600 --test-per-class 1000\n"
             "python scripts/prepare_xdomain.py\n"
             "scripts\\train_chain_cifake.bat        (trains A1, C, A2 for 5 epochs and B for 3 epochs into models\\cifake)\n"
             "python scripts/publish_cifake_models.py\n"
             "python scripts/run_cifake_experiments.py     (writes experiments/cifake/metrics.json)\n"
             "python scripts/docs_build/make_figures.py    (charts in docs/figures)\n"
             "python scripts/measure_latency.py            (API running; writes docs/metrics/latency.json)\n"
             "python -m pytest tests\n"
             "python scripts/smoke_test.py\n"
             "python scripts/capture_screens.py            (both servers running; screenshots in docs/screenshots)", 8),
        H2("B.4 Using the application"),
        N("Open the landing page and select Sign in. Sign in with the demo account; the token is a signed value that expires after 12 hours.",
          "On Analyze image, drop a PNG, JPG/JPEG or WEBP file (at most 10 MB) or click the upload area, check the preview and press Analyze image.",
          "Read the verdict card: the verdict wording, the confidence word (High at 85% or more, Moderate at 60% or more, otherwise Low), the Real / AI-generated split and the number of agreeing routes.",
          "Open Branch votes to see each route's label, confidence and fusion weight, and Robustness check to see whether the verdict survives JPEG, resizing and blur. A consistency below full agreement means the result needs extra caution.",
          "Open the Grad-CAM tabs (EfficientNet, ResNet50, MobileNetV3) to see where each route looked. The heat map is an explanation aid, not proof of authenticity.",
          "Model insights shows the measured held-out performance; How it works shows the four routes; System status shows the answer of `/health` and the upload rules."),
        H2("B.5 Interface summary"),
        TAB("HTTP interface of the application (API on port 8414)", ["Method and path", "Purpose", "Notes"],
            [["`GET /health`", "Liveness and model status", "models_loaded, device, error"],
             ["`GET /api/config`", "Routes, weights, gate and confidence settings, metadata", "Public"],
             ["`GET /api/insights`", "Evaluation metrics shown on the insights page", "Public"],
             ["`POST /api/auth/login`", "Demo sign-in, returns a signed bearer token", "401 for a wrong login"],
             ["`GET /api/auth/me`", "Current user from the token", "401 without a token"],
             ["`POST /api/analyze`", "Full analysis: verdict, votes, Grad-CAM, robustness", "Token required; field `image`; 400, 401, 413, 500, 503"],
             ["`POST /api/predict`", "JSON verdict without the token", "Same contract as the original server"],
             ["`GET /`, `POST /predict`, `GET /insights`", "Original server-rendered pages", "Kept unchanged on port 8414"]],
            widths=[2.0, 2.7, 1.9], align=["l", "l", "l"], size=9.5),
        TAB("Settings in `.env` (defaults shown)", ["Variable", "Default", "Meaning"],
            [["`VERIVISION_PORT`", "8414", "API port"], ["`FRONTEND_PORT`", "5414", "Web app port"], ["`VERIVISION_MAX_UPLOAD_MB`", "10", "Upload limit"],
             ["`VERIVISION_DEMO_EMAIL` / `_PASSWORD`", f"{F.DEMO_EMAIL} / {F.DEMO_PASSWORD}", "Demo sign-in"],
             ["`VERIVISION_W_A1`, `_A2`, `_B`, `_C`", "0.35, 0.15, 0.25, 0.25", "Fusion weights (normalised at load)"],
             ["`VERIVISION_GATE_TAU_B`, `_TAU_C`, `_CORRECTION`", "2.5, 2.5, 0.75", "Gate thresholds and nudge"],
             ["`VERIVISION_EPOCHS`, `VERIVISION_BATCH`", "8, 32", "Training knobs for the default scripts"]],
            widths=[2.6, 1.9, 2.1], align=["l", "l", "l"], size=9.5),
        H2("B.6 Troubleshooting"),
        B("**The web app cannot reach the API.** Start the API window (`.venv\\Scripts\\python.exe run.py`) and press Try again.",
          "**Port already in use.** Change `VERIVISION_PORT` or `FRONTEND_PORT` in `.env` and restart.",
          "**Model files missing (503).** Run the training steps of B.3 or re-run `run.bat`; the System status page names the missing files.",
          "**Fake-data warning.** If `prepare_dataset.py` cannot download the public data it falls back to clearly labelled synthetic demo images; metrics from such models are not meaningful."),
    ]


def screens_blocks():
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("Chapter 8 shows the main flow. The screens below complete the set: the dark theme, the upload states, the page captured while its numbers were still counting up, and the two landing-page sections that quote the measured results."),
        PAIR([(SH("02_landing_dark.png"), "Landing page in the dark theme: the same ensemble card and feature strip; the theme is switched with the button at the top right."),
              (SH("14_insights_dark.png"), "Model insights page in the dark theme: the same measured values as the light page of Chapter 8.")], 3.15),
        PAIR([(SH("04_analyze_empty.png"), "Analyze page after sign-in, before an image is chosen; the toast confirms \"Signed in, Welcome, Demo User\"."),
              (SH("05_analyze_ready.png"), "`fake_00000.png` (2.6 KB) selected: file name, size, remove button and a preview appear, and the Analyze button is enabled.")], 3.15),
        FIG(SH("06_analyze_running.png"), "Result page captured while the headline confidence was still counting up: it reads 88.33% beside a bar already at Real 0.8% / AI-generated 99.2%; the settled value is 99.25% (Chapter 8). The file keeps the name `06_analyze_running.png` from the capture script.", F.shot_w(SH("06_analyze_running.png"), 5.0, 3.0)),
        PAIR([(SH("15_landing_features.png"), "Landing page, features: four-model ensemble, Grad-CAM, robustness check, runs locally, CPU or GPU, and honest about limits."),
              (SH("16_landing_numbers.png"), "Landing page, numbers: accuracy 92.3%, F1 92.7%, ROC-AUC 98.7%, 2,000 test images and 61.0% after a 2x resample, with the \"what it cannot do\" box.")], 3.15),
        P("The landing page rounds the measured values to one decimal (92.35% is shown as 92.3% and 92.75% as 92.7%) and quotes the accuracy after a 2x resample (61.0%) next to the headline figures, so the weakest result is visible before sign-in."),
    ]
