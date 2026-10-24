# HOW_TO_RUN — SentinelFlow

> **Update:** `run.bat` now starts the Flask API on port **8415** and the new React console on port **5415**
> (see `docs/03_HOW_TO_RUN.md`). Wherever this guide says `http://localhost:5000`, use `http://127.0.0.1:5415` for the console
> or `http://127.0.0.1:8415` for the original dashboard. Docker still serves the original dashboard on 5000.

## 1. Prerequisites

- **Operating system:** Windows 10/11 or a modern Linux distribution.
- **Python:** 3.11 or 3.12 recommended. Check with `python --version`.
  Download from https://www.python.org/downloads/ (on Windows, tick
  “Add python.exe to PATH” during installation).
- **Docker (optional, Method B only):** Docker Desktop from
  https://www.docker.com/products/docker-desktop/
- **Packet capture (live mode only):** Scapy needs elevated privileges —
  run as Administrator (Windows) or root (Linux). On Windows you may also need
  Npcap from https://npcap.com/ if capture fails to start.
- **Browser:** any modern browser (Chrome/Edge/Firefox).

No CICIDS2017 download, GPU, or special hardware is required: if the dataset is
unreachable, training uses a labelled synthetic fallback automatically, and
Simulation Mode demonstrates the full pipeline without capture permissions.

## 2. Method A — Automatic (Recommended)

For a complete non-coder:

1. Find the `SentinelFlow` folder on your computer.
2. Double-click **`run.bat`**. A black command window opens — this is normal.
   It runs the startup steps and stays open while SentinelFlow runs.
3. What you will see:
   - `[1/6] Python found` plus the version — installation continuing normally.
   - `[2/6]` virtual-environment setup (first run takes longer).
   - `[3/6]` dependency installation with pip progress lines.
   - `[4/6]` model check; first run trains the model and prints real metrics
     (accuracy, precision, recall, F1, ROC-AUC).
   - `[5/6] Starting SentinelFlow on http://localhost:5000`.
4. Your browser should open at `http://localhost:5000` automatically.
   If it does not, open that address manually.
5. Successful startup looks like: the command window shows
   `* Running on http://127.0.0.1:5000` and the browser shows the SentinelFlow
   dashboard with summary cards and empty-or-growing tables.
6. Using it:
   - Choose an interface from the dropdown and press **Start Live**, or
   - Press **Start Simulation** (works everywhere, no permissions needed).
   - Click any detection row to inspect the threat detail.
   - Watch the Mitigation Center; quarantines recover automatically (~40 s).
7. To stop: press Ctrl+C in the black window, or just close the window.

## 3. Method B — Docker

Use this if Docker Desktop is already installed:

```text
docker build -t sentinelflow .
docker run --rm -p 5000:5000 sentinelflow
```

Then open `http://localhost:5000`.

Or simply double-click **`run-docker.bat`**, which builds the image, runs the
container (mapped to localhost port 5000), and opens the dashboard.

Note: Docker reliably supports the dashboard, model inference, database, and
Simulation Mode. Live host packet capture inside a container is
platform-dependent and is not promised — use Simulation Mode in Docker.

## 4. Method C — Manual

Windows CMD:

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python ml\train_model.py
python app.py
```

Windows PowerShell:

```text
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ml\train_model.py
python app.py
```

Linux / macOS:

```text
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ml/train_model.py
python app.py
```

Then open `http://localhost:5000`.

## 5. Troubleshooting

- **“Python was not found” / `python` not recognized:** install Python 3.11/3.12
  from https://www.python.org/downloads/ and tick “Add python.exe to PATH”.
  Close and reopen the terminal, then retry.
- **Python version problem:** run `python --version`. SentinelFlow targets
  3.11/3.12; newer versions usually work but are untested with some drivers.
- **Windows Defender / SmartScreen blocks `run.bat`:** click “More info” →
  “Run anyway”. The script only creates a venv, installs packages, and starts
  a localhost server.
- **Virtual-environment creation fails:** the window shows the exact command and
  error. Common fixes: reinstall Python with PATH enabled, free disk space, or
  run `python -m venv .venv` manually to see details.
- **pip installation fails:** the actual pip error stays visible in the window.
  Check your internet connection, then re-run `run.bat` (it reuses `.venv`).
  Corporate proxies may need `pip --proxy` configuration.
- **Scapy / Npcap issue:** install Npcap from https://npcap.com/ (WinPcap
  compatibility mode if offered), then restart and run as Administrator.
- **Capture permission denied:** run the terminal as Administrator (Windows) or
  with sudo (Linux). Alternatively press **Start Simulation** — full demo,
  no permissions needed.
- **Invalid interface:** open the interface dropdown and pick another entry;
  virtual/VPN adapters sometimes cannot capture.
- **Port already in use:** another program occupies port 5000. Stop it (or the
  other SentinelFlow window) and retry.
- **Browser does not open automatically:** manually open `http://localhost:5000`.
- **Model not found:** run `python ml\train_model.py` from the SentinelFlow
  folder (or re-run `run.bat`, which trains automatically when missing).
- **Dataset download failure:** training falls back to labelled synthetic data
  automatically and records the provenance; no action needed for a demo.
- **Docker not installed:** install Docker Desktop from
  https://www.docker.com/products/docker-desktop/ and ensure it is running.
- **Docker port issue:** `docker ps` may show another container on 5000; stop it
  with `docker stop <name>` and retry.
- **Live capture unavailable:** use **Start Simulation** — same inference,
  severity, mitigation, and database, clearly labelled as Simulation Mode.
