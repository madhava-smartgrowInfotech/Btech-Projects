# Configuration

SignalScout reads its configuration from `.env` in the project folder.

- `setup.bat` creates `.env` from `.env.example` on the first run and generates a random `JWT_SECRET`.
- Running setup again adds any new keys and keeps your values.
- `.env` is git-ignored. Secrets never leave your PC.

After changing `.env`, restart SignalScout (close the `run.bat` window and run it again).

Check every key and connection at any time:

```
venv\Scripts\python scripts\check_env.py               # checks the values and whether each service is reachable
venv\Scripts\python scripts\check_env.py --send-test   # also sends a real Telegram message and a test email
```

Some values can also be changed while SignalScout runs, under **Administration → Settings**. See [Settings in the app](#settings-in-the-app) at the end of this page.

---

## Server

| Key | Default | What it does |
|---|---|---|
| `BACKEND_PORT` | `8202` | Port of the API. It also serves the built web app to phones through the tunnel. Fixed for this product; do not change it unless something else uses it. |
| `FRONTEND_PORT` | `5202` | Port of the dashboard in development mode. If the port is taken, startup fails rather than moving to another port. |
| `BACKEND_HOST` | `0.0.0.0` | Address the API listens on. `0.0.0.0` lets ESP32 nodes and phones on the same Wi-Fi reach it. Use `127.0.0.1` to allow this PC only. |
| `PUBLIC_API_URL` | `http://localhost:8202` | Address that ESP32 nodes on your network should use, for example `http://192.168.1.20:8202`. The **Connect a phone** page shows your PC's LAN address. |
| `DASHBOARD_URL` | `http://localhost:5202` | Used for the "open complaint" links in email and Telegram notifications. |
| `CORS_ORIGINS` | empty | Extra browser origins allowed to call the API, comma separated. Ports 5202 and 8202 on `localhost` are always allowed. The phone probe needs no entry, because the API serves it through the tunnel from the same address. |

## Phone probe access

| Key | Default | What it does |
|---|---|---|
| `TUNNEL_ENABLED` | `true` | Starts a free Cloudflare quick tunnel (`tools/cloudflared.exe`) to the API, so phones get an HTTPS address. Phone browsers only allow GPS on HTTPS pages. The address changes every time `run.bat` starts, and the **Connect a phone** page always shows the current one as a QR code. Set it to `false` if you only use this PC. |
| `PROBE_INTERVAL_S` | `10` | Default seconds between readings. Each phone can change this in the probe's Settings tab. |
| `PROBE_SPEEDTEST_INTERVAL_S` | `60` | Default seconds between speed tests. `0` turns them off. Data saver mode on the phone also turns them off. |
| `PROBE_SPEEDTEST_MAX_BYTES` | `1000000` | Largest download used by a speed test. The test starts small and grows until it lasts long enough. |
| `PROBE_WEAK_RTT_MS` | `400` | A round trip above this makes a probe reading Weak. |
| `PROBE_WEAK_DL_MBPS` | `2` | A download below this makes a probe reading Weak. |

## Security

| Key | Default | What it does |
|---|---|---|
| `JWT_SECRET` | generated | **Required.** Signs sign-in tokens. `setup.bat` writes a random 64-character value. If you change it, everyone has to sign in again. |
| `JWT_EXPIRE_HOURS` | `12` | How long a sign-in lasts. |

Device keys for phones and ESP32 nodes are stored only as SHA-256 hashes. A key is shown once when it is created. It can be replaced on the **Devices** page.

## Database

| Key | Default | What it does |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/app.db` | The SQLite file, created on first start. To start from scratch, stop SignalScout and delete `data/app.db`, `data/app.db-wal` and `data/app.db-shm`. |

## First-run data

| Key | Default | What it does |
|---|---|---|
| `SEED_DEMO_USERS` | `true` | Creates three demo accounts (password `Scout@2026`): `user@signalscout.demo`, `engineer@signalscout.demo` and `admin@signalscout.demo`. Set it to `false` for a real deployment, and create your own admin with **Register** before you turn it off. |
| `SEED_SAMPLE_DATA` | `true` | Replays public-dataset traces so the map, analytics and desk have data at once. The data is tagged **Sample**, and an admin can remove it in Settings. |

## Zone detection and complaints

These keys set the **standard** values. Admins can change them live in Settings, or switch to the demo thresholds.

| Key | Default | What it does |
|---|---|---|
| `H3_RESOLUTION` | `9` | Zone size. 9 means hexagons of about 0.1 km². 8 is about 0.7 km², 10 about 0.015 km². Changing it only affects new readings. |
| `DETECT_MIN_READINGS` | `8` | Readings needed in the window before a zone is judged. |
| `DETECT_WINDOW_MIN` | `30` | Length of the sliding window, in minutes. |
| `DETECT_BAD_SHARE` | `0.7` | Share of Weak or Dead readings that makes a zone bad. |
| `DETECT_PERSIST_MIN` | `15` | How long a zone must stay bad before its complaint is registered. |
| `VERIFY_MIN_READINGS` | `5` | New readings needed after a fix before it is judged. |
| `VERIFY_STRONG_SHARE` | `0.7` | Share of Strong readings that confirms the fix (status becomes Verified). |
| `VERIFY_REOPEN_SHARE` | `0.5` | Share of Weak or Dead readings that reopens the complaint. |
| `VERIFY_TIMEOUT_DAYS` | `7` | How long to wait for verification readings. After that the complaint shows "no new readings". |

## ESP32 simulator

Used when you have no ESP32 hardware. It sends the same data a real node would.

| Key | Default | What it does |
|---|---|---|
| `ESP32_SIMULATOR` | `true` | `run.bat` starts `scripts/esp32_simulator.py` with the API. |
| `ESP32_SIMULATOR_NODES` | `3` | Number of simulated nodes: a strong one, a weak one and a flaky one. |
| `ESP32_SIMULATOR_INTERVAL_S` | `15` | Seconds between reports. |
| `ESP32_SIMULATOR_LAT`, `ESP32_SIMULATOR_LON` | empty | Where the nodes stand. Empty means automatic: near your recent phone readings, otherwise near the sample data. |

For a real node, see `firmware/esp32_node/README.md`.

## Telegram notifications

The desk is told about new and reopened complaints.

| Key | What it does |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token of your bot. |
| `TELEGRAM_CHAT_ID` | Chat that receives messages. Leave it empty and link the chat in the app instead (see step 5). |

**Get a token:**

1. Open Telegram and search for **@BotFather** (the one with the blue tick).
2. Send `/newbot`, choose a display name, then a username ending in `bot`.
3. BotFather replies with a token such as `123456789:AA...`. Paste it after `TELEGRAM_BOT_TOKEN=`.
4. Restart SignalScout.
5. In Telegram, open your bot and send it any message (for example "hi"). Bots cannot start a chat by themselves.
6. In SignalScout, go to **Administration → Settings → Link Telegram chat**. The app picks up the chat that just messaged the bot.
7. Click **Send test**.

To send to a group instead, add the bot to the group, send a message in the group, then click **Link Telegram chat**.

## Email notifications (Gmail SMTP)

| Key | Default | What it does |
|---|---|---|
| `SMTP_HOST` | `smtp.gmail.com` | Mail server. |
| `SMTP_PORT` | `587` | STARTTLS port. |
| `SMTP_USER` | empty | The Gmail address that sends. |
| `SMTP_PASSWORD` | empty | A 16-character **app password**, not your normal password. |
| `SMTP_FROM` | empty | Sender shown to recipients. Defaults to `SMTP_USER`. |
| `DESK_EMAIL` | empty | Inbox of the complaint desk. Complaint emails are sent only when this is set. It can be the same address as `SMTP_USER`. |

**Create an app password:**

1. Go to https://myaccount.google.com/security.
2. Turn on **2-Step Verification** if it is off. App passwords need it.
3. Go to https://myaccount.google.com/apppasswords.
4. Enter a name such as "SignalScout" and click **Create**.
5. Copy the 16 letters. Spaces do not matter.
6. Paste them after `SMTP_PASSWORD=` and restart.
7. Check it with **Settings → Send test**.

Notifications that fail (for example while offline) are queued and retried with increasing delays. **Settings → Recent notifications** shows each one's state. Complaints from sample data never send notifications.

## Optional services

| Key | What it does | How to get it |
|---|---|---|
| `OPENCELLID_API_KEY` | Shows known cell towers within 1 km on each complaint (map markers and a list, marking the cell that served the readings when it is known). Results are cached for a week per area. | Sign up at https://opencellid.org. After signing in, copy the **Access Token** from your profile page. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Rewrites each complaint summary in plain language for the notification. Without a key, a clear template text is used. | Sign in at https://aistudio.google.com/apikey and click **Create API key**. `GEMINI_MODEL` defaults to `gemini-3.8-flash`. |
| `KAGGLE_USERNAME`, `KAGGLE_KEY` | Needed only if the dataset download is ever blocked. | See [04_DATASET.md](04_DATASET.md#5-downloading-the-datasets-again). |

Leave optional keys empty to switch the feature off. Nothing else changes.

---

## Settings in the app

**Administration → Settings** stores these values in the database. They take effect immediately, without a restart.

| Setting | Range | Meaning |
|---|---|---|
| `detect_min_readings` | 2-200 | Readings needed in the window |
| `detect_window_min` | 1-1440 | Window length (minutes) |
| `detect_bad_share` | 0.3-1.0 | Share of Weak/Dead that makes a zone bad |
| `detect_persist_min` | 0-1440 | Minutes a zone must stay bad before registration |
| `verify_min_readings` | 2-200 | New readings needed to verify a fix |
| `verify_strong_share` | 0.3-1.0 | Share of Strong readings that confirms a fix |
| `verify_reopen_share` | 0.2-1.0 | Share of Weak/Dead readings that reopens |
| `verify_timeout_days` | 1-90 | Days to wait for verification readings |
| `probe_weak_rtt_ms` | 50-5000 | Phone probe: round trip above this is Weak |
| `probe_weak_dl_mbps` | 0.1-100 | Phone probe: download below this is Weak |
| `notify_telegram`, `notify_email` | on / off | Send complaint updates on each channel |
| `telegram_chat_id` | - | The linked desk chat |

Two buttons set several values at once:

| Values | Standard thresholds | Demo thresholds |
|---|---|---|
| Readings needed | 8 | 4 |
| Window | 30 min | 10 min |
| Minutes a zone must stay bad | 15 | 2 |
| Readings to verify a fix | 5 | 3 |
| Strong share to verify | 0.7 | 0.7 |
| Weak/Dead share to reopen | 0.5 | 0.5 |

**Demo thresholds** register a complaint after about two minutes in a dead zone, which suits a live demonstration.
