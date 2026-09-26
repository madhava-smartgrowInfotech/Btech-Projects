# How to run SeatWise

This guide takes you from a Windows PC with nothing installed to SeatWise running in your browser. The first setup takes about 5 minutes; afterwards, starting takes a few seconds.

## 1. What you need

| Item | Version | How to get it |
|---|---|---|
| Windows | 10 or 11 (64-bit) | - |
| Python | **3.11** | https://www.python.org/downloads/release/python-3119/ - choose *Windows installer (64-bit)*. On the first installer screen, tick **Add python.exe to PATH**, then click **Install Now**. |
| Node.js | LTS (20 or newer) | https://nodejs.org - download the **LTS** installer and click through with the default options. |
| Git | any | https://git-scm.com/download/win (only needed to download or update the code). |
| Disk space | about 1.5 GB | - |
| Internet | only for the first setup | Setup downloads the Python and web packages once. SeatWise itself runs offline. |

Other Python versions may be installed alongside 3.11. SeatWise uses 3.11 through the `py -3.11` launcher.

To check what you have, open **Command Prompt** (press Windows, type `cmd`, press Enter) and run:

```bat
py -3.11 --version
node --version
```

## 2. Get the code

If you received SeatWise as a folder, skip this step. Otherwise clone the repository and open the product folder (the folder that contains `setup.bat` and `run.bat`).

## 3. One-time setup

Double-click **`setup.bat`** (or run it from Command Prompt in the SeatWise folder). It:

1. checks for Python 3.11 and Node.js, and tells you what to install if something is missing;
2. creates a private Python environment in `venv\` and installs the backend packages;
3. creates `.env` from `.env.example` and generates a random login secret;
4. installs the web app packages in `frontend\node_modules\`;
5. creates the database `data\app.db` with the demo accounts;
6. runs `scripts\check_env.py` and prints a checklist - every line should say `OK`.

It is safe to run `setup.bat` again at any time (for example after an update).

## 4. Start SeatWise

Double-click **`run.bat`**. It:

- starts the **SeatWise API** window (port **8113**) and the **SeatWise web** window (port **5113**);
- waits until both answer, then opens **http://localhost:5113** in your browser.

Keep the two windows open while you use SeatWise. The API documentation is at http://localhost:8113/docs.

SeatWise always uses ports 8113 and 5113, so it can run next to other products on the same PC. If one of those ports is already taken, `run.bat` tells you instead of starting.

## 5. First sign-in

| Account | Email | Password |
|---|---|---|
| Exam controller (administrator) | `admin@seatwise.local` | `SeatWise@2026` |
| Invigilator | `invigilator@seatwise.local` | `SeatWise@2026` |
| More invigilators | `inv01@seatwise.local` ... `inv09@seatwise.local` | `SeatWise@2026` |

The sign-in page also has one-click **Demo workspace** buttons for both roles. Change the demo password (`DEMO_PASSWORD` in `.env`, or **Team > Reset password**) before sharing the PC.

## 6. A five-minute tour (the demo scenario)

1. Sign in as the exam controller and open **Import data**. Under **Templates & samples**, download the **Sample workbook**, then drop it on the upload area. *Validation passes*, so click **Import 1,020 rows**.
2. Open **Sittings & plans**, choose a sitting and click **Generate plan**. It is solved in a few seconds with **0 same-paper neighbours**. Click **Publish**. Repeat for two more sittings.
3. Click **Seat maps**. Drag a candidate onto a red seat: the move is blocked and the reason is shown. Drop on a green seat to swap. Then open **Exports** and download the seating charts (PDF) and hall lists (Excel).
4. Sign out and open **Find my seat** on the home page. Enter a candidate ID (for example one from the seat map) and download the QR slip. Sign in as the invigilator, open **Attendance**, type or scan that ID, and mark attendance.

The same scenario can be checked automatically:

```bat
venv\Scripts\python scripts\demo_scenario.py
```

## 7. Stop SeatWise

Double-click **`stop.bat`**, or close the two SeatWise windows. `stop.bat` only stops the programs on SeatWise's own ports.

## 8. Reset

| Goal | How |
|---|---|
| Clear all exam data but keep accounts and settings | **Settings > Reset workspace** (type RESET) |
| Start completely fresh (new database with demo accounts) | Stop SeatWise, then run `venv\Scripts\python scripts\init_db.py --reset` |
| Re-create the sample files | `venv\Scripts\python scripts\generate_sample_data.py` (seed 2026 recreates the committed files exactly) |

## 9. Use it from tablets and phones

Invigilators can take attendance on a tablet, and candidates can look up seats on their phones, over the same Wi-Fi as the SeatWise PC.

1. Find the PC's address: open Command Prompt and run `ipconfig`, then note the **IPv4 Address** (for example `192.168.1.20`).
2. On the tablet or phone, open `http://192.168.1.20:5113`.
3. The first time, Windows may ask whether Node.js may use the network. Allow it on **Private networks**.
4. To make the QR codes on seat slips open this address, set `PUBLIC_BASE_URL=http://192.168.1.20:5113` in `.env` and restart SeatWise before printing slips.

Camera scanning on the attendance screen is offered only where the browser allows the camera, which means on `localhost` or HTTPS. Over a plain network address, use a hand-held QR/barcode scanner, which types into the scan box, or type the candidate ID.

## 10. Useful commands

```bat
:: check the machine and .env
venv\Scripts\python scripts\check_env.py --network

:: backend tests
cd backend && ..\venv\Scripts\python -m pytest

:: frontend type check and production build
cd frontend && npm run build

:: engine benchmark (about 7 minutes) or a quick smoke run
venv\Scripts\python -m ml.benchmark
venv\Scripts\python -m ml.benchmark --quick
```

Problems? See [10_TROUBLESHOOTING.md](10_TROUBLESHOOTING.md).
