"""Start SignalScout: API (8202), web dev server (5202), phone HTTPS link and ESP32 simulator - in one window.

    run.bat                      # everything
    run.bat --no-tunnel          # skip the Cloudflare HTTPS link
    run.bat --no-simulator       # skip the ESP32 simulator
    run.bat --no-build           # do not rebuild the web app for the phone even if sources changed
    run.bat --no-browser         # do not open the dashboard automatically
    run.bat --stop               # from another window: stop a running SignalScout cleanly

Press Ctrl+C to stop. Only the processes started here are stopped.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "venv" / "Scripts" / "python.exe"
RUNTIME = ROOT / "data" / "runtime"
TUNNEL_FILE = RUNTIME / "tunnel.json"
STOP_FILE = RUNTIME / "stop.request"
IS_WIN = sys.platform == "win32"
COLORS = {"api": "\033[36m", "web": "\033[35m", "tunnel": "\033[33m", "sim": "\033[32m", "run": "\033[1m"}
RESET = "\033[0m"
children: dict[str, subprocess.Popen] = {}
stopping = threading.Event()


for _stream in (sys.stdout, sys.stderr):   # child tools print symbols the legacy console code page lacks
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure:
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except ValueError:
            pass


def say(tag: str, msg: str) -> None:
    text = f"{COLORS.get(tag, '')}[{tag:>6}]{RESET} {msg}"
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"), flush=True)


def load_env() -> dict[str, str]:
    env = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def pump(tag: str, stream, on_line=None) -> None:
    for raw in iter(stream.readline, ""):
        line = raw.rstrip()
        if not line:
            continue
        if on_line:
            on_line(line)
        if tag == "tunnel" and not re.search(r"trycloudflare\.com|ERR|error|Registered tunnel", line):
            continue   # cloudflared is chatty; keep the useful lines
        say(tag, line)


def start(tag: str, cmd: list[str] | str, cwd: Path, on_line=None, shell: bool = False) -> subprocess.Popen:
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if IS_WIN else 0
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "FORCE_COLOR": "0", "NO_COLOR": "1"}
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace", bufsize=1, shell=shell, creationflags=flags, env=env)
    children[tag] = proc
    threading.Thread(target=pump, args=(tag, proc.stdout, on_line), daemon=True).start()
    return proc


def stop_all() -> None:
    stopping.set()
    for tag, proc in list(children.items()):
        if proc.poll() is None:
            if IS_WIN:   # the whole tree of *our* child only (npm -> node, etc.)
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            else:
                proc.terminate()
            say("run", f"stopped {tag}")
    TUNNEL_FILE.unlink(missing_ok=True)


def wait_http(url: str, timeout: float) -> bool:
    end = time.time() + timeout
    while time.time() < end and not stopping.is_set():
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(0.7)
    return False


def dist_is_stale() -> bool:
    index = ROOT / "frontend" / "dist" / "index.html"
    if not index.exists():
        return True
    built = index.stat().st_mtime
    sources = [ROOT / "frontend" / "index.html", ROOT / "frontend" / "vite.config.ts", ROOT / "frontend" / "tailwind.config.ts"]
    sources += [p for p in (ROOT / "frontend" / "src").rglob("*") if p.is_file()]
    sources += [p for p in (ROOT / "frontend" / "public").rglob("*") if p.is_file()]
    return any(p.stat().st_mtime > built for p in sources if p.exists())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-tunnel", action="store_true")
    ap.add_argument("--no-simulator", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--stop", action="store_true", help="ask a running launcher to shut down cleanly")
    args = ap.parse_args()
    if args.stop:
        RUNTIME.mkdir(parents=True, exist_ok=True)
        STOP_FILE.write_text("stop", encoding="utf-8")
        print("Stop requested - the SignalScout window will shut down within a few seconds.")
        return 0
    if IS_WIN:
        os.system("")   # enable ANSI colours in the Windows console

    env = load_env()
    api_port, web_port = int(env.get("BACKEND_PORT", 8202)), int(env.get("FRONTEND_PORT", 5202))
    host = env.get("BACKEND_HOST", "0.0.0.0")
    for port, name in ((api_port, "API"), (web_port, "web dev server")):
        if port_busy(port):
            say("run", f"Port {port} ({name}) is already in use - SignalScout may already be running. Close that window first.")
            return 1

    npm = "npm.cmd" if IS_WIN else "npm"
    if not args.no_build and dist_is_stale():
        say("run", "building the web app for phones (one-time after changes) ...")
        if subprocess.run([npm, "run", "build"], cwd=ROOT / "frontend", shell=IS_WIN).returncode != 0:
            say("run", "web build failed - the dashboard on port 5202 still works; phones need a successful build")

    RUNTIME.mkdir(parents=True, exist_ok=True)
    TUNNEL_FILE.unlink(missing_ok=True)
    STOP_FILE.unlink(missing_ok=True)

    say("run", f"starting API on port {api_port} ...")
    start("api", [str(PY), "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", host, "--port", str(api_port),
                  "--no-access-log", "--timeout-graceful-shutdown", "3"], ROOT)
    if not wait_http(f"http://127.0.0.1:{api_port}/api/health", 90):
        say("run", "the API did not start - see the [api] lines above")
        stop_all()
        return 1

    say("run", f"starting web dev server on port {web_port} ...")
    start("web", f"{npm} run dev", ROOT / "frontend", shell=True)

    tunnel_url: dict[str, str] = {}
    cloudflared = ROOT / "tools" / "cloudflared.exe"
    if env.get("TUNNEL_ENABLED", "true").lower() in ("1", "true", "yes", "on") and not args.no_tunnel:
        if cloudflared.exists():
            def on_tunnel(line: str) -> None:
                m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
                if m and "url" not in tunnel_url:
                    tunnel_url["url"] = m.group(0)
                    TUNNEL_FILE.write_text(json.dumps({"url": m.group(0), "started_at": datetime.now(timezone.utc).isoformat(), "pid": children["tunnel"].pid}), encoding="utf-8")
            start("tunnel", [str(cloudflared), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{api_port}"], ROOT, on_tunnel)
        else:
            say("tunnel", "tools/cloudflared.exe not found - run setup.bat to enable the phone HTTPS link")

    sim = ROOT / "scripts" / "esp32_simulator.py"
    if env.get("ESP32_SIMULATOR", "true").lower() in ("1", "true", "yes", "on") and not args.no_simulator and sim.exists():
        start("sim", [str(PY), str(sim), "--api", f"http://127.0.0.1:{api_port}"], ROOT)

    wait_http(f"http://127.0.0.1:{web_port}", 60)
    for _ in range(40):
        if "url" in tunnel_url or "tunnel" not in children:
            break
        time.sleep(0.5)

    line = "=" * 64
    print(f"\n{line}\n  SignalScout is running\n{line}")
    print(f"  Dashboard      http://localhost:{web_port}")
    print(f"  API + docs     http://localhost:{api_port}/docs")
    if "url" in tunnel_url:
        print(f"  Phone (HTTPS)  {tunnel_url['url']}   (QR code: Dashboard > Connect a phone)")
    print("  Demo sign-in   user@signalscout.demo / engineer@signalscout.demo / admin@signalscout.demo")
    print("  Password       Scout@2026")
    print(f"  Stop           press Ctrl+C in this window\n{line}\n", flush=True)
    if not args.no_browser:
        webbrowser.open(f"http://localhost:{web_port}")

    def handle(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle)
    try:
        while True:
            time.sleep(1)
            if STOP_FILE.exists():
                STOP_FILE.unlink(missing_ok=True)
                raise KeyboardInterrupt
            for tag in ("api", "web"):
                if children[tag].poll() is not None:
                    say("run", f"{tag} stopped unexpectedly (exit {children[tag].returncode}) - shutting down")
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        say("run", "stopping SignalScout ...")
    finally:
        stop_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
