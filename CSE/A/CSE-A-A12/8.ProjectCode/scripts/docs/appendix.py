"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

import os
import re

from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from . import facts as F


def source(rel, start, end=None, strip_docstring=False):
    """Return the text of a source file from the line containing `start` up to (not including) the line containing `end`."""
    path = os.path.join(F.CODE, rel)
    lines = open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    a = next(i for i, l in enumerate(lines) if start in l)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i])
    chunk = lines[a:b]
    while chunk and not chunk[-1].strip():
        chunk.pop()
    return "\n".join(chunk)


def code_blocks():
    s = source
    out = [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings below are extracted from the repository by the document build script, so they are the code that was tested and measured. "
          "File paths are relative to `8.ProjectCode`."),
        H2("A.1 Preprocessing (`model/preprocess.py`)"),
        CODE(s("model/preprocess.py", "def apply_clahe", "def preprocess_for_display")),
        H2("A.2 Network definition (`model/model_builder.py`)"),
        CODE(s("model/model_builder.py", "def build_custom_cnn", "def build_transfer_model")),
        CODE(s("model/model_builder.py", "def find_last_conv_layer")),
        H2("A.3 Grad-CAM (`model/gradcam.py`)"),
        CODE(s("model/gradcam.py", "def make_gradcam_heatmap")),
        H2("A.4 Database layer (`database/db.py`)"),
        CODE(s("database/db.py", "def init_db", "def get_prediction")),
        H2("A.5 Session tokens and login (`backend/main.py`)"),
        CODE(s("backend/main.py", "def _sign", "class Login")),
        CODE(s("backend/main.py", '@api.post("/api/auth/login")', '@api.post("/api/auth/logout")')),
        H2("A.6 Prediction route (`backend/main.py`)"),
        CODE(s("backend/main.py", '@api.post("/api/predict"', '@api.get("/api/predictions")')),
        H2("A.7 Training and evaluation (`scripts/train_experiment.py`)"),
        P("The data split, the augmentation generator, class weights and the fit call:"),
        CODE(s("scripts/train_experiment.py", "    if args.protocol == \"official\":", "    # how many test images share a patient id")),
        CODE(s("scripts/train_experiment.py", "    aug = ImageDataGenerator(", "    ckpt = os.path.join")),
    ]
    return out


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Windows 10 or 11, Python 3.10 or 3.11 on PATH, Node.js 18 or newer on PATH.",
          "About 2 GB of disk space for the Python environment (TensorFlow) and a modern browser."),
        H2("B.2 One-click start"),
        N("Open the folder `8.ProjectCode` and double-click `run.bat`, or run it from a terminal in that folder.",
          "On the first run it creates `.venv`, installs `requirements.txt` and `requirements-api.txt` (several minutes), and runs `npm install` in `frontend/`.",
          "Two console windows open, **PneumoDetect API** (port 8312) and **PneumoDetect UI** (port 5312), and the browser opens http://localhost:5312.",
          "Wait about twenty seconds on the very first request while TensorFlow loads the model.",
          "Stop everything with `stop.bat` or by closing the two windows."),
        P("The ports and the demo credentials are set in `.env` (copy `.env.example` if it is missing). `run.bat flask` starts the original Flask interface on port 5000 instead."),
        H2("B.3 Manual start"),
        CODE("# terminal 1, project root\n.venv\\Scripts\\python -m uvicorn backend.main:api --port 8312\n\n# terminal 2\ncd frontend\nnpm install\nnpm run dev"),
        H2("B.4 Using the application"),
        TAB("Walk-through", ["Step", "Action", "Result"], [
            ["1", "Open http://localhost:5312 and choose **Sign in**; press **Fill demo credentials** and **Sign in** (demo@pneumodetect.ai / Pneumo@123)", "The dashboard opens"],
            ["2", "Open **New scan**; drop a PNG or JPG chest X-ray (up to 8 MB) or choose a file", "A preview and the file details appear"],
            ["3", "Press **Analyse**", "A progress bar runs; the result page opens"],
            ["4", "Read the class badge, confidence and probability bars; switch between **Side by side** and **Blend heatmap**", "The Grad-CAM overlay shows the regions that drove the prediction"],
            ["5", "Use **Print report**, **Download heatmap** or **Delete scan** as needed", "A report, an image file, or a confirmation dialog"],
            ["6", "Open **History**; search by file name, filter by class, sort a column, or **Export CSV**", "The table updates; a CSV file downloads"],
            ["7", "Open **Dashboard** for totals, class distribution and scans per day", "Charts and recent scans"],
        ], widths=[0.5, 3.8, 2.0], size=9.5, align=["c", "l", "l"]),
        H2("B.5 Training a model"),
        CODE("python scripts/train_experiment.py --data_root <path to chest_xray> --name exp01_custom_cnn_clahe \\\n    --export_model saved_models\n# restart the API: the Demo Mode badge changes to 'Trained model'"),
        P("The data folder must contain `train/`, `val/` and `test/` with `NORMAL/` and `PNEUMONIA/` sub-folders (the public \"chest_xray\" layout). "
          "`scripts/leakage_analysis.py` and `scripts/make_figures.py` then recompute the analysis and the figures used in this report."),
        H2("B.6 Running the tests"),
        CODE("python -m pytest tests -q          # 73 tests, about one minute\npython scripts/smoke_test.py          # with the servers running\npython scripts/verify_ui.py           # needs: pip install playwright; playwright install chromium\npython scripts/capture_screens.py     # regenerates docs/screenshots"),
        H2("B.7 Troubleshooting"),
        B("**\"The API is not reachable\":** the API window is not running or is still loading TensorFlow. Check the **PneumoDetect API** window.",
          "**Port already in use:** change `BACKEND_PORT` or `FRONTEND_PORT` in `.env` and start again.",
          "**`ModuleNotFoundError: cv2`** outside `run.bat`: `pip install -r requirements.txt -r requirements-api.txt` into the Python you are using.",
          "**TensorFlow fails to start with a DLL error** after other scientific libraries were imported first: import TensorFlow first (the project scripts do)."),
    ]


def screens_blocks():
    shots = [
        ("01_landing_light.png", "Landing page, light theme"),
        ("02_landing_dark.png", "Landing page, dark theme"),
        ("03_login.png", "Sign-in screen with the demo credentials box"),
        ("04_detect_empty.png", "Detect screen before a file is chosen"),
        ("05_detect_preview.png", "Detect screen with a preview and the analyse button"),
        ("07_result_blend.png", "Result screen, blended heat-map view"),
        ("08_result_dark.png", "Result screen, dark theme"),
        ("10_dashboard_dark.png", "Dashboard, dark theme"),
        ("12_about.png", "About screen"),
        ("14_result_demo_mode.png", "Result screen in Demo Mode (untrained network, before the model was trained): the amber banner and the near-equal probabilities are the warning that the output is meaningless"),
        ("15_detect_demo_mode.png", "Detect screen in Demo Mode"),
    ]
    out = [H1("APPENDIX C: ADDITIONAL SCREENS")]
    out.append(P("All screenshots are captures of the running application at 1440 x 900 with real scans in the history. "
                 "The two Demo Mode screens (the last two figures) were taken before the model was trained and are kept to document that state."))
    for f, cap in shots:
        if os.path.exists(F.shot(f)):
            out.append(FIG(F.shot_view(f), cap, F.shot_w(F.shot_view(f), 5.6)))
    return out
