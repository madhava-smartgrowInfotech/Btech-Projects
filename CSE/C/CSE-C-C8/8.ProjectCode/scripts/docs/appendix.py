"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .ch9_10 import src


def _code_report():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("Listings are copied from `8.ProjectCode` in the state in which the results were measured; line ranges are whole statements."),
        H2("A.1 Section detection (`app/services/pdf_extract.py`)"),
        CODE(src("app/services/pdf_extract.py", 87, 112), 7.5),
        H2("A.2 Structural score (`app/services/features.py`)"),
        CODE(src("app/services/features.py", 27, 63), 7.5),
        H2("A.3 Conflict detection and reviewer ranking (`app/services/matching.py`)"),
        CODE(src("app/services/matching.py", 48, 62), 7.5),
        CODE(src("app/services/matching.py", 65, 112), 7.5),
        H2("A.4 The analysis pipeline (`app/services/pipeline.py`)"),
        CODE(src("app/services/pipeline.py", 18, 42), 7.5),
        H2("A.5 Training the decision model (`scripts/train_model.py`)"),
        CODE(src("scripts/train_model.py", 46, 62), 7.5),
    ]


def code_blocks():
    if F.REPORT:
        return _code_report()
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured. Docstrings and comments are kept as they are; the line ranges are whole statements, and long functions are cut only at their end."),
        H2("A.1 Section detection (`app/services/pdf_extract.py`)"),
        P("A heading is a short line (80 characters or fewer) whose lower-cased text matches one of the patterns of a section; the first heading found for each section wins, and each section runs to the next heading. "
          "The roman-numeral limitation discussed in Chapter 8 follows from the introduction pattern, which allows an optional arabic \"1\" but not \"I.\"."),
        CODE(src("app/services/pdf_extract.py", 7, 17), 8),
        CODE(src("app/services/pdf_extract.py", 87, 112), 8),
        H2("A.2 Structural signals (`app/services/features.py`)"),
        CODE(src("app/services/features.py", 27, 63), 8),
        H2("A.3 The decision signal (`app/services/ml_predict.py`)"),
        CODE(src("app/services/ml_predict.py", 29, 80), 8),
        H2("A.4 Conflict detection and reviewer ranking (`app/services/matching.py`)"),
        CODE(src("app/services/matching.py", 48, 62), 8),
        CODE(src("app/services/matching.py", 65, 112), 8),
        H2("A.5 The analysis pipeline (`app/services/pipeline.py`)"),
        CODE(src("app/services/pipeline.py", 18, 45), 8),
        H2("A.6 The analyze endpoint (`app/main.py`)"),
        CODE(src("app/main.py", 158, 206), 8),
        H2("A.7 Training the decision model (`scripts/train_model.py`)"),
        CODE(src("scripts/train_model.py", 39, 78), 8),
    ]


def _guide_report():
    e = F.ENV
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B(f"Windows PC (built on an {e['cpu']}, {e['ram_gb']} GB, no GPU), Python 3.11 or 3.12, Node.js 18 or newer, a current browser.",
          "Internet for the first installation and first analysis (MiniLM about 90 MB; Qwen2.5-1.5B-Instruct about 3 GB if the AI review is wanted; about 6 GB free memory while it runs) and for the literature tab."),
        H2("B.2 Installation and start"),
        P("Double-click `run.bat` in `8.ProjectCode`: it creates `.venv`, installs the requirements, prepares the dataset, trains the decision model on the first run, installs the web packages and starts **PeerScope API** (port 8408) and **PeerScope Web** (port 5408); the browser opens `http://localhost:5408`. Manual start:"),
        CODE("""python -m venv .venv && .venv\\Scripts\\activate && python -m pip install -r requirements.txt
python scripts\\prepare_dataset.py && python scripts\\train_model.py && python scripts\\make_demo_pdf.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8408
cd frontend && npm install && npm run dev      # web app on http://localhost:5408""", 8),
        P("`docker build -t peerscope .` and `docker run --rm -p 8408:8408 peerscope` start the API only. Settings live in `.env` (`PEERSCOPE_PORT`, `FRONTEND_PORT`, `PEERSCOPE_MAX_UPLOAD_MB` = 20, `PEERSCOPE_LLM_MODEL`, `PEERSCOPE_EMBED_MODEL`, the five `PEERSCOPE_W_*` weights, `PEERSCOPE_DB`); an invalid model name switches the AI review off."),
        TAB("Main settings (`.env`, defaults)", ["Variable", "Default", "Meaning"],
            [["PEERSCOPE_PORT / FRONTEND_PORT", "8408 / 5408", "API and web ports (keep `VITE_API_URL` equal to the API address)"],
             ["PEERSCOPE_MAX_UPLOAD_MB", "20", "Upload limit; larger files get HTTP 413"],
             ["PEERSCOPE_LLM_MODEL / _FALLBACK", "Qwen2.5-1.5B / 0.5B Instruct", "Local review models; an invalid name switches the AI review off"],
             ["PEERSCOPE_EMBED_MODEL", "all-MiniLM-L6-v2", "Sentence encoder for matching and literature ranking"],
             ["PEERSCOPE_W_EXPERTISE ... _CONFLICT", "0.55, 0.20, 0.15, 0.10, 0.60", "Match-score weights"],
             ["PEERSCOPE_DB", "SQLite file in `data/`", "A different file gives a clean history"]],
            widths=[2.3, 1.7, 2.6], align=["l", "l", "l"], size=9.5),
        H2("B.3 Using the application"),
        TAB("User guide", ["Screen", "How to use it"],
            [["Landing", "Overview of the product; \"Analyze a paper\" and \"Open dashboard\" start the work."],
             ["Dashboard", "Reviewers in the directory, stored analyses, decision-model accuracy (with its synthetic-data caveat), local AI status and the latest analyses."],
             ["Analyze paper", "Drop a PDF (up to 20 MB). Keep \"active reviewers only\" on, set a minimum score, or type a topic or method the reviewers must match, then press Analyze paper; with the local model the wait is several minutes on a CPU. "
              "Read the Overview, Review, Literature, Reviewers and Audit tabs; export JSON or PDF from the last one."],
             ["Reviewers", "Search, add, edit, activate or deactivate and delete reviewers; import or export CSV. Set conflict terms (names, institutions, project names) to have them penalised when they appear in a paper."],
             ["Model performance", "Metrics, confusion matrix and class counts of the decision model, read from `models/metrics.json`, with the synthetic-data warning."],
             ["Analysis history", "Every stored analysis; open one to see it again, or export it."],
             ["About", "Pipeline description, weights, responsible-use rules, privacy statement and live system status."]],
            widths=[1.4, 5.2], align=["l", "l"], size=9.5),
        P("Reviewer CSV: export produces, and import expects, the columns `id` (ignored), `display_name` (required; rows without it are skipped), `affiliation`, `expertise_description`, `research_topics`, `methods`, `keywords`, `publication_titles` (list fields separated by commas, semicolons or vertical bars), `current_load`, `maximum_load`, `is_active` and `conflict_terms`. "
          "A file with a header but no names imports zero rows and reports `imported: 0` without an error."),
        H2("B.4 Tests and troubleshooting"),
        CODE(f"""python -m pytest tests            # {F.PYTEST_TOTAL} tests, {F.PYTEST_PASSED} passed in {F.PYTEST_SECONDS} s (model off)
python scripts/smoke_test.py      # {F.SMOKE_TOTAL} live checks
python scripts/measure_metrics.py # all measured results -> docs/metrics/metrics.json""", 8),
        TAB("Common problems", ["Symptom", "Cause and remedy"],
            [["Port in use / backend unreachable", "Change the port in `.env` or start `python -m uvicorn app.main:app --port 8408`; use `http://127.0.0.1:5408` if `localhost` resolves to IPv6."],
             ["AI review \"unavailable\"", "Model not downloaded or too little memory; the deterministic review is still shown."],
             ["Analysis takes minutes", "Normal with the local model on a CPU (about nine minutes here); disable it for a fast analysis."],
             ["Literature tab \"unavailable\"", "No internet, or the title contains a question mark (known defect)."],
             ["Very little text, wrong title or no introduction", "Scanned PDF (no OCR), or roman-numeral headings (known limitation)."],
             ["Python or Node.js not found", "Install them and tick \"Add python.exe to PATH\"; reopen the terminal."],
             ["Dependency installation fails", "Check the internet connection, delete `.venv` and run `run.bat` again; the pip error names the failing package."],
             ["Times appear several hours behind", "Timestamps are stored in UTC; the History list shows them without a time zone."],
             ["Reviewer CSV imports nothing", "The file has no `display_name` values; add names and import again."],
             ["Upload refused", "Only text-based PDFs up to 20 MB with a valid PDF header are accepted (HTTP 400 or 413 otherwise)."]],
            widths=[2.2, 4.4], align=["l", "l"], size=9.5),
    ]


def guide_blocks():
    if F.REPORT:
        return _guide_report()
    e = F.ENV
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B(f"Windows PC (the build machine was an {e['cpu']} with {e['ram_gb']} GB of memory and no GPU; these are the machine's figures, not stated minimums). A full analysis with the local language model needs about 6 GB of free memory.",
          "Python 3.11 or 3.12 on the PATH and Node.js 18 or newer.",
          "A current browser (Chrome, Edge or Firefox) on `http://localhost:5408`.",
          "An internet connection for the first installation and for the first analysis, which downloads the sentence encoder (about 90 MB) and, when the AI review is wanted, the Qwen2.5-1.5B-Instruct model (about 3 GB) into `models/hf_cache`. "
          "Literature context needs internet at every analysis; without it the Literature tab shows an \"unavailable\" notice."),
        H2("B.2 Installation and start"),
        H3("B.2.1 Automatic (recommended)"),
        N("Open the project folder `8.ProjectCode` and double-click `run.bat`.",
          "The script checks Python and Node.js, creates `.venv` (and rebuilds it if it was copied from another machine), installs `requirements.txt`, prepares the dataset and trains the decision model on the first run, installs the web packages and starts two windows: **PeerScope API** (port 8408) and **PeerScope Web** (port 5408).",
          "The browser opens `http://localhost:5408`. The API documentation is at `http://127.0.0.1:8408/docs`.",
          "To stop, close the two windows."),
        H3("B.2.2 Manual"),
        CODE("""python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
python scripts\\prepare_dataset.py        # writes data/processed_dataset.csv (synthetic fallback)
python scripts\\train_model.py            # writes models/*.joblib and models/metrics.json
python scripts\\make_demo_pdf.py          # writes data/demo/demo_paper.pdf
python -m uvicorn app.main:app --host 127.0.0.1 --port 8408

cd frontend
npm install
npm run dev                              # web app on http://localhost:5408""", 8.5),
        H3("B.2.3 Docker"),
        P("`docker build -t peerscope .` followed by `docker run --rm -p 8408:8408 peerscope` (or double-clicking `run-docker.bat`) starts the API only; the web app is started with `npm run dev` as above."),
        H3("B.2.4 Settings"),
        TAB("Environment variables (`.env`, defaults shown)", ["Variable", "Default", "Meaning"],
            [["PEERSCOPE_PORT / FRONTEND_PORT", "8408 / 5408", "API and web-app ports (keep `VITE_API_URL` equal to the API address)"],
             ["PEERSCOPE_MAX_UPLOAD_MB", "20", "Upload limit; larger files are refused with HTTP 413"],
             ["PEERSCOPE_LLM_MODEL / PEERSCOPE_LLM_FALLBACK", "Qwen2.5-1.5B-Instruct / Qwen2.5-0.5B-Instruct", "Local review models; an invalid name switches the AI review off"],
             ["PEERSCOPE_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2", "Sentence encoder for reviewer matching and literature ranking"],
             ["PEERSCOPE_LITERATURE_COUNT / _TIMEOUT", "6 / 8 s", "Number of OpenAlex works and the request timeout"],
             ["PEERSCOPE_W_EXPERTISE, _KEYWORD, _METHOD, _AVAIL, _CONFLICT", "0.55, 0.20, 0.15, 0.10, 0.60", "Weights of the match score"],
             ["PEERSCOPE_DB", "SQLite file in `data/`", "Database URL; a different file gives a clean history"]],
            widths=[2.5, 1.8, 2.3], align=["l", "l", "l"], size=9.5),
        H2("B.3 Using the screens"),
        TAB("User guide", ["Screen", "How to use it"],
            [["Landing", "Overview of the product; \"Analyze a paper\" and \"Open dashboard\" start the work."],
             ["Dashboard", "Reviewers in the directory, stored analyses, decision-model accuracy (with its synthetic-data caveat), local AI status and the latest analyses."],
             ["Analyze paper", "Drop a PDF (up to 20 MB). Optionally keep \"active reviewers only\" on, set a minimum score, or type a topic or method the reviewers must match. Press Analyze paper. With the local model the wait is several minutes on a CPU. "
              "Read the Overview, Review, Literature, Reviewers and Audit tabs; export JSON or PDF from the last one."],
             ["Reviewers", "Search, add, edit, activate or deactivate and delete reviewers; import or export CSV. Set conflict terms (names, institutions, project names) to have them penalised when they appear in a paper."],
             ["Model performance", "Metrics, confusion matrix and class counts of the decision model, read from `models/metrics.json`, with the synthetic-data warning."],
             ["Analysis history", "Every stored analysis; open one to see it again, or export it."],
             ["About and responsible use", "Pipeline description, weights, responsible-use rules, privacy statement and live system status."]],
            widths=[1.4, 5.2], align=["l", "l"], size=10),
        H2("B.4 Reviewer CSV format"),
        P("Export produces, and import expects, one reviewer per row with these columns: `id` (ignored on import), `display_name` (required; rows without it are skipped), `affiliation`, `expertise_description`, `research_topics`, `methods`, `keywords`, `publication_titles` "
          "(list fields are comma separated), `current_load`, `maximum_load`, `is_active` (`true` or `false`) and `conflict_terms`. A file with a header but no `display_name` values imports zero rows and reports `imported: 0` without an error."),
        CODE("""display_name,affiliation,expertise_description,research_topics,methods,keywords,publication_titles,current_load,maximum_load,is_active,conflict_terms
Reviewer Example,Example Lab,"Natural language processing and retrieval",language; nlp,transformer; evaluation,retrieval; nlp,,0,5,true,example-project""", 7.5),
        P("Fields may be separated by commas, semicolons or vertical bars inside a list field (the parser splits on all three)."),
        H2("B.5 Running the tests"),
        CODE(f"""python -m pytest tests                    # {F.PYTEST_TOTAL} tests, {F.PYTEST_PASSED} passed in {F.PYTEST_SECONDS} s (local model off)
python scripts/smoke_test.py              # {F.SMOKE_TOTAL} live checks against the running API and web app
python scripts/measure_metrics.py         # decision model, matching, conflicts, real PDFs -> docs/metrics/metrics.json
python scripts/measure_latency.py stages  # per-stage timing with the local model
python scripts/capture_screens.py         # 1440x900 screenshots of every screen (needs Playwright)""", 8.5),
        P("To run the tests without loading the language model, set `PEERSCOPE_LLM_MODEL=disabled` and `PEERSCOPE_LLM_FALLBACK=disabled` first; the end-to-end test then takes seconds instead of minutes."),
        H2("B.6 Troubleshooting"),
        TAB("Problems and remedies", ["Symptom", "Cause and remedy"],
            [["Python or Node.js not found", "Install them and tick \"Add python.exe to PATH\"; reopen the terminal."],
             ["Dependency installation fails", "Check the internet connection, delete `.venv` and run `run.bat` again; the pip error names the failing package."],
             ["Port 8408 or 5408 in use", "Close the other program or change the port in `.env` (and `VITE_API_URL`)."],
             ["\"Cannot reach the PeerScope backend\"", "The API window is closed or crashed; start it with `python -m uvicorn app.main:app --port 8408`."],
             ["AI review shows \"unavailable\"", "The model could not be downloaded or loaded (no internet, not enough memory). The deterministic review is still shown; retry later."],
             ["An analysis takes many minutes", "Normal with the local model on a CPU (about nine minutes for the build machine). Disable the model for a fast deterministic analysis."],
             ["Literature tab says \"unavailable\"", "No internet, or the paper's title contains a question mark, which OpenAlex rejects (a known defect). The rest of the analysis is complete."],
             ["Very little text found", "The PDF is scanned images; PeerScope has no OCR. Use a text-based PDF."],
             ["Introduction not detected, title wrong", "Heading styles such as roman numerals are not recognised by the section parser (a known limitation)."],
             ["Times appear several hours behind", "Timestamps are stored in UTC; the History list shows them without a time zone."],
             ["Browser cannot reach `localhost:5408`", "The Vite server listens on 127.0.0.1; use `http://127.0.0.1:5408` if `localhost` resolves to IPv6."]],
            widths=[2.2, 4.4], align=["l", "l"], size=10),
    ]


def _screens_report():
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("Chapter 8 shows all 17 screens. The table lists the alternate states among them (theme, scrolled page, dialog); two further result figures not used in Chapter 8 follow."),
        TAB("Alternate states of the application", ["Screen", "State", "What differs"],
            [["Landing page", "Dark, scrolled to how it works", "The pipeline steps below the hero"],
             ["Landing page", "Light theme", "Same layout and data, light colours; theme switched with the sun button"],
             ["Dashboard", "Light theme", "Same tiles and recent analyses as the dark dashboard"],
             ["Reviewers", "Add-reviewer dialog", "Eleven fields; the same columns as the CSV format"]],
            widths=[1.5, 2.2, 2.9], align=["l", "l", "l"], size=9.5),
        PAIR([(F.fig("f06_dataset_structure.png"), "Class counts of the synthetic dataset and how each label relates to the phrases in the text."),
              (F.fig("f09_matching_scaling.png"), "Median ranking time against the number of reviewers (MiniLM and TF-IDF fallback).")], 3.0),
        PAIR([(F.fig("f05_threshold.png"), "Share of papers kept and accuracy on them as the minimum confidence rises."),
              (F.fig("f10_real_papers_signals.png"), "Structural signals on four real PDFs.")], 3.0),
        P("The first figure shows why the decision model cannot exceed about 0.56 accuracy on its data: the label of a paper is drawn from the same phrases that appear in its text, and the borderline class comes from both groups. "
          "The second shows that ranking time grows linearly with the directory because every reviewer profile is embedded again for each request; a cache of profile vectors is the first change for a larger pool. "
          "The light theme and the dialog above use the same code and data as the dark screens of Chapter 8, and were captured in the same session."),
    ]


def screens_blocks():
    if F.REPORT:
        return _screens_report()
    s = F.shot
    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("Chapter 8 shows every screen of the application. This appendix repeats the four screens that show an alternative state (the light theme, the how-it-works section of the landing page and the add-reviewer dialog) at a larger size so that their detail can be read; "
          "all are real captures at 1440 by 900 pixels taken with the same data as the screens in Chapter 8."),
        FIG(s("02_landing_how_it_works_dark.png"), "Landing page scrolled to the how-it-works section (dark theme).", F.shot_w(s("02_landing_how_it_works_dark.png"), 5.6, 3.9)),
        FIG(s("03_landing_light.png"), "Landing page in the light theme.", F.shot_w(s("03_landing_light.png"), 5.6, 3.9)),
        FIG(s("17_dashboard_light.png"), "Dashboard in the light theme, with three stored real analyses.", F.shot_w(s("17_dashboard_light.png"), 5.6, 3.9)),
        FIG(s("12_reviewers_add_modal.png"), "Add-reviewer dialog: display name, affiliation, expertise description, topics, methods, keywords, publication titles, loads, status and conflict terms.", F.shot_w(s("12_reviewers_add_modal.png"), 5.6, 3.9)),
        P("The light theme uses the same layout and the same data as the dark one, and is switched with the sun button in the header. The add-reviewer dialog is the form behind the reviewer directory; the same eleven fields are the columns of the CSV format in Appendix B."),
    ]
