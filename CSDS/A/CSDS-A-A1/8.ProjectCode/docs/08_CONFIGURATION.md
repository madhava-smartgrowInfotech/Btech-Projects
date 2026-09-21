# Configuration

All settings live in **`.env`** in the project folder. `setup.bat` creates it from **`.env.example`** the first time and fills in a random `JWT_SECRET`. `.env` is git-ignored - never commit it. Restart PolicyLens (`stop.bat`, then `run.bat`) after changing it.

| Key | Default | Required | What it does | How to get / choose it |
|---|---|---|---|---|
| `GEMINI_API_KEY` | *(empty)* | **Yes** for AI features | Key for the Google Gemini API: Policy Card extraction, answers, Claim Copilot, comparisons, translations | Free at **https://aistudio.google.com/apikey** -> *Create API key* -> copy. Without it, upload, search, the document viewer and the faithfulness checker still work, and the Policy Card shows how to add a key. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Yes | Main model | Any model your key can use; `venv\Scripts\python scripts\check_gemini.py` lists them. Current list: https://ai.google.dev/gemini-api/docs/models |
| `GEMINI_LITE_MODEL` | `gemini-3.5-flash-lite` | Yes | Fast model for translating Hindi/Telugu questions into English search queries | A Flash-Lite model |
| `GEMINI_FALLBACK_MODELS` | `gemini-3.6-flash,gemini-3.5-flash-lite` | No | Models tried in order when the main one is overloaded (503/504) or out of quota (429). An unavailable model is skipped for 10 minutes. | Comma-separated; empty disables fallback |
| `GEMINI_TIMEOUT_SECONDS` | `90` | No | Maximum wait for one Gemini response | Raise on slow connections |
| `LLM_MAX_RPM` | `10` | No | Requests per minute PolicyLens sends to Gemini (it waits rather than exceeding it) | At or below your key's limit, shown in AI Studio -> *Dashboard -> Rate limits* |
| `EMBEDDING_PROVIDER` | `local` | No | Dense retrieval embeddings: `local` = all-MiniLM-L6-v2 on the CPU (offline, no quota); `gemini` = `GEMINI_EMBEDDING_MODEL` through the API | Changing it creates a separate vector collection; re-index by running `scripts\reset.bat` |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | No | Embedding model when `EMBEDDING_PROVIDER=gemini` | |
| `SUPPORTED_LANGUAGES` | `en,hi,te` | No | Answer languages offered in Settings and chat | Any of `en` (English), `hi` (Hindi), `te` (Telugu) |
| `JWT_SECRET` | *(random, set by setup)* | Yes | Signs login tokens | Any long random string; changing it signs everyone out |
| `JWT_EXPIRE_MINUTES` | `1440` | No | How long a login lasts (24 hours) | |
| `BACKEND_PORT` | `8101` | No | API port | Fixed for PolicyLens so it can run beside other products; change only if something else must use 8101 |
| `FRONTEND_PORT` | `5101` | No | Web app port (Vite uses `strictPort`, so it fails clearly instead of picking another port) | Same as above |
| `CORS_ORIGINS` | `http://localhost:5101,http://127.0.0.1:5101` | No | Browser origins allowed to call the API directly | Add origins if you serve the web app elsewhere |
| `DATA_DIR` | `data` | No | Folder for the database, vector index, uploads, page images and AI cache | Relative to the project folder or absolute |
| `MODELS_DIR` | `models` | No | Folder for the downloaded local models (`models\hf\`) | |
| `MAX_UPLOAD_MB` | `25` | No | Largest PDF accepted | |
| `LOG_LEVEL` | `INFO` | No | Backend log detail: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Logs go to the API window and `logs\backend.log` | |
| `DEMO_EMAIL` | `demo@policylens.app` | No | Demo account created on first start (owns the labelled sample policies) | |
| `DEMO_PASSWORD` | `Demo@12345` | No | Its password | Change it if others can reach this computer |

## Other configuration files

| File | Purpose |
|---|---|
| `frontend/vite.config.ts` | Reads `FRONTEND_PORT`/`BACKEND_PORT` from `.env`; proxies `/api` to the backend; `strictPort: true` |
| `models/manifest.json` | Exact Hugging Face model IDs and revisions downloaded by `scripts\download_models.py` |
| `backend/requirements.txt` | Python packages |
| `frontend/package.json` | Web app packages |
| `backend/pytest.ini` | Test settings |

## Checking the configuration

- `venv\Scripts\python scripts\check_gemini.py` - verifies the key, lists available Flash models and tests JSON output in Hindi and Telugu.
- http://localhost:8101/api/health - database, vector store, local models, Gemini configuration and which models are currently available.
