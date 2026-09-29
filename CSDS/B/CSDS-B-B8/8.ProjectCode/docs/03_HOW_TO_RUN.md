# CareWatch - How to run

## Requirements
- Windows 10/11, **Python 3.11**, **Node.js 18+ (LTS)**, Git
- A webcam, or an Android phone with the free **IP Webcam** app on the same Wi-Fi
- Optional, for alert delivery: a Telegram bot token and a Gmail app password (see `docs/ALERTS_SETUP_WARNING.md`)

## 1. One-time setup
Double-click **`setup.bat`**, or run from the `8.ProjectCode` folder:
```bat
setup.bat
```
This creates `venv\`, installs the CPU build of PyTorch and the Python packages in `requirements.txt`, and runs
`npm install` in `frontend\`. It takes about 5-10 minutes the first time.

`.env` is already included. For alert delivery, fill in `TELEGRAM_BOT_TOKEN`, `SMTP_USER` and `SMTP_PASSWORD`.

## 2. Start
Double-click **`run.bat`**. It starts:
- the backend: http://127.0.0.1:8208 (API docs at http://127.0.0.1:8208/docs)
- the frontend: http://localhost:5208 (opens in your browser)

**Demo login:** `demo@carewatch.app` / `CareWatch123` (or create your own account).

## 3. Use it
1. **Contacts & settings.** Add family members (email and/or Telegram chat ID). "Look up chats" finds the chat
   IDs of people who have messaged your bot.
2. **Live monitor.** Pick the camera source, then press **Start monitoring**:
   - `0` means this computer's webcam.
   - For a phone, open IP Webcam, tap *Start server*, and enter `http://<phone-ip>:8080/video`.
   - Without a camera, use the sample video: `data/sample/demo_fall.mp4` (full path, e.g. `D:\...\8.ProjectCode\data\sample\demo_fall.mp4`).
3. Walk, sit, drink water. The activity and timeline update live, and only the skeleton is shown.
4. **Simulated fall.** Drop onto a mat and stay still. After about 3 s a red countdown appears on every screen.
   Press **I'm OK** to cancel. If nobody presses it, Telegram and email alerts go out with a snapshot.
5. Dim the lights. The *Low-light enhancement on* badge appears and recognition continues.
6. **Daily report** shows time per activity and inactivity warnings. For a quick demo, set *Inactivity warning*
   to 0.5 min and sit still.

Monitoring keeps running while the browser is closed. It also resumes after a restart if it was running.

## 4. Re-train and evaluate (optional)
```bat
venv\Scripts\activate
python scripts\download_data.py         :: full HAR images -> data\raw\har (the CCTV and fall sets are committed)
python ml\extract_keypoints.py          :: YOLO11n-pose keypoints -> data\keypoints\poses.npz (~15-30 min CPU)
python ml\train.py                      :: activity model -> models\activity_rf.joblib, experiments\metrics.json
python ml\eval.py                       :: evaluation -> experiments\eval\metrics.json
python scripts\make_demo_video.py       :: rebuilds data\sample\demo_fall.mp4
```
Clips recorded on the Live monitor (keypoints only) are saved in `data\own_clips\<label>\`. `ml\train.py`
includes them automatically.

## 5. Smoke test
With the backend running:
```bat
venv\Scripts\python scripts\smoke_test.py
```
It drives the real API end to end: login, contacts, monitoring on the sample video, a fall, 'I'm OK', a second
fall, the countdown running out, alert dispatch, the report and metrics. It ends with `SMOKE TEST PASSED`.

## Troubleshooting
| Problem | Fix |
|---|---|
| "Could not open camera source" | Close other apps that use the webcam, try `1` instead of `0`, or check the phone URL in a browser. |
| Port 8208 / 5208 already in use | Another CareWatch window is open. Close it, or change `BACKEND_PORT` / `FRONTEND_PORT` in `.env` (and in `run.bat`). |
| Alerts show "undelivered" | Telegram/Gmail keys are not set in `.env` (see `docs/ALERTS_SETUP_WARNING.md`), or there are no active contacts. |
| Gmail "Username and Password not accepted" | Use an **app password**, not your normal password. 2-Step Verification must be on. |
| Low fps | Close heavy programs. The pose model runs on CPU at about 10-20 fps on a typical laptop. |
