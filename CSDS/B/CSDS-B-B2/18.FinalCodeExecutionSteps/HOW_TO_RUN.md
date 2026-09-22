# How to run SignalScout

SignalScout runs on one Windows PC. Two double-clicks set it up and start it: **`setup.bat`** once, then **`run.bat`** every time. Phones connect through a secure link that `run.bat` opens for you.

---

## 1. What you need

| Item | Version | How to get it |
|---|---|---|
| Windows | 10 or 11, 64-bit | - |
| Python | **3.11** | `winget install -e --id Python.Python.3.11`, or https://www.python.org/downloads/ (tick **Add python.exe to PATH**) |
| Node.js | LTS (20.19 or newer) | `winget install -e --id OpenJS.NodeJS.LTS`, or https://nodejs.org/ |
| Internet | for the first setup and for phones | Setup downloads about 500 MB of packages |
| Disk space | about 3 GB free | Python packages (including PyTorch CPU), web packages, data |
| A phone (optional) | Android with Chrome | For measuring in the field; see [section 5](#5-measure-with-a-phone) |

Open a **new** Command Prompt after installing Python or Node.js, so Windows finds them. Check with:

```
py -3.11 --version
node --version
```

## 2. Install (once)

1. Put the `8.ProjectCode` folder anywhere, for example `D:\SignalScout\8.ProjectCode`. Avoid folders that sync to the cloud (OneDrive), because they slow the installation down.
2. Double-click **`setup.bat`**. It runs 8 steps and can safely be run again at any time:

| Step | What it does |
|---|---|
| 1 | Finds Python 3.11 |
| 2 | Finds Node.js |
| 3 | Creates `venv\` and installs the Python packages (`backend\requirements.txt`) |
| 4 | Creates `.env` from `.env.example` with a random security key (keeps your values when run again) |
| 5 | Verifies the datasets in `data\raw\` and downloads any that are missing |
| 6 | Downloads `cloudflared.exe` into `tools\`, for the phone's HTTPS link |
| 7 | Installs the web packages and builds the web app |
| 8 | Trains the models, only if `models\` is empty (about 6 minutes); the trained models are included, so this is normally skipped |

3. When it prints **Setup complete**, press a key to close the window.

Optional, and possible at any time: add Telegram and email details to `.env` so the complaint desk gets notified. See [08_CONFIGURATION.md](08_CONFIGURATION.md#telegram-notifications). To check every key and connection:

```
venv\Scripts\python scripts\check_env.py
```

## 3. Start

Double-click **`run.bat`**. One window starts everything and shows its output with a tag per part (`[api]`, `[web]`, `[tunnel]`, `[sim]`):

| Part | Address |
|---|---|
| Dashboard | http://localhost:5202 (opens in your browser) |
| API and interactive docs | http://localhost:8202/docs |
| Phone link (HTTPS) | `https://<random-words>.trycloudflare.com`, shown in the window and as a QR code under **Connect a phone** |
| ESP32 simulator | three simulated sensor nodes reporting every 15 s |

When everything is up, the window prints:

```
================================================================
  SignalScout is running
================================================================
  Dashboard      http://localhost:5202
  API + docs     http://localhost:8202/docs
  Phone (HTTPS)  https://....trycloudflare.com   (QR code: Dashboard > Connect a phone)
  Demo sign-in   user@signalscout.demo / engineer@signalscout.demo / admin@signalscout.demo
  Password       Scout@2026
  Stop           press Ctrl+C in this window
================================================================
```

The first start takes about half a minute longer: sample data is loaded in the background, and the web app is rebuilt for phones if needed.

`run.bat` options:

| Option | Effect |
|---|---|
| `run.bat --no-tunnel` | No HTTPS link; only this PC and your LAN can connect |
| `run.bat --no-simulator` | No simulated ESP32 nodes |
| `run.bat --no-build` | Do not rebuild the phone web app even if sources changed |
| `run.bat --no-browser` | Do not open the dashboard automatically |

SignalScout uses only ports **8202** and **5202**, so it runs alongside other software on the same PC. If a port is taken, it stops with a clear message instead of picking another port. See [10_TROUBLESHOOTING.md](10_TROUBLESHOOTING.md#port-8202-or-5202-is-already-in-use).

## 4. First sign-in

Open http://localhost:5202 → **Sign in**, and use one of the demo accounts. The password is `Scout@2026` for all three.

| Account | What you can do |
|---|---|
| `user@signalscout.demo` | Measure with a phone, see the map, report problems, follow your complaints |
| `engineer@signalscout.demo` | Everything above plus the **Operator desk** |
| `admin@signalscout.demo` | Everything plus **Settings** and **Users** |

The map, analytics and desk already show **Sample** data, replayed from a public drive-test dataset. An admin can remove it under **Settings → Sample data**. To try the complaint flow in a few minutes, sign in as admin and click **Settings → Demo thresholds**.

## 5. Measure with a phone

1. On the PC: **Connect a phone** shows a QR code.
2. On an Android phone:
   - turn on **Location**;
   - turn **Wi-Fi off**, so the mobile network is measured;
   - scan the QR code with the camera and open the link in **Chrome**.
3. Sign in, for example as `user@signalscout.demo`. Allow location and tap **Register and continue**.
4. Tap **Start measuring** and keep the screen on while you walk.

Readings appear on the PC's **Coverage map** within seconds. Without signal the phone keeps measuring and stores readings. They upload by themselves when the connection returns.

Phone browsers allow GPS only on HTTPS pages, which is why the link goes through the tunnel. The link **changes every time `run.bat` starts**, so scan the new QR code after a restart. A phone that is already registered stays registered.

## 6. ESP32 sensor node (optional)

Without hardware, the built-in simulator provides three nodes. For a real ESP32:

1. **Devices → Add ESP32 node**. Enter a name, the Wi-Fi network, and a position if it has no GPS. Copy the key.
2. Follow `firmware/esp32_node/README.md`: Arduino IDE, the ESP32 board package, three libraries, `config.h`, upload.
3. Set `API_BASE` to the **API for ESP32 nodes** address shown under **Connect a phone**, for example `http://192.168.0.108:8202`. The node must be on the same network as the PC, and Windows Firewall must allow port 8202 on private networks.

To turn the simulator off, set `ESP32_SIMULATOR=false` in `.env`, or start with `run.bat --no-simulator`.

## 7. Stop

- Press **Ctrl+C** in the `run.bat` window. It stops the API, the dashboard, the tunnel and the simulator. It stops only what it started.
- From another Command Prompt in the folder, `run.bat --stop` does the same.
- Closing the window also stops everything.

Nothing is lost on stopping. Data stays in `data\app.db`.

## 8. Reset, update, retrain

| Task | How |
|---|---|
| Start again with empty data | Stop SignalScout, then delete `data\app.db`, `data\app.db-wal` and `data\app.db-shm`. The next start creates a fresh database with the demo accounts and sample data. |
| Keep data but remove the sample | **Settings → Sample data → Remove sample data** |
| New security key (signs everyone out) | Delete the `JWT_SECRET=` line from `.env` and run `setup.bat` |
| Update after getting new code | Run `setup.bat` again. It installs new packages and rebuilds; your `.env` and data are kept. |
| Retrain the models | `venv\Scripts\python ml\train_all.py` (about 6 minutes), then restart `run.bat`. See [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md). |
| Run the tests | `venv\Scripts\python -m pytest`. See [09_TESTING.md](09_TESTING.md). |
| Share your own readings | `venv\Scripts\python scripts\export_field_sample.py` writes an anonymised sample to `data\field\` |

## 9. Running pieces by hand

`run.bat` is the normal way to start. For development, the parts can also be started separately from the folder:

```
venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8202
cd frontend && npm run dev
tools\cloudflared.exe tunnel --url http://localhost:8202
venv\Scripts\python scripts\esp32_simulator.py --api http://127.0.0.1:8202
```

When started by hand, the tunnel address is not shown under **Connect a phone**. Use the address that `cloudflared` prints, and add `/probe`.
