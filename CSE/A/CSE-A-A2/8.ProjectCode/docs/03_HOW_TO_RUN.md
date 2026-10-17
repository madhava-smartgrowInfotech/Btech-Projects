# How to run ResQAI

ResQAI has two parts: the Flask API (`app.py`, port **8302**) and the React web app (`frontend/`, port **5302**).
The original Flask page is still served at `http://localhost:8302/`.

## Requirements
- Windows with Python 3.10+ and Node.js 18+

## First time
```
setup.bat
```
Creates `venv`, installs `requirements.txt`, runs `npm install` in `frontend/`, and copies `.env.example` to `.env`.

## Every time
```
run.bat
```
Starts the API (8302) and the web app (5302) in two windows and opens http://localhost:5302.
`stop.bat` stops both. Ports can be changed with `BACKEND_PORT` / `FRONTEND_PORT` in `.env`.

## By hand
```
set PORT=8302 && python app.py          :: API
cd frontend && npm run dev              :: web app (proxies /api to the API)
```
Production build: `cd frontend && npm run build` (output in `frontend/dist`).

## Check it works
```
python scripts/smoke_test.py            :: accounts, login, detection and dispatch flow, needs the app running
python scripts/capture_screens.py       :: walks every screen, saves docs/screenshots/*.png, fails on console errors
```
The screenshot script needs `pip install playwright` and `playwright install chromium` once.

## Signing in
Open http://localhost:5302, press **Sign in** and **Create an account** on first use (password 8+ characters).
Accounts are saved in `data/users.json`. `REQUIRE_AUTH=1` in `.env` also makes the API reject calls without a login token.

## Screens
`/` landing - `/login` and `/register` - then, signed in only: `/monitor` live monitor - `/manual` manual override - `/response` emergency response map.
The 15 second confirmation and dispatched-alert dialogs appear on any app screen.
