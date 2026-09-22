# 10 · Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `setup.bat`: *Python 3.11 was not found* | Python missing or a different version on PATH | Install Python 3.11 (64-bit) from python.org and tick **Add python.exe to PATH**. If several versions are installed, the `py -3.11` launcher is used automatically |
| `setup.bat`: *Node.js was not found* | Node not installed | Install the LTS version from https://nodejs.org, open a new Command Prompt, run `setup.bat` again |
| `pip install` fails behind a proxy / no internet | Packages cannot be downloaded | Connect to the internet (or set `HTTPS_PROXY`) and run `setup.bat` again — it is safe to repeat |
| *Port 8204 is already in use* in the API window | UPI Guardian already running, or another program uses 8204 | Run `stop.bat`, then `run.bat`. If another program needs 8204, change `API_PORT` in `.env` |
| Web window: *Port 5204 is already in use* | Same for the web app | `stop.bat`, or change `FRONTEND_PORT` in `.env` |
| Browser shows *Cannot reach UPI Guardian* | The API window is closed or crashed | Look at the **UPI Guardian API (8204)** window for the error; restart with `run.bat` |
| `/api/health` shows a model with `"loaded": false` | Model file missing | Run `venv\Scripts\python ml\train_all.py` (needs `setup.bat train` first), then restart |
| *JWT_SECRET is not set* on start | `.env` missing or the placeholder secret was kept | Run `setup.bat` (creates `.env`) or put a random value in `JWT_SECRET` |
| Signed out unexpectedly | Token expired (12 h) or `JWT_SECRET` changed | Sign in again |
| **Listen** does nothing / *Voice is not available right now* | gTTS needs internet for new phrases | Connect to the internet. Screen guides are pre-recorded and work offline; the app falls back to the browser's own voice (Telugu may be missing in some browsers) |
| Camera does not start on the phone | Cameras need a secure (https) page | Use the link from `run_phone.bat`, allow camera access in Chrome, or use the **Upload** / **Samples** tabs |
| `run_phone.bat`: *cloudflared was not found* | Not installed | `winget install --id Cloudflare.cloudflared`, then run `run_phone.bat` again |
| `run_phone.bat`: *The tunnel did not start* | No internet or a firewall blocks Cloudflare | Check the connection; see `logs\cloudflared.log` |
| Phone link stopped working | Quick-tunnel links change on every start | Open the new link printed by `run_phone.bat`; reinstall the PWA if needed |
| Installed app shows an old version | The service worker cached the previous build | Close and reopen the app (it updates automatically), or clear the site data in Chrome |
| Night-time scenario shows Low risk | The risk engine uses the real time | Set **Settings → Sandbox clock** to `01:30`; remember to switch back with **Use real time** |
| A payment says *Please answer the safety check before paying* | Medium / High payments need the intent answer | Tap **Continue to safety check** first |
| *Incorrect UPI PIN* | Sample accounts use `1234` | Use `1234` or the PIN you chose at registration (change it in Settings) |
| *Not enough balance in your sandbox wallet* | Wallet emptied during testing | Reset the sandbox (admin → Sandbox tools → Reset) or delete `data\app.db` and restart |
| Sample data looks different after many tests | You changed it | Reset the sandbox |
| `database is locked` | Two copies of the API use the same `data\app.db` | Run `stop.bat`; start only one copy |
| Tests fail with `ModuleNotFoundError` | Run from the wrong folder or without the venv | `cd backend` and run `..\venv\Scripts\python -m pytest` |
| `npm run build` fails with type errors | Code changes broke types or a translation key is missing in `hi.ts` / `te.ts` | Read the first error; every English key must exist in both other languages |

Logs: the API writes JSON lines to its window (`LOG_LEVEL` in `.env`); the phone tunnel writes
`logs\cloudflared.log`.
