"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, TAB


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a project file, read from disk so the listing is always the real code."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().replace("\r\n", "\n").rstrip("\n").split("\n")
    a = (start or 1) - 1
    b = end or len(lines)
    return "\n".join(lines[a:b])


def code_blocks():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured and are read from the files when this document is built. "
          "Only the most important functions are shown; the quiz generator and the database schema are described in Chapters 5 and 6."),
        H2("A.1 Chunking (`utils/text_extraction.py`, lines 58-74)"),
        CODE(src("utils/text_extraction.py", 58, 74), 8),
        H2("A.2 Index and retrieval (`utils/rag_engine.py`, lines 26-57)"),
        P("`build_index` fits the TF-IDF vectoriser on the chunks of one user; `retrieve` scores a query by cosine similarity and drops zero scores."),
        CODE(src("utils/rag_engine.py", 26, 57), 7.5),
        H2("A.3 Extractive answer and generation (`utils/rag_engine.py`, lines 59-101)"),
        P("`_extractive_answer` selects the best sentences; `generate_answer` calls the language model first when a key is given and falls back to the extractive answer."),
        CODE(src("utils/rag_engine.py", 59, 101), 7.5),
        H2("A.4 The ask and roadmap endpoints (`backend/main.py`, lines 297-321 and 400-430)"),
        CODE(src("backend/main.py", 297, 321) + "\n\n" + src("backend/main.py", 400, 430), 7.5),
    ]


def guide_blocks():
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B(f"A Windows PC (the build machine was an {F.ENV['cpu']} with {F.ENV['ram']} and no GPU; these are not stated minimums), Python 3.11 or newer (built with {F.ENV['python']}), Node.js 20 or newer (24.19 was used) and a current browser (Chrome was used).",
          "An internet connection for the first installation only. No other service is needed: the default answer mode is offline."),
        H2("B.2 Installation and start"),
        N("Open the folder `8.ProjectCode` and double-click `run.bat`. On the first run it creates the virtual environment `venv`, installs `backend\\requirements.txt` (which includes the root `requirements.txt`: Flask, scikit-learn, NumPy, pypdf, python-docx, FastAPI, uvicorn, python-multipart and itsdangerous) and runs `npm install` in `frontend`.",
          "It then opens two windows: the backend (`uvicorn backend.main:app` on `127.0.0.1:8301`, health check at `http://localhost:8301/api/health`, interactive API documentation at `/api/docs`) and the frontend (Vite on `http://localhost:5301`).",
          "Open `http://localhost:5301` in the browser. Register an account (or use the demo account below) and start with the Upload screen.",
          "To stop, close the two server windows. Ports and the cookie-signing secret are read from `.env` (copy `.env.example`; `.env` is not stored in version control)."),
        P("Manual start: `venv\\Scripts\\python -m uvicorn backend.main:app --port 8301` in `8.ProjectCode`, and `npm install` then `npm run dev` in `frontend` (`npm run build` runs the type check and the production build). "
          "The original Flask interface starts with `venv\\Scripts\\python app.py` at `http://127.0.0.1:5000`; both interfaces share `instance/app.db`."),
        TAB("Settings in `.env` and the demo account", ["Key or field", "Meaning or value"],
            [["`BACKEND_PORT`, `FRONTEND_PORT`", "8301 and 5301 by default; the Vite proxy sends `/api` from the frontend port to the backend port"],
             ["`SECRET_KEY`", "Signs the session cookie; change it for any use beyond a local demo"],
             ["`ANTHROPIC_API_KEY`", "Optional. When set (and `pip install anthropic` has been run) answers are written by Claude from the retrieved passages; if a call fails the extractive answer is used"],
             ["Demo account", "URL `http://localhost:5301`, username `demo`, password `Demo@1234`. It exists in the local `instance/app.db`; with a fresh database register it again or register any account (there is no administrator)."]],
            widths=[2.1, 4.6], align=["l", "l"], size=10),
        H2("B.3 Using the screens"),
        TAB("User guide", ["Screen (route)", "How to use it"],
            [["Landing, Login, Register (`/`, `/login`, `/register`)", "Register with a username, a password and optional interests, then log in; the application opens on the Upload screen."],
             ["Upload (`/app/upload`)", "Drop or choose a PDF, DOCX or TXT file (up to 16 MB), type a subject and press *Upload & process*. The result card lists the detected topics and chunks indexed. Try `sample_data/sample_notes_data_structures.txt` first."],
             ["Documents (`/app/documents`)", "Lists every upload with subject, topics, chunks and date; search by name, subject or topic; *Generate quiz* starts a quiz and the bin button deletes the document."],
             ["Ask (`/app/ask`)", "Type a question and press *Ask* or Ctrl+Enter. The answer is shown with the sources (file, passage, match score); the right panel keeps the last ten questions."],
             ["Quiz (`/app/quiz`)", "Choose a document, answer five fill-in-the-blank questions and press *Submit quiz*; the result page shows the score and the correct term and topic of every question."],
             ["Roadmap and Dashboard (`/app/roadmap`, `/app`)", "The roadmap ranks topics by quiz accuracy: High below 50 %, Medium below 80 %, Low otherwise. The dashboard shows counts, accuracy per subject and the latest documents; the sun and moon button switches theme."]],
            widths=[1.9, 4.8], align=["l", "l"], size=9.5),
        H2("B.4 Running the tests, measurements and screenshots"),
        CODE(r"""venv\Scripts\python -m pip install pytest==8.3.3 httpx==0.27.2   :: once
venv\Scripts\python -m pytest -q                                 :: 84 tests, temporary database
venv\Scripts\python scripts\smoke_test.py                        :: 24 live API checks (backend running)
python scripts\fetch_corpus.py ; venv\Scripts\python scripts\run_experiments.py   :: corpus, experiments\results.json
venv\Scripts\python scripts\serve_scratch.py --data <folder> --port 8301 ; ... scripts\measure_api.py
python scripts\capture_screens.py --rich --responsive ; python scripts\make_figures.py ; python scripts\make_diagrams.py""", 8),
        P("Use `serve_scratch.py` for measurements and screenshots so that `instance/app.db` is not changed. `scripts/dense_baseline.py` (optional, separate environment with `fastembed`) writes the dense similarity matrix for the reference rows."),
        H2("B.5 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and fix"],
            [["The page shows an error or loads nothing after login", "The backend is not running on port 8301. Start it (B.2) and check `http://localhost:8301/api/health`."],
             ["Upload is refused, or a quiz says there is not enough content, or submit says there is no active quiz", "Only PDF, DOCX and TXT up to 16 MB are accepted; a quiz needs a longer document; after a restart generate a new quiz."],
             ["Upload succeeds but reports that no readable text could be extracted", "The PDF has no text layer (a scan) or is empty. The platform has no OCR; use a text version of the file."],
             ["Answers look unrelated to the question", "The question shares only a general word with the notes (there is no relevance threshold). Rephrase with words used in the notes."],
             ["Port already in use; scripts slow on `localhost`", "Change the port in `.env` and restart. Use `127.0.0.1` in scripts: on the test machine `localhost` added about two seconds per request."]],
            widths=[2.4, 4.3], align=["l", "l"], size=9.5),
    ]


def screens_blocks():
    s = F.shot

    def one(name, cap, base=5.2, h=3.2):
        return FIG(s(name), cap, F.shot_w(s(name), base, h))

    def pr(a, ca, b, cb, w=3.1):
        return ("pair", [(s(a), ca), (s(b), cb)], w)

    return [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("These captures complement Chapter 8. Desktop screens are 1440 x 900 pixels; the responsive screens are 360 x 780 and 768 x 1024 pixels. All were taken from the running application "
          "against a scratch database; the quiz answers behind the dashboard and roadmap were scripted (Section 8.2)."),
        pr("01_landing-light.png", "Landing page, light theme.", "02_landing-dark.png", "Landing page, dark theme.", 2.95),
        pr("03_login.png", "Login screen.", "04_register.png", "Registration screen with the form filled.", 2.95),
        pr("05_upload-ready.png", "Upload screen with the sample notes chosen, before pressing Upload & process.",
           "10_quiz-picker.png", "Quiz screen: a button to start a quiz on each document.", 2.95),
        one("14_dashboard-dark.png", "Dashboard in the dark theme.", 4.4, 2.8),
        ("pair", [(s("15_mobile-dashboard.png"), "Dashboard on a 360 x 780 phone."), (s("16_mobile-ask.png"), "Ask screen on a phone."),
                  (s("17_tablet-roadmap.png"), "Roadmap on a 768 x 1024 tablet."), (s("18_mobile-roadmap-dark.png"), "Roadmap on a phone, dark theme.")], 1.5),
    ]
