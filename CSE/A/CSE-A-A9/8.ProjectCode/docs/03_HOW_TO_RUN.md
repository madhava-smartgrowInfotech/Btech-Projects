# How to run BotGraph

BotGraph runs entirely on one Windows computer. It makes no calls to outside services, so the Gemini entries in
`.env.example` are not used.

## 1. What you need

- Windows 10 or 11
- **Python 3.11 or newer** (tick "Add python.exe to PATH" when installing) - https://www.python.org/downloads/
- **Node.js LTS** - https://nodejs.org/
- About 3 GB of free disk space (PyTorch is the big part) and an internet connection for the first setup

## 2. Start it

Open the `8.ProjectCode` folder and double-click **`run.bat`** (or run it from a terminal).

The first run calls `setup.bat` for you. It creates `.venv`, installs the Python packages (PyTorch downloads once and can
take several minutes) and installs the web app packages. Every later run starts in a few seconds.

When it is ready your browser opens on **http://localhost:5309**.

| Part | Address |
| --- | --- |
| Web app | http://localhost:5309 |
| API | http://127.0.0.1:8309 (interactive docs at `/docs`) |

Two minimised windows named *BotGraph API* and *BotGraph web app* keep it running. Close them to stop.

## 3. Demo login

Password for both accounts: **`Demo@1234`**

| Account | Email | Can do |
| --- | --- | --- |
| Moderator | `moderator@botgraph.app` | everything, including confirm / dismiss and retraining |
| Analyst | `analyst@botgraph.app` | explore accounts, botnets and model results (read-only) |

The sign-in page has a one-click demo button and fills the credentials for you.

## 3a. A five-minute tour

1. **Graph & features** - node and edge counts, which parts are real data, the 23 features.
2. **Models & scale** - the three architectures against the no-graph baseline; open *Scalability*.
3. **Accounts** - open the top account: its probability, the traits behind it, its neighbourhood graph.
4. **Botnet clusters** - open a coordinated cluster; the injected botnets come back as single communities.
5. **Moderator queue** - dismiss one member and confirm another; see both in the *Decision log*, then press *Retrain with decisions*.

## 4. Useful commands

Run these from the `8.ProjectCode` folder with the project environment (`.venv\Scripts\python`).

| What | Command |
| --- | --- |
| Rebuild the graph from the committed datasets | `.venv\Scripts\python -m ml.data` |
| Train all models and write `models/` and `experiments/metrics.json` | `.venv\Scripts\python -m ml.train` (a few minutes on CPU) |
| Scalability sweep and `experiments/eval/metrics.json` | `.venv\Scripts\python -m ml.eval` |
| End-to-end smoke test (uses its own scratch database and model copies) | `.venv\Scripts\python scripts\smoke_test.py` |
| Production build of the web app | `cd frontend` then `npm run build` |
| Refresh the raw datasets from Kaggle | `.venv\Scripts\python -m pip install kagglehub` then `.venv\Scripts\python scripts\download_data.py` |
| Re-capture the screenshots (app must be running) | `.venv\Scripts\python -m pip install playwright` then `.venv\Scripts\python scripts\capture_screens.py` |

The trained models, scores and clusters are committed, so nothing needs training before the first start.

## 5. Settings

`.env` (created from `.env.example` on first run):

| Key | Meaning |
| --- | --- |
| `BACKEND_PORT` | API port, 8309 |
| `FRONTEND_PORT` | web app port, 5309 |
| `DATABASE_URL` | SQLite file for users, decisions and retraining runs (`data/app.db`, created on first start) |
| `JWT_SECRET` | signs the login tokens; replace the placeholder with a long random string for anything beyond a local demo |

## 6. If something goes wrong

| Symptom | Fix |
| --- | --- |
| `Python ... was not found` | Install Python 3.11+, tick *Add to PATH*, open a new terminal, run `setup.bat` again |
| Setup stops while installing PyTorch | Check your connection and run `setup.bat` again; it resumes |
| The page says *API offline* | The API window closed or its port is busy. Close both BotGraph windows and run `run.bat` again |
| `Port 5309 is already in use` | Another copy is running. Close the old windows, or change `FRONTEND_PORT` / `BACKEND_PORT` in `.env` |
| Sign-in says the password is wrong | Use `Demo@1234`. If you changed users, delete `data/app.db` and restart to re-create the demo accounts |
| Want to wipe moderator decisions | Stop the app, delete `data/app.db`, start again |
