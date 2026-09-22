"""Starts a Cloudflare quick tunnel to the web app and prints the HTTPS link + a QR code.

Used by run_phone.bat. The tunnel stays open while this window is open.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def find_cloudflared() -> str | None:
    configured = os.getenv("CLOUDFLARED_PATH", "").strip().strip('"')
    candidates = [
        configured,
        shutil.which("cloudflared") or "",
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    exe = find_cloudflared()
    if not exe:
        print("[x] cloudflared was not found. Install it with:  winget install --id Cloudflare.cloudflared")
        print("    then close this window and run run_phone.bat again.")
        return 1
    port = int(os.getenv("FRONTEND_PORT", "5204"))
    log_path = ROOT / "logs" / "cloudflared.log"
    log_path.parent.mkdir(exist_ok=True)
    if log_path.exists():
        log_path.unlink()
    proc = subprocess.Popen(
        [exe, "tunnel", "--no-autoupdate", "--url", f"http://localhost:{port}", "--logfile", str(log_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = None
    for _ in range(60):
        time.sleep(1)
        if proc.poll() is not None:
            break
        if log_path.exists():
            m = URL_RE.search(log_path.read_text(encoding="utf-8", errors="ignore"))
            if m:
                url = m.group(0)
                break
    if not url:
        print("[x] The tunnel did not start. Check your internet connection and logs\\cloudflared.log")
        proc.terminate()
        return 1

    print()
    print("  ================================================================")
    print("   Open this link on your phone (Chrome):")
    print(f"   {url}")
    print("  ================================================================")
    print()
    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.print_ascii(invert=True)
    except Exception:
        pass
    print("  Tip: in Chrome tap the menu (three dots) -> 'Add to Home screen' / 'Install app'.")
    print("  The link changes every time the tunnel starts. Keep this window open.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
