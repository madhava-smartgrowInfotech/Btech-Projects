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
    while chunk and (not chunk[-1].strip() or set(chunk[-1].strip()) <= set("#- ")):
        chunk.pop()
    return "\n".join(chunk)


def code_blocks():
    s = source
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings below are extracted from the repository by the document build script, so they are the code that was tested and measured. "
          "File paths are relative to `8.ProjectCode`."),
        H2("A.1 Image clean-up before OCR (`ocr_processor.py`)"),
        CODE(s("ocr_processor.py", "def preprocess_image_for_ocr", "def _ocr_image_array")),
        H2("A.2 Text from a PDF: text layer first, OCR for scanned pages (`ocr_processor.py`)"),
        CODE(s("ocr_processor.py", "def extract_text_from_pdf_bytes", "def extract_text(")),
        H2("A.3 Unit expression and row patterns (`ner_processor.py`)"),
        CODE(s("ner_processor.py", "# Matches unit tokens commonly found", "# Common test-date formats")),
        H2("A.4 Snapping a noisy test name to the dictionary (`ner_processor.py`)"),
        CODE(s("ner_processor.py", "_TEST_NAME_VECTORIZER = TfidfVectorizer", "# Regex patterns for line-level extraction")),
        H2("A.5 Extracting rows from the text (`ner_processor.py`)"),
        CODE(s("ner_processor.py", "    for raw_line in text.splitlines():", "def _deduplicate")),
        H2("A.6 Classification (`result_analyzer.py`)"),
        CODE(s("result_analyzer.py", "def classify_result", "def analyze_results")),
        H2("A.7 Explanations with a safe fall-back (`ai_insights.py`)"),
        CODE(s("ai_insights.py", "def generate_rule_based_insight", "# Optional LLM enrichment")),
        CODE(s("ai_insights.py", "def generate_insight")),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B("Python 3.11 or newer and Node.js 20 or newer (LTS) on the PATH.",
          "**Tesseract OCR** (optional): needed only for scanned PDFs and photographs. Text-based PDFs work without it. Windows: install from the UB Mannheim build and add `tesseract.exe` to the PATH; macOS: `brew install tesseract`; Ubuntu: `sudo apt-get install tesseract-ocr`.",
          "A modern browser. About 1 GB of disk space for the Python environment and the front-end packages."),
        H2("B.2 One-click start (Windows)"),
        N("Open the folder `8.ProjectCode` and double-click `run.bat` (or run it from a terminal in that folder).",
          "On the first run it creates `backend\\.venv`, installs `backend\\requirements.txt` (a few minutes) and runs `npm install` in `frontend\\`. It rebuilds the environment automatically if it is missing or broken.",
          "Two console windows open (the API on port 8308 and the web app on port 5308) and the browser opens http://localhost:5308.",
          "Close the two console windows to stop the application."),
        P("The ports, the token signing key and the optional API key are set in `.env`; copy `.env.example` to `.env` if it does not exist. "
          "The original Streamlit interface still runs separately with `streamlit run app.py` on port 8501 and shares the same database."),
        H2("B.3 Manual start (any operating system)"),
        CODE("# terminal 1, from 8.ProjectCode\npython -m venv backend/.venv\nbackend/.venv/Scripts/python -m pip install -r backend/requirements.txt\nbackend/.venv/Scripts/python -m uvicorn backend.main:app --port 8308\n\n# terminal 2\ncd frontend\nnpm install\nnpm run dev        # http://localhost:5308, proxies /api to port 8308"),
        P("On macOS or Linux use `backend/.venv/bin/python`. For a production-style run, `npm run build` in `frontend/` and start only the backend: it serves the built front end itself at http://localhost:8308."),
        H2("B.4 Settings in `.env`"),
        TAB("Environment variables", ["Variable", "Purpose"], [
            ["`BACKEND_PORT`, `FRONTEND_PORT`", "fixed at 8308 and 5308 for this project so several products can run side by side"],
            ["`JWT_SECRET`", "signs login tokens; change it on first run"],
            ["`DEMO_EMAIL`, `DEMO_PASSWORD`", "override the demo account (default `demo@lablens.com` / `Demo@1234`)"],
            ["`ANTHROPIC_API_KEY`", "enables the \"Use LLM for richer explanations\" switch; without it the built-in explanations are used"],
        ], widths=[2.2, 3.8], size=10, align=["l", "l"]),
        H2("B.5 Using the application"),
        TAB("Walk-through", ["Step", "Action", "Result"], [
            ["1", "Open http://localhost:5308 and choose **Sign in**, then **Sign in as demo user**", "The dashboard opens"],
            ["2", "On an empty library choose **Load sample reports**", "Five synthetic reports are rendered as PDFs and processed by the real pipeline"],
            ["3", "Open **Upload report**, drop a PDF, JPG or PNG (up to 15 MB) and press **Process report**", "A stage tracker runs and the extracted results appear with their status"],
            ["4", "Open **Report analysis** and pick a report", "Result table and explanation cards for every abnormal result"],
            ["5", "Open **My reports**; search by name or status, expand a report, or delete it", "History with a confirmation dialog on delete"],
            ["6", "Open **Health trends** and pick a test", "Chart against the reference band, the overall pattern and a table of every value"],
            ["7", "Open **Compare reports** and pick two reports", "Tests in common with signed change, and bar charts grouped by unit"],
            ["8", "Open **Health insights**; filter by Low or High, or search", "Every explanation for every abnormal result in the library"],
        ], widths=[0.5, 3.4, 2.1], size=9.5, align=["c", "l", "l"]),
        P("Every page carries the notice that LabLens is an educational tool and not a medical device. Rows in a report should look like `Hemoglobin 13.5 g/dL 12 - 16`; reports whose table cells are separate lines of text are not supported."),
        H2("B.6 Running the tests and the experiments"),
        CODE("python -m pytest tests -q                 # 36 tests, a few seconds, temporary database\n"
             "python scripts/smoke_test.py               # API + browser flow in a temporary copy\n"
             "python scripts/ui_check.py                 # needs a running app and Playwright\n"
             "python scripts/capture_screens.py          # refreshes docs/screenshots\n"
             "python -X utf8 scripts/run_experiments.py  # generated corpus -> experiments/lablens/metrics.json and docs/figures\n"
             "python -X utf8 scripts/measure_api.py      # API latency -> experiments/lablens/api_latency.json"),
        P("`smoke_test.py` needs a built front end for its browser part (`cd frontend && npm run build`); `ui_check.py` and `capture_screens.py` need `pip install playwright && playwright install chromium`."),
        H2("B.7 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Fix"], [
            ["\"Cannot reach the LabLens backend on port 8308\"", "the API window is not running; start `run.bat` again and read its console"],
            ["Upload of a JPG or PNG fails with an OCR message", "install Tesseract OCR (see B.1)"],
            ["\"No recognizable lab test rows were found\"", "the layout is unusual, the scan is too faint, or each table cell is a separate line; try a clearer file"],
            ["The LLM switch is disabled", "no `ANTHROPIC_API_KEY` in `.env`; the feature is optional"],
            ["Port already in use", "stop the other product or change the ports in `.env`"],
            ["API calls are slow from a script", "call `127.0.0.1` instead of `localhost`"],
        ], widths=[2.6, 3.4], size=9.5, align=["l", "l"]),
    ]


def screens_blocks():
    shots = [
        ("01_landing_dark.png", "Landing page, dark theme: the headline, the accepted formats (PDF, JPG, JPEG, PNG) and the notice that this is an educational tool"),
        ("03_login.png", "Sign-in screen with the demo account box and the one-click demo sign-in"),
        ("05_upload_empty.png", "Upload screen before a file is chosen: drop zone, the disabled LLM switch with its explanation, and the six-stage pipeline list"),
        ("12_about.png", "About screen: the five pipeline stages, the technology stack and the stated limitations"),
        ("13_dashboard_empty_state.png", "Dashboard of an empty library: zero totals and the two ways to begin, uploading a report or loading five sample reports"),
    ]
    out = [H1("APPENDIX C: ADDITIONAL SCREENS")]
    out.append(P("All screens are captures of the running application at 1440 x 900 pixels. The library behind them holds only synthetic reports (invented patient and values), "
                 "except the last screen, which shows the application before any report is loaded."))
    for f, cap in shots:
        if os.path.exists(F.shot(f)):
            out.append(FIG(F.shot_view(f), cap, F.shot_w(F.shot_view(f), 4.7, 4.6)))
    return out
