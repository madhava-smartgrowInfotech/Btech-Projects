# UniHealth - How to run

## Requirements
- Windows 10/11
- Python 3.11 or newer - https://www.python.org/downloads/ (tick "Add python.exe to PATH")
- Node.js LTS (20 or newer) - https://nodejs.org/
- A Gemini API key for the AI assistant - https://aistudio.google.com/apikey

## 1. Set up (once)
Open the `8.ProjectCode` folder and double-click **`setup.bat`**, or run it in a terminal:
```
setup.bat
```
It creates `venv`, installs the Python packages and runs `npm install`. It also builds the three hospital databases
from the committed Synthea sample (`scripts/seed_hospitals.py`, seed 42) and trains the models if they are missing.
It takes about 3-5 minutes.

## 2. Add your keys
`setup.bat` creates `.env` from `.env.example`. Open `.env` and set:
```
GEMINI_API_KEY=your-key-from-aistudio.google.com
JWT_SECRET=any-long-random-text
HOSPITAL_SHARED_SECRET=another-long-random-text
```
Everything else has working defaults. Without a Gemini key every feature works except the assistant, which shows a
clear "not configured" message.

## 3. Start
Double-click **`run.bat`**. It opens five minimised windows:
- the three hospital FHIR servers on ports 12061, 12062 and 12063
- the API on port 8206
- the web app on port 5206

When everything is ready, it opens http://localhost:5206. To stop UniHealth, close the five "UniHealth" windows.

## 4. Demo logins (password `demo123`)
| Username | Role |
|---|---|
| `patient` | Patient with records at all three hospitals |
| `patient2`, `patient3` | Patients at two hospitals / one hospital |
| `dr.riverside` (also `dr.northbridge`, `dr.lakeview`) | Doctor at that hospital |
| `staff.lakeview` (also `staff.northbridge`, `staff.riverside`) | Hospital records staff |
| `admin` | Platform administrator |

## 5. Demo walkthrough
1. Sign in as **patient**. You see one timeline built from three hospitals, with each hospital's local ID and match confidence.
2. Sign in as **dr.riverside**, search `Gibson`, and click **Request history**. Access is blocked because there is no consent.
3. As **patient**, open **Consents**. The request appears under "Access requests". Click **Approve**.
4. As **dr.riverside**, click **Request history** again. The merged record loads. Click **Assess risk** to see heart-disease and diabetes risk with reasons.
5. As **patient**, click **Revoke**. The doctor's next request fails. Open **Audit & consent log**: the ledger shows every access and verifies intact.
6. As **patient**, open **Assistant**, choose **Telugu** and click **Explain latest lipid panel**.
7. As **staff.lakeview**, pick the patient, record a visit and click **Record visit & sync summary**. The patient's reminders now include the follow-up and medication.

## 6. Tests and evaluation
With `run.bat` running:
```
venv\Scripts\python scripts\smoke_test.py     # end-to-end API test (F1-F8)
venv\Scripts\python ml\eval.py                # writes experiments\eval\metrics.json
cd frontend && npm run build                  # production build check
```
To retrain the models, run `venv\Scripts\python ml\train.py`, which writes `models\*.joblib` and `experiments\metrics.json`.
To reset the hospitals to the original sample, delete `data\hospital_*.db` and `data\app.db`, then run `run.bat`.

## Troubleshooting
| Problem | Fix |
|---|---|
| "Port 5206 is already in use" | Another copy is running - close the old "UniHealth" windows |
| Hospital shows "offline" | Its window was closed. Re-run `run.bat` |
| Assistant says "not configured" or "401" | Put a valid key in `GEMINI_API_KEY` in `.env` and restart `run.bat` |
| `python` not found | Reinstall Python with "Add to PATH" ticked |
