# APISentry — How to run

## Prerequisites
- **Python 3.11+**
- **Node.js LTS** (18+) and npm
- Windows (scripts are `.bat`); the commands also work cross-platform if you run
  the equivalent shell commands.

## 1. Setup (one time)
From this folder (`8.ProjectCode`):

```bat
setup.bat
```

This creates a Python virtual environment, installs backend and frontend
dependencies, and creates `.env` from `.env.example`.

**Optional — enable Gemini for AI tests (F4):** get a free key at
https://aistudio.google.com/apikey and set `GEMINI_API_KEY` in `.env`.
Without a key, APISentry uses a built-in test generator, so everything still works.

## 2. Run everything

```bat
run.bat
```

This starts, in separate windows:
- DemoPay practice target — http://localhost:12130
- VulnBank practice target — http://localhost:12131
- Backend API — http://localhost:8213
- Frontend — http://localhost:5213 (opens in your browser)

**Demo login:** `demo@apisentry.local` / `demo12345`

Close the four opened windows to stop the services.

## 3. Try the demo flow
1. Sign in with the demo login.
2. On **Targets**, you'll see **DemoPay** and **VulnBank** pre-loaded.
3. Click **Scan** on DemoPay and confirm you're authorised → the scan runs.
4. On **Results** you'll see a score of **38/100 (grade D)** with 12 findings,
   including **BOLA on `/accounts/{account_id}`** and a **missing rate limit on
   `/login`**, each with evidence, a curl reproduction and a fix.
5. Open the **AI tests** tab → **Generate & run** to see business-logic tests
   (negative amount, foreign-account transfer, replayed payment).
6. Open the **Validation** tab → detection rate vs the known-vulnerability list.
7. Open the **Report** tab → view the HTML report or download the PDF.

## 4. CLI (for CI/CD, F7)
```bat
venv\Scripts\python.exe apisentry.py scan ^
  --spec targets\demopay_openapi.json ^
  --auth targets\demopay_vulns.json ^
  --known targets\demopay_vulns.json ^
  --fail-on high
```
Exits with code **1** when a finding at or above the chosen severity is present
(so a build pipeline fails). Add `--report out.html` or `--json out.json` to save.
The DemoPay/VulnBank targets must be running (via `run.bat`).

## 5. Tests & evaluation
- **Smoke test** (backend must be running via `run.bat`):
  ```bat
  venv\Scripts\python.exe scripts\smoke_test.py
  ```
- **Evaluation** (targets must be running):
  ```bat
  venv\Scripts\python.exe ml\eval.py
  ```
  Writes `experiments/eval/metrics.json`.
- **Frontend production build:**
  ```bat
  cd frontend && npm run build
  ```

## Troubleshooting
- **Port already in use** — change `BACKEND_PORT` / `FRONTEND_PORT` /
  `DEMOPAY_PORT` / `VULNBANK_PORT` in `.env`, then re-run `run.bat`.
- **"Out of scope" / scan blocked** — the target host must be in
  `SCOPE_ALLOWLIST` in `.env` (localhost is allowed by default).
- **AI tests say generator "builtin"** — set `GEMINI_API_KEY` in `.env` to use
  Gemini; the built-in generator is the intended fallback.
