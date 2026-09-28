# How to run MediQueue

## Requirements

- Windows 10/11
- Python 3.11+ (https://www.python.org/downloads/ - tick "Add python.exe to PATH")
- Node.js LTS (https://nodejs.org/)
- Optional: a Google Gemini API key for free-text symptom mapping - https://aistudio.google.com/apikey
- Optional (phone access): `cloudflared` - `run_phone.bat` installs it with winget if missing

## 1. Set up (once)

```bat
cd 8.ProjectCode
setup.bat
```

This creates `venv\`, installs the Python packages, creates `.env` from `.env.example` with a random JWT secret, and
installs the frontend packages.

Optional: open `.env` and set `GEMINI_API_KEY=...`. Without it, typed symptoms are matched with the built-in keyword
matcher (the booking screen says which one was used).

All datasets and the trained models are already in the folder - no download is needed.

## 2. Start

```bat
run.bat
```

Two windows open - API on http://localhost:8215 (docs at `/docs`) and web app on http://localhost:5215 - and the
browser opens. The database `data\app.db` is created and seeded on first start.

## 3. Log in (password `demo1234` for all)

| Role | Email |
|---|---|
| Patient | `patient@mediqueue.app` |
| Hospital OP desk | `desk<id>@mediqueue.app` - e.g. `desk1@mediqueue.app` (one per hospital) |
| District admin (dashboard + any hospital's console) | `admin@mediqueue.app` |

The login page also has one-click demo buttons. Patients can create their own account.

## 4. Use it on a phone

```bat
run_phone.bat
```

Starts everything plus a free Cloudflare quick tunnel and prints a link like
`https://something.trycloudflare.com`. Open it on the phone (any network). Keep the window open. No account needed.

## 5. Demo walkthrough

1. **Patient (phone):** Book a visit -> type `fever, cough, breathlessness` -> *Match my description* -> *Check
   severity* -> **Severe**, Pulmonology -> area Ameerpet -> *Suggest hospitals* -> 3 hospitals on the map -> *Book
   token* -> token page with position and estimated wait.
2. **Admin or desk (laptop):** Hospital console -> pick the same hospital -> *Call next* and *Add emergency*; the
   phone's position and wait update instantly.
3. **Full day:** in the console, *Limits* -> set Daily OP limit to `5` (below today's bookings) -> book again as
   the patient for today: the booking moves to the next day automatically (the token page says why). Set the limit
   back afterwards.
4. **Referral:** console -> *Refer* on the patient -> Pulmonology -> choose hospital -> send. Patient -> Referrals ->
   consent. Log in as that hospital's desk (or admin) -> Referrals -> *Accept and book* -> *Mark completed*.
5. **District dashboard (admin):** load map, waits, severity mix, next-day moves and referrals.

## 6. Checks

```bat
REM with the backend running
venv\Scripts\python scripts\smoke_test.py

REM frontend production build
cd frontend && npm run build
```

## 7. Retrain and evaluate (optional)

```bat
venv\Scripts\python ml\train_triage.py
venv\Scripts\python ml\train_noshow.py
venv\Scripts\python ml\eval.py          REM writes experiments\eval\metrics.json (about 1 minute)
```

Refresh data: `venv\Scripts\python scripts\download_data.py` (Kaggle), `python scripts\fetch_hospitals.py`
(OpenStreetMap), then `python scripts\build_network.py`. Delete `data\app.db` to reseed.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Port 5215 is already in use` / 8215 busy | Close the old MediQueue windows (or another app using the port) and run again |
| "Cannot reach the server" in the app | The API window must be running; check it for errors |
| Phone link shows an error for the first seconds | Wait 10-20 s after the link appears and reload |
| Want a clean start | Stop the app, delete `data\app.db`, start again |
