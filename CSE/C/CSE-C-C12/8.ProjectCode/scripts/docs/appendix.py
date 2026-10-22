"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""

from . import facts as F
from .blocks import B, CODE, H1, H2, N, P, PAIR, TAB
from .ch8 import _cap
from .ch8_report import APPENDIX_C
from .ch9_10 import src, src_fn


def code_blocks():
    out = [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The listings are copied from the repository (`8.ProjectCode`) in the state in which the results of this report were measured. Comments and docstrings are kept as they are; each listing is a whole function or class."),
        H2("A.1 Query expansion (`app/rag/query_expansion.py`)"),
        CODE(src_fn("app/rag/query_expansion.py", "expand_query_hyde"), 8),
        H2("A.2 Hybrid score fusion (`app/rag/hybrid_retriever.py`)"),
        CODE(src_fn("app/rag/hybrid_retriever.py", "fuse"), 8),
        H2("A.3 Cross-encoder reranking (`app/rag/reranker.py`)"),
        CODE(src_fn("app/rag/reranker.py", "Reranker.rerank"), 8),
    ]
    if not F.REPORT:
        out += [H2("A.4 The retrieval pipeline (`app/rag/pipeline.py`)"), CODE(src_fn("app/rag/pipeline.py", "Pipeline.answer"), 8)]
    out += [
        H2("A.4 Safety rules (`app/rag/safety.py`)" if F.REPORT else "A.5 Safety rules (`app/rag/safety.py`)"),
        CODE(src("app/rag/safety.py", 1, 20), 7.5),
        CODE(src_fn("app/rag/safety.py", "check_safety"), 7.5),
        CODE(src_fn("app/rag/safety.py", "apply_safety_filter"), 8),
        H2("A.5 Answer generation with fallback (`app/rag/generator.py`)" if F.REPORT else "A.6 Answer generation with fallback (`app/rag/generator.py`)"),
        CODE(src_fn("app/rag/generator.py", "Generator.fallback_answer"), 8),
        CODE(src_fn("app/rag/generator.py", "Generator.generate"), 8),
        H2("A.6 The chat endpoint (`app/routes/chat.py`)" if F.REPORT else "A.7 The chat endpoint (`app/routes/chat.py`)"),
        CODE(src_fn("app/routes/chat.py", "chat"), 8),
    ]
    if not F.REPORT:
        out += [H2("A.8 Database models (`app/models.py`)"), CODE(src("app/models.py", 1, 28), 8)]
    if not F.REPORT:
        out += [H2("A.9 Password hashing and tokens (`app/auth.py`)"), CODE(src("app/auth.py", 1, 24), 8),
                H2("A.10 History routes (`app/routes/history.py`)"), CODE(src("app/routes/history.py", 27, 49), 8)]
    return out


def _env_rows():
    return [["CARELENS_HOST / CARELENS_PORT", "127.0.0.1 / 8000 (run.bat sets 8412 through `.env`)", "Address of the API"],
            ["CARELENS_DB_PATH", "data/carelens.db", "SQLite file"],
            ["CARELENS_SECRET_KEY", "a development value", "Token signing key; change it for any shared use"],
            ["CARELENS_TOKEN_EXPIRE_MIN", "1440", "Token life in minutes"],
            ["CARELENS_EMBEDDING_MODEL", F.ENV["embedding_model"], "Sentence-embedding model"],
            ["CARELENS_RERANKER_MODEL", F.ENV["reranker_model"], "Cross-encoder"],
            ["CARELENS_GENERATOR_MODEL", F.ENV["generator_model"], "Local generator; an unavailable id selects the evidence-based fallback"],
            ["CARELENS_TOP_K / CARELENS_CANDIDATE_K", f"{F.TOP_K} / {F.CANDIDATE_K}", "Evidence cards shown / candidate pool"],
            ["CARELENS_HYBRID_SEM / CARELENS_HYBRID_LEX", f"{F.FUSION_WEIGHTS[0]} / {F.FUSION_WEIGHTS[1]}", "Fusion weights"],
            ["BACKEND_PORT / FRONTEND_PORT (`.env`)", f"{F.API_PORT} / {F.WEB_PORT}", "Ports used by run.bat and the Vite proxy"]]


def guide_blocks():
    e = F.ENV
    return [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        B(f"A Windows 10 or 11 PC (built and measured on an {e['cpu']}, {e['ram_gb']} GB, no GPU), Python 3.11 (3.10 or newer works), Node.js 18 or newer and a current browser (Chrome or Edge).",
          "About 4 GB of free disk space and an internet connection for the first start, when the three models (MiniLM, the cross-encoder and Flan-T5-small) are downloaded once from Hugging Face. "
          "Afterwards the application also works offline through its fallbacks.",
          "Docker Desktop only for the Docker method."),
        H2("B.2 Method A: automatic start (`run.bat`)"),
        N("Open the project folder (the one containing `run.bat`) in File Explorer and double-click `run.bat`.",
          "The window checks Python and Node.js, creates `.venv` on the first run, installs `requirements.txt` and the frontend packages, builds the knowledge base (`scripts/prepare_data.py`) and the indexes (`scripts/build_index.py`) if missing, and seeds the demo account (`scripts/seed_demo.py`).",
          f"Two windows open: CareLens API (port {F.API_PORT}) and CareLens Web (port {F.WEB_PORT}). The browser opens at http://localhost:{F.WEB_PORT}.",
          "To stop, close the two server windows."),
        H2("B.3 Method B: Docker"),
        CODE("docker compose up --build", 8),
        P(f"Docker builds the React app and starts two containers: the API on port {F.API_PORT} and an nginx server on port {F.WEB_PORT} that serves the app and forwards `/api` to the API. The `data` folder is mounted, so history survives restarts."),
        H2("B.4 Method C: manual start (two terminals)"),
        CODE("python -m venv .venv\n.venv\\Scripts\\activate.bat\npip install -r requirements.txt\npython scripts\\prepare_data.py\npython scripts\\build_index.py\npython scripts\\seed_demo.py\n"
             f"python -m uvicorn app.main:app --host 127.0.0.1 --port {F.API_PORT}\n\n:: second terminal\ncd frontend\nnpm install\nnpm run dev", 8),
        H2("B.5 Using the application"),
        N(f"Open http://localhost:{F.WEB_PORT}, choose the demo login (`{F.DEMO_LOGIN[0]}` / `{F.DEMO_LOGIN[1]}`) or create an account (password of 6 to 128 characters).",
          "On the Symptom assistant screen type your symptoms in everyday words (3 to 2000 characters) and press Enter, or tap an example chip. Shift+Enter inserts a new line.",
          "Read the banner first: red means emergency wording was detected, amber means a caution keyword. Then read the answer, the top condition and the evidence cards (symptoms, description, guidance, severity, red flags).",
          "The answer is saved automatically. Open History to search by symptom or condition, open a consultation, or delete it after confirming.",
          "About & metrics shows the pipeline and the evaluation figures shipped with the application (an upper bound; see Chapter 8). The sun/moon button switches the theme; Sign out ends the session.",
          "The information is preliminary and is not a diagnosis; in an emergency call the local emergency number."),
        H2("B.6 Tests and measurement scripts"),
        TAB("Scripts used for the tests and the measurements in this report", ["Command (from the project folder, inside `.venv`)", "Purpose"],
            [["`python -m pytest tests -v`", f"{F.PYTEST_TOTAL} unit and API tests"],
             ["`python scripts/smoke_test.py`", f"{F.SMOKE_TOTAL} end-to-end checks through the frontend proxy (app running)"],
             ["`python scripts/evaluate.py`", "The shipped evaluation (writes `results/metrics.json`; its protocol keeps the held-out record in the index)"],
             ["`python scripts/measure_metrics.py`", "Ablation, query sets, relevance, generator, safety and latency measurements (writes `docs/metrics/metrics.json`)"],
             ["`python scripts/measure_latency.py <label>`", "HTTP latency of the running API"],
             ["`python scripts/capture_docs_screens.py`", "Captures the screens in `docs/screenshots/` (needs `pip install playwright`; add `--echo` for the default-generator screen)"]],
            widths=[3.0, 3.3], align=["l", "l"], size=9.5),
        H2("B.7 Configuration"),
        TAB("Settings read from environment variables", ["Variable", "Default", "Meaning"], _env_rows(), widths=[2.2, 2.2, 1.9], align=["l", "l", "l"], size=9),
        H2("B.8 Troubleshooting"),
        B("**Python or Node not found:** reinstall with \"Add to PATH\" ticked and reopen the terminal.",
          f"**Port in use:** change `BACKEND_PORT` and `FRONTEND_PORT` in `.env` (and `CARELENS_PORT`), or close the program using {F.API_PORT} or {F.WEB_PORT}.",
          "**Slow first start or model download failure:** the models download once; with no network the application falls back to TF-IDF retrieval and evidence-based answers (weaker on paraphrased input).",
          "**The answer text is the prompt itself:** the default generator is affected by `transformers` 5; start the backend with `CARELENS_GENERATOR_MODEL` set to an unavailable id to use the evidence-based fallback, or install a 4.x version.",
          "**Docker not running:** start Docker Desktop and wait until it reports Running."),
    ]


def screens_blocks():
    names = APPENDIX_C
    caps = {
        "02_landing_dark.png": "Landing page, dark theme.",
        "03_landing_bottom_dark.png": "Bottom of the landing page (dark theme).",
        "04_register.png": "Create-account form (email and a password of 6 to 128 characters).",
        "10_history_search.png": "History filtered by the search term \"fever\": one consultation remains.",
        "12_delete_confirm.png": "Confirmation dialog before a consultation is deleted.",
        "14_about_dark.png": "About page, dark theme.",
        "15_mobile_assistant.png": "Symptom assistant at phone width (390 pixels).",
        "16_mobile_history.png": "History as cards at phone width.",
        "17_not_found.png": "Unknown route: the 404 screen.",
    }
    out = [H1("APPENDIX C: ADDITIONAL SCREENS"),
           P("These screens complete the set of captures described in Chapter 8: theme variants, registration, the search result, the delete confirmation, the phone-width layouts and the not-found page. "
             "All were captured from the running application on 2026-10-22.")]
    pairs = [names[i:i + 2] for i in range(0, len(names), 2)]
    for pr in pairs:
        w = 2.0 if any(n.startswith("1") and n[:2] in ("15", "16") for n in pr) else 2.8
        out.append(PAIR([_cap(n, caps[n]) for n in pr], w))
    return out
