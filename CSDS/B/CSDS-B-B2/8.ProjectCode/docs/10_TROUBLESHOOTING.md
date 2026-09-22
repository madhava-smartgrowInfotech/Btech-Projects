# Troubleshooting

Start with the built-in check. It tests every setting and connection and says what to fix:

```
venv\Scripts\python scripts\check_env.py
```

The `run.bat` window shows what each part is doing (`[api]`, `[web]`, `[tunnel]`, `[sim]`). Detailed logs are in `logs\`.

---

## Setup

| Problem | Fix |
|---|---|
| **"Python 3.11 was not found"** | Install it: `winget install -e --id Python.Python.3.11`, or from python.org (tick **Add python.exe to PATH**). Open a **new** window and run `setup.bat` again. Other Python versions can stay installed; setup looks for 3.11 through `py -3.11`. |
| **"Node.js was not found"** | `winget install -e --id OpenJS.NodeJS.LTS`, then open a new window. |
| **Python packages fail to install** | Check the internet connection and run setup again; it continues where it stopped. On a company network, set the proxy first (`set HTTPS_PROXY=http://proxy:port`). If an antivirus locks files, pause it for the install, or add the folder as an exception. |
| **The PyTorch download is slow** | It is the largest package (about 200 MB, CPU version). Let it finish. Running setup again does not download it twice. |
| **`npm install` fails with EPERM or EBUSY** | A running SignalScout holds the files. Stop `run.bat` (Ctrl+C) and run `setup.bat` again. |
| **Dataset download fails** | The datasets are already in `data\raw\`, so this only happens if files were deleted. Check the connection. If Kaggle asks you to sign in, add `KAGGLE_USERNAME` and `KAGGLE_KEY` to `.env` ([how](04_DATASET.md#5-downloading-the-datasets-again)). |
| **cloudflared download fails** | Download `cloudflared-windows-amd64.exe` from https://github.com/cloudflare/cloudflared/releases/latest, rename it to `cloudflared.exe` and put it in `tools\`. Everything except the phone link works without it. |
| **Very long paths / "file name too long"** | Move the folder closer to the drive root, for example `D:\SignalScout\8.ProjectCode`. |

## Starting

### Port 8202 or 5202 is already in use

SignalScout uses these two ports only, and does not move to other ones.

1. Is SignalScout already running in another window? Close that window, or run `run.bat --stop`.
2. Otherwise find the program using the port:
   ```
   netstat -ano | findstr :8202
   tasklist /fi "PID eq <number from the last column>"
   ```
   Close that program. As a last resort, change `BACKEND_PORT` or `FRONTEND_PORT` in `.env`.

| Problem | Fix |
|---|---|
| **"web build failed"** in the window | The dashboard on port 5202 still works; only phones need the build. Run `cd frontend && npm run build` to see the error. `setup.bat` reinstalls the packages if they are damaged. |
| **"api stopped unexpectedly"** | Scroll up in the window for the error. Common causes: a damaged `.env` line (run `setup.bat` to repair it), or a missing model file (run `venv\Scripts\python ml\train_all.py`). |
| **The browser did not open** | Open http://localhost:5202 yourself. |
| **Dashboard shows "Something went wrong"** or keeps loading | Check that the `[api]` part is running, then reload. The dashboard keeps the last data it loaded, so it may show older numbers while the API restarts. |
| **Signed out unexpectedly** | Sign-ins last 12 hours (`JWT_EXPIRE_HOURS`). Changing `JWT_SECRET` also signs everyone out. |

## Phone and field probe

| Problem | Fix |
|---|---|
| **"Waiting for the secure link…"** on Connect a phone | The tunnel is still starting (up to about 20 s), or it cannot reach Cloudflare. Look at the `[tunnel]` lines in the `run.bat` window. Firewalls that block outgoing port 443 or 7844 block the tunnel; try another network. `TUNNEL_ENABLED` must be `true`. |
| **The link does not open on the phone** | The address is new on every start: scan the current QR code again. If the page says the site cannot be reached, wait 10-20 seconds, because new addresses take a moment to appear on the internet. |
| **"Allow location" was refused** | In Chrome: the lock icon next to the address → **Permissions → Location → Allow**. Check that location is on in the phone's quick settings. |
| **GPS accuracy is poor (±100 m or more)** | Go outdoors, set location mode to high accuracy, and wait a minute for the first fix. The chip on the Live tab turns green at ±50 m or better. |
| **Banner "You're on Wi-Fi"** | Turn Wi-Fi off. Readings over Wi-Fi are stored but kept out of mobile coverage and complaints. |
| **Operator shows "Unknown"** | The phone's address did not match a known mobile network, for example on some VPNs. Turn off any VPN or data-saver proxy, or choose the operator under the probe's **Settings → Mobile operator**. |
| **Readings stop when the screen turns off** | Browsers pause pages with the screen off. Keep the screen on; the probe asks Chrome to keep it awake ("Screen kept on" chip). Battery saver modes can block this; turn them off while measuring. |
| **Red bar "This phone's key was replaced"** | The key was replaced or the device removed on **Devices**. Tap **Register again**. Readings still waiting on the phone are kept and upload afterwards. |
| **Readings wait to sync but never upload** | Check that the phone is online and the tunnel is running, then tap **Sync now** on the Sync tab. After a `run.bat` restart the phone needs the **new** link: open it from the QR code once, and the queued readings upload. |
| **iPhone** | The probe works in Safari, but iOS shows no connection-type hints and cannot keep the screen awake as reliably. Android with Chrome is recommended. |
| **Speed tests use too much data** | Turn on **Data saver** in the probe's Settings, or set **Speed test every** higher. The estimated MB per hour is shown there. |

## Map, complaints and verification

| Problem | Fix |
|---|---|
| **The map is empty or shows the wrong place** | Check **Filters** (period, operator, time of day, sources) and use **Clear filters**. With data in several towns, pick one with the **area selector** under the title. **Show my area** jumps to your position. |
| **My readings are on the map but no complaint appears** | Standard thresholds need at least 8 readings in 30 minutes, 70% of them Weak or Dead, and the zone must stay bad for 15 minutes. Admins can switch to **Settings → Demo thresholds** (4 readings, about 2 minutes). Readings over Wi-Fi never count. Readings must fall in one zone (about 0.1 km²), so stay within about 100 m. |
| **A complaint was "dismissed" by itself** | A detected zone that recovers, or gets no further readings within 24 hours, is dismissed rather than registered. The timeline says which. |
| **A resolved complaint stays "Awaiting verification"** | Verification needs new readings from the zone after the resolve time: 5 by default, 3 with demo thresholds. Measure there again. After 7 days without readings it says so; an engineer can also **Confirm fix** by hand. |
| **Better signal says "Too few readings to model the area"** | The predictor needs readings of the same operator nearby. It then falls back to the nearest measured strong spot. Measure more of the surroundings. |

## Notifications

| Problem | Fix |
|---|---|
| **Link Telegram chat: "No messages found"** | Telegram bots cannot start a chat. Open your bot in Telegram, tap **Start** or send "hi", then click **Link Telegram chat** again. |
| **Telegram test fails with "Unauthorized"** | The token in `TELEGRAM_BOT_TOKEN` is wrong or was revoked. Get a new one from @BotFather (`/token`), update `.env` and restart. |
| **Email test fails with "535 Username and Password not accepted"** | `SMTP_PASSWORD` must be a Gmail **app password**, not your normal password, and 2-Step Verification must be on. Create one at https://myaccount.google.com/apppasswords. |
| **Test works but complaints send no email** | Set `DESK_EMAIL`, and check that **Send email** is on under Settings. Complaints from sample data never notify. |
| **A notification shows "failed"** | **Settings → Recent notifications** shows the error. Messages are retried automatically with increasing delays, so a short outage fixes itself. |

## ESP32 node

See the troubleshooting table in `firmware/esp32_node/README.md`. The most common issue is that Windows Firewall blocks port 8202 from the network:

**Windows Security → Firewall & network protection → Allow an app through firewall**, then allow Python on **Private** networks. Or run this in an administrator Command Prompt:

```
netsh advfirewall firewall add rule name="SignalScout API" dir=in action=allow protocol=TCP localport=8202 profile=private
```

## Data and models

| Problem | Fix |
|---|---|
| **"database is locked"** | Another program (for example a database viewer) has `data\app.db` open. Close it. |
| **Start over with a clean database** | Stop SignalScout, then delete `data\app.db`, `data\app.db-wal` and `data\app.db-shm`. |
| **"Not trained yet"** on Model performance or System status | Run `venv\Scripts\python ml\train_all.py` (about 6 minutes), then restart `run.bat`. |
| **Tests fail** | Run them from the project folder with the project's Python: `venv\Scripts\python -m pytest`. They use their own temporary database and do not need SignalScout to be running. |
