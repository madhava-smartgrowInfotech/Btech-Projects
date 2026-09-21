# Troubleshooting

## Setup

| Problem | Fix |
|---|---|
| `Python 3.11 was not found` | Install Python 3.11 (64-bit) from https://www.python.org/downloads/release/python-3119/ and tick **Add python.exe to PATH**. Other Python versions can stay installed - setup uses `py -3.11`. |
| `Node.js was not found` | Install the LTS version from https://nodejs.org, close and reopen Command Prompt, run `setup.bat` again. |
| `pip install` fails with a network or SSL error | Check the internet connection or proxy, then run `setup.bat` again - it resumes. |
| `Microsoft Visual C++ ... is required` | Install the "Microsoft Visual C++ Redistributable (x64)" from Microsoft, then rerun setup. |
| Model download fails (`download_models.py`) | Temporary Hugging Face issue or blocked network. Run `venv\Scripts\python scripts\download_models.py` again. |
| `npm ci` fails | Delete `frontend\node_modules` and run `setup.bat` again; setup falls back to `npm install`. |

## Starting

| Problem | Fix |
|---|---|
| `Port 8101 is already in use` / `Port 5101 is already in use` | PolicyLens may already be running - run `stop.bat`. If another program uses the port, change `BACKEND_PORT`/`FRONTEND_PORT` in `.env`. |
| `http://127.0.0.1:8101/api/health did not respond` | Look at the *PolicyLens API* window for the error. The most common cause is a missing package - run `setup.bat` again. |
| The browser shows "Can't reach the PolicyLens server" | The API window was closed or crashed. Run `stop.bat`, then `run.bat`. |
| The first question takes 20-40 seconds | The local models are still loading after start-up. Later questions are faster. |

## AI features

| Problem | Fix |
|---|---|
| "No Gemini API key is configured" | Paste your key into `GEMINI_API_KEY` in `.env` and restart. Check with `venv\Scripts\python scripts\check_gemini.py`. |
| "The Gemini free-tier limit has been reached for now" | Free keys have per-minute and per-day limits. Wait a minute (or until tomorrow for the daily limit). Lower `LLM_MAX_RPM` if it happens often. Your limits: AI Studio -> Dashboard -> Rate limits. |
| "The AI service is busy right now" | Google's models are overloaded. PolicyLens already tries the fallback models; try again in a minute. `http://localhost:8101/api/health` shows which models are cooling down. |
| Answers come from a Flash-Lite model | The main model was overloaded or out of quota, so the fallback answered. The model name is shown under each answer. |
| Policy Card says it could not be built | Open the policy and click **Build Policy Card** / **Re-run AI extraction** once the AI service is available. |
| Hindi or Telugu text shows as boxes | The page loads Noto fonts for both scripts; refresh the page. On very old browsers, update the browser. |

## Documents

| Problem | Fix |
|---|---|
| "This PDF has no readable text layer" | The file is a scan. Download the insurer's original policy wording PDF (text you can select). |
| "This PDF is password-protected" | Save an unlocked copy (open it with the password and print to PDF), then upload that. |
| "This policy is already in your library" | The same PDF (by content) is already uploaded; open the existing one. |
| Highlight is slightly off on a page | Highlights come from the text positions in the PDF; some PDFs draw text in unusual orders. The clause text in the side panel is always exact. |
| Processing is stuck | Processing runs in the API; if the API was restarted mid-way it resumes automatically on the next start. Check the API window for errors. |

## Data

| Problem | Fix |
|---|---|
| Start again from a clean state | `scripts\reset.bat` (type `RESET`). Keeps `.env` and the models. |
| Moved the project folder | Nothing to change - all paths are relative to the project folder. |
| Search results look stale after changing `EMBEDDING_PROVIDER` | Run `scripts\reset.bat` so every policy is re-indexed with the new embeddings. |

## Logs

- Backend: the *PolicyLens API* window and `logs\backend.log` (one line per request and per AI call, with model and timing).
- Web app: the *PolicyLens Web* window and the browser's developer console (F12).
