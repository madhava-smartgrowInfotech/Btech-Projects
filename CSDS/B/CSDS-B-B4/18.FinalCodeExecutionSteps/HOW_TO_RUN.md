# 03 · How to run UPI Guardian

Everything runs on one Windows 10/11 PC. Setup is one command, starting is one command.

---

## 1. What you need (install once)

| Tool | Version | How to get it |
|---|---|---|
| **Python** | 3.11 (64-bit) | https://www.python.org/downloads/release/python-3119/ → *Windows installer (64-bit)*. In the installer tick **"Add python.exe to PATH"**, then *Install Now*. |
| **Node.js** | LTS (22 or newer) | https://nodejs.org → download the **LTS** installer → Next, Next, Finish. |
| **Git** | any recent | https://git-scm.com/download/win (only needed to download the code). |
| **cloudflared** *(only for phones)* | any recent | Open *PowerShell* and run `winget install --id Cloudflare.cloudflared` |

Check them in a new *Command Prompt*:

```bat
py -3.11 --version
node --version
```

Disk space: about 3 GB after setup. Internet is needed during setup and for spoken phrases that
are not pre-recorded.

## 2. One-time setup

1. Open the project folder `8.ProjectCode` (next to this folder) in File Explorer.
2. Double-click **`setup.bat`** (or run it from a Command Prompt in this folder).

`setup.bat` will:

| Step | What happens |
|---|---|
| 1 | Checks Python 3.11 and Node.js |
| 2 | Creates the Python virtual environment `venv\` and installs `backend\requirements.txt` |
| 3 | Creates `.env` from `.env.example` with a new random `JWT_SECRET` (an existing `.env` is never overwritten) |
| 4 | Runs `npm install` in `frontend\` |
| 5 | Confirms the trained models in `models\` (trains them if they are missing) |
| 6 | Checks the pre-recorded voice phrases |

It takes about **2–5 minutes** and ends with `Setup complete.`

> To also install the packages for **retraining** the models (PyTorch CPU, sentence-transformers),
> run `setup.bat train` instead.

## 3. Start

Double-click **`run.bat`**. It:

1. starts the API in a window titled **UPI Guardian API (8204)**,
2. starts the web app in a window titled **UPI Guardian Web (5204)**,
3. opens **http://localhost:5204** in your browser.

The first start creates the database `data\app.db` and loads the sample accounts and history
(about 10 seconds).

| Address | What |
|---|---|
| http://localhost:5204 | The web app |
| http://localhost:5204/docs (or http://127.0.0.1:8204/docs) | Interactive API documentation |
| http://127.0.0.1:8204/api/health | Health check (shows which models are loaded) |

## 4. Sign in

On the sign-in page, press **Use** next to a sample account, or type:

| Account | Sign in with | Password | Sandbox UPI PIN |
|---|---|---|---|
| Everyday user (Meera Sharma) | `demo@upiguardian.app` or `9000000001` | `Guardian@123` | `1234` |
| Family member / trusted contact (Arjun Sharma) | `family@upiguardian.app` or `9000000002` | `Guardian@123` | `1234` |
| Fraud-risk team (admin) | `admin@upiguardian.app` or `9000000009` | `Admin@1234` | `1234` |

You can also create your own account (**Create an account**) — every new wallet gets ₹50,000 of
sandbox money.

## 5. Try the four demo scenarios

| # | Do this | You should see |
|---|---|---|
| 1 | As Meera: **Send money** → tap **Ravi (friend)** → ₹800 → *Check and pay* | *This payment looks safe* (Low) → *Pay ₹800* → PIN `1234` → *Payment sent* |
| 2 | **SMS check** → paste `Your KYC expires today, click link http://kyc-verify-now.top/a77 to update or your account will be blocked.` → *Check message*; switch the language (文A icon) to **हिन्दी** and press **सुनें** | Verdict **Scam** (fake KYC), highlighted phrases, and the warning spoken in Hindi |
| 3 | **Settings → Sandbox clock** → set `01:30` → *Use this time*. **Send money** → UPI ID `vikram.4411@upg`, ₹25,000 → *Check and pay* | **High risk** with reasons (new 12-day-old account, 54× usual amount, 01:30 at night); open *How the model decided* for the SHAP bars; the safety check; after the PIN the payment is **held** — press *Cancel this payment* |
| 4 | **Requests** → the request from **Refund Desk** ("Refund … approve to receive") | Red banner **Approving will DEBIT ₹4,999**, deceptive words highlighted; *Review and pay* shows the collect-request guard as the first reason |

Afterwards, set the sandbox clock back with **Use real time**.

## 6. On an Android phone (installable app)

Camera scanning and app installation need a secure (https) address. `run_phone.bat` provides one.

1. Install cloudflared once: `winget install --id Cloudflare.cloudflared`
2. Close any running UPI Guardian windows (or run `stop.bat`).
3. Double-click **`run_phone.bat`**. It builds the web app, starts it, opens a Cloudflare quick
   tunnel and prints a link like `https://something-random.trycloudflare.com` (plus a QR code of it).
4. On the phone, open that link in **Chrome**.
5. To install: Chrome menu (⋮) → **Add to Home screen / Install app**, or tap **Install app** in the
   app's top bar when it appears.
6. Keep the `run_phone.bat` window open while you use the phone. The link changes every time the
   tunnel starts — open the new link and install again if needed.

No Cloudflare account is needed.

## 7. Stop

- Close the two server windows, **or**
- double-click **`stop.bat`** — it stops only the processes on ports 8204 and 5204 (and the phone
  tunnel), nothing else.

## 8. Reset the sandbox

Any of these gives you a fresh copy of the sample data:

- Sign in as the **admin** → *Sandbox tools* → **Reset sandbox**, **or**
- stop UPI Guardian, delete `data\app.db` (and `app.db-wal`, `app.db-shm` if present), start again.

## 9. Retrain the models (optional)

```bat
setup.bat train
venv\Scripts\python ml\train_all.py
```

About 15 minutes on a 6-core CPU. It rewrites `experiments\` and `models\`; restart `run.bat`
afterwards. See [05_MODELS_AND_TRAINING.md](../8.ProjectCode/docs/05_MODELS_AND_TRAINING.md).

## 10. Run the tests

```bat
cd backend
..\venv\Scripts\python -m pytest
cd ..\frontend
npm run build
```

See [09_TESTING.md](../8.ProjectCode/docs/09_TESTING.md). If something does not work, see
[10_TROUBLESHOOTING.md](../8.ProjectCode/docs/10_TROUBLESHOOTING.md).
