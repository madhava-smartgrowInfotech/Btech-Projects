# How to run ATHENA

## Requirements
- Windows with **Python 3.11+** and **Node.js 18+** on PATH
- About 1.5 GB free disk for the Python environment and packages
- Internet on the first run only (package install)

## Start it
Double-click **`run.bat`** (or run it from a terminal in this folder).

On a fresh checkout it first runs `setup.bat`, which:
1. creates the `venv/` Python environment and installs `requirements.txt`
2. generates the synthetic dataset and trains the triage model if `models/triage_model.joblib` is missing
3. generates the sample reports in `data/sample_reports/` if missing
4. runs `npm install` in `frontend/`

Then it starts the API on **http://localhost:8307** and the web app on **http://localhost:5307** in two minimised windows, and opens the browser. Close those two windows to stop.

## Sign in
| Role | Email | Password |
|---|---|---|
| Clinician | clinician@athena.health | Athena@123 |
| Admin | admin@athena.health | Athena@123 |

The login screen also has one-click demo buttons. A new database starts with 12 clearly labelled **sample cases** in the queue so the queue and performance pages are not empty.

## Try the demo
1. **New patient**, then pick a sample report from the list (for example `report 01 chest pain stemi`). The report is read, the vitals fill in, and the extracted findings appear with their page numbers.
2. **Assign priority**. The result page shows the priority, calibrated confidence, the fused record and the SHAP list of what drove it.
3. **Accept or change**. Change the priority with a reason. The queue reorders and the override is logged on the case.
4. **Performance** shows accuracy, per-priority recall, the confusion matrix and seconds per patient.

You can also upload your own PDF, PNG or JPG report.

## Checks
With both servers running (`run.bat`):
```
venv\Scripts\python scripts\smoke_test.py          # API flow end to end
venv\Scripts\python ml\eval.py                     # writes experiments\eval\metrics.json
python scripts\capture_screens.py                  # needs: pip install playwright
python scripts\check_responsive.py                 # 360 / 768 / 1440, light and dark, keyboard
cd frontend && npm run build                       # production build
```

## Retrain the model
```
venv\Scripts\python ml\make_data.py                # seeded synthetic dataset to data\sample\
venv\Scripts\python ml\train.py                    # writes models\ and experiments\metrics.json
```
Restart the API afterwards. Delete `data\app.db` to reset the queue and the review log.

## Settings
Ports are fixed: API 8307, web 5307 (set in `run.bat` and `frontend/vite.config.js`). `.env` is optional: `DATABASE_URL` and `JWT_SECRET` are read from it when present, otherwise safe local defaults apply.

## Troubleshooting
- **"Cannot reach the ATHENA API"** in the browser: the API window is not running. Run `run.bat` again and check the minimised "ATHENA API" window for errors.
- **Port already in use**: another copy is running. Close its windows first.
- **First scan is slow** (a few seconds): the OCR engine loads on first use. PDFs with a text layer are read instantly.
- **Package install fails**: check the connection and run `setup.bat` again.
