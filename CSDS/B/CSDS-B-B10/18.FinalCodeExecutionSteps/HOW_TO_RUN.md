# How to run SkyCipher

## Requirements

- Windows 10/11
- Python 3.11 or newer - https://www.python.org/downloads/ (tick "Add python.exe to PATH")
- Node.js LTS (20 or newer) - https://nodejs.org/
- Optional: a webcam for the live link

No API keys are needed. The sample data is already in `data/sample/`.

## First run

1. Open the `8.ProjectCode` folder.
2. Double-click **`setup.bat`** (one time, takes a few minutes). It creates `venv/`, installs the Python
   packages, installs the frontend packages and creates `.env` with a random login secret.
3. Double-click **`run.bat`**. Two windows open (API on port **8210**, web app on port **5210**) and the
   browser opens http://localhost:5210.
4. Sign in with the demo account (pre-filled on the sign-in page):
   - Email: `demo@skycipher.app`
   - Password: `SkyCipher@2026`

To stop SkyCipher, close the two server windows.

## Manual start (without the .bat files)

```bat
python -m venv venv
venv\Scripts\pip install -r backend\requirements.txt
copy .env.example .env            &:: then set JWT_SECRET to a long random string
cd frontend && npm install && cd ..

cd backend && ..\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8210
:: in a second window
cd frontend && npm run dev
```

## Demo walkthrough

1. **Image studio** - pick a drone image, press *Encrypt*. The cipher looks like noise and its histogram is
   flat. Press *Decrypt*: "Checksum matches". Press *Try a key with 1 bit flipped*: decryption fails.
2. **Security lab** - press *Run security analysis*: entropy ~7.999, NPCR ~99.61 %, UACI ~33.46 %,
   correlation ~0. Press *Run attack tests* to see how much survives noise and cropping. Export the report
   as HTML.
3. **Live link** - press *Connect* on the ground station, then *Start transmission* on the sender.
   Encrypted frames stream in with FPS, latency and throughput. Press *Flip 1 bit* on the ground station
   key and reconnect: frames turn to noise.
4. **Benchmark** - press *Run benchmark* to compare with AES-256-CTR and ChaCha20.

## Checks

```bat
:: with the backend running
venv\Scripts\python scripts\smoke_test.py      &:: end-to-end API test, prints ALL SMOKE TESTS PASSED
venv\Scripts\python ml\eval.py                 &:: evaluation -> experiments\eval\metrics.json
cd frontend && npm run build                   &:: production build
```

## Data

`data/sample/` already holds 60 VisDrone images, 2 short drone sequences and 6 USC-SIPI test images.
To rebuild it: `venv\Scripts\python scripts\download_data.py`. For the full 2.16 GB VisDrone dataset:
`venv\Scripts\python scripts\download_data.py --full` (goes to `data/raw/`, not committed). If Kaggle asks
for credentials, set `KAGGLE_USERNAME` and `KAGGLE_KEY` in `.env` (https://www.kaggle.com/settings -> API).

## Troubleshooting

| Problem | Fix |
|---|---|
| "Port 5210 is already in use" / API does not start | Another program uses the port. Close it, or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env`. |
| `Set JWT_SECRET in .env` | `.env` is missing or still has the placeholder - run `setup.bat` or set `JWT_SECRET`. |
| Sign-in page says "Session expired" | Sign in again (tokens last 12 hours). |
| Webcam does not start | Allow camera access in the browser, or use the drone sequence sender. |
| Live link shows noise | The ground station key differs from the sender key. |
