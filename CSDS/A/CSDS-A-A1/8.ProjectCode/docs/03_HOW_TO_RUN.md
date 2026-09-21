# How to run PolicyLens

This guide takes a Windows 10/11 computer from nothing to a running PolicyLens. It takes about 15 minutes, most of which is downloads.

---

## 1. What you need

| Requirement | Version | How to check | Where to get it |
|---|---|---|---|
| Windows | 10 or 11, 64-bit | - | - |
| Python | **3.11** | `py -3.11 --version` | [python.org - Python 3.11.9](https://www.python.org/downloads/release/python-3119/): use the "Windows installer (64-bit)" and tick **Add python.exe to PATH** |
| Node.js | 20.19+ or 22+ (LTS) | `node --version` | [nodejs.org](https://nodejs.org) - the **LTS** download |
| Git | any | `git --version` | [git-scm.com](https://git-scm.com/download/win) (only to clone the code) |
| Disk space | about 3 GB free | - | - |
| Internet | needed for setup and for AI answers | - | - |
| Gemini API key | free | - | see step 3 |

8 GB of RAM is enough; 16 GB is comfortable. No graphics card is needed - all local models run on the CPU.

---

## 2. Get the code

If you already have the folder, skip this step. Otherwise clone your copy of the repository and open the
**project folder** - the one that contains `setup.bat`, `run.bat` and the `backend` and `frontend` folders:

```bat
git clone <repository-url>
cd <path-to-the-project-folder>
```

All commands below are run from this project folder.

---

## 3. Get a free Gemini API key

PolicyLens uses Google Gemini to read policies and write answers.

1. Open **https://aistudio.google.com/apikey** and sign in with any Google account.
2. Accept the terms if asked, then click **Create API key** (choose the default project if asked).
3. Copy the key that appears.

You will paste it in step 5.

---

## 4. Run the one-time setup

Double-click **`setup.bat`** in the project folder, or run it from Command Prompt:

```bat
setup.bat
```

It will:

1. check Python 3.11 and Node.js,
2. create a Python environment (`venv\`) and install the backend packages (about 1 GB the first time),
3. create `.env` from `.env.example` with a random login secret,
4. download the three local AI models into `models\hf\` (about 480 MB),
5. install the frontend packages (`frontend\node_modules\`),
6. create the database, the demo account and the four sample policies, and build their search index.

When it finishes you will see **Setup complete. Start PolicyLens with run.bat**.

If anything fails, the message says what is missing; see [10_TROUBLESHOOTING.md](10_TROUBLESHOOTING.md).

---

## 5. Add your Gemini key

1. Open the file **`.env`** in the project folder with Notepad or VS Code.
2. Find the line `GEMINI_API_KEY=` and paste your key straight after the `=` (no spaces, no quotes).
3. Save the file.

Optional check - this sends three tiny test requests:

```bat
venv\Scripts\python scripts\check_gemini.py
```

---

## 6. Start PolicyLens

Double-click **`run.bat`**. It:

1. checks that ports **8101** (API) and **5101** (web app) are free,
2. opens two windows - *PolicyLens API* and *PolicyLens Web*,
3. waits until both are ready and opens **http://localhost:5101** in your browser.

The first start takes 20-40 seconds while the local models load.

| What | Address |
|---|---|
| Web app | http://localhost:5101 |
| API documentation (Swagger) | http://localhost:8101/docs |
| Health check | http://localhost:8101/api/health |

---

## 7. First login

Use the demo account, which already has four sample policies:

| Email | Password |
|---|---|
| `demo@policylens.app` | `Demo@12345` |

Or click **Get started** to create your own account, then use **My policies -> Sample policies** or **Upload policy**.

Try this sequence:

1. **My policies** -> open *Family Health Optima* -> look at the **Policy Card** and **Risks**.
2. **Ask this policy** -> "Is cataract surgery covered and after how long?" -> click a citation number to see the clause highlighted on its page.
3. **Claim Copilot** -> choose the policy -> "Knee replacement" -> add a policy start date and an estimated bill -> **Check my claim**.
4. **Compare plans** -> choose two policies -> **Compare**.
5. **Settings** -> answer language **हिन्दी** -> ask another question.

---

## 8. Stop PolicyLens

Close the two PolicyLens windows, or double-click **`stop.bat`** (it stops only the processes on ports 8101 and 5101, so other programs are not affected).

---

## 9. Reset to a clean state

To delete all accounts, uploads, conversations and claim checks on this computer and recreate the demo account with the sample policies:

```bat
scripts\reset.bat
```

Type `RESET` to confirm. Your `.env` and the downloaded models are kept.

---

## 10. Use it from a phone on the same Wi-Fi

The web app also listens on your network address. When `run.bat` starts, the *PolicyLens Web* window prints a line such as `Network: http://192.168.0.108:5101/`. Open that address on a phone connected to the same Wi-Fi. If it does not load, allow **Node.js** through Windows Defender Firewall for private networks.

---

## 11. Run the evaluation (optional)

To re-measure retrieval, answer, claim and extraction quality (see [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md)), stop PolicyLens first, then:

```bat
venv\Scripts\python ml\run_all.py
```

Results appear in `experiments\eval-YYYYMMDD-HHMM\` and on the **Model performance** page.

---

## 12. Run the tests (optional)

```bat
cd backend
..\venv\Scripts\python -m pytest
cd ..\frontend
npm run build
```

See [09_TESTING.md](09_TESTING.md).
