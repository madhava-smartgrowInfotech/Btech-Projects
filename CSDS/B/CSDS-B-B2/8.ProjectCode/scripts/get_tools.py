"""Download portable third-party tools into tools/ (git-ignored): cloudflared for the phone's HTTPS link.

    python scripts/get_tools.py
"""
from __future__ import annotations

import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
CLOUDFLARED = TOOLS / "cloudflared.exe"
URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"


def version(exe: Path) -> str | None:
    try:
        out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return None


def main() -> int:
    TOOLS.mkdir(exist_ok=True)
    if CLOUDFLARED.exists() and version(CLOUDFLARED):
        print(f"[OK]   cloudflared already present: {version(CLOUDFLARED)}")
        return 0
    print("[....] downloading cloudflared (about 55 MB) ...")
    tmp = CLOUDFLARED.with_suffix(".part")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "SignalScout-setup/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as out:
            while chunk := resp.read(1 << 20):
                out.write(chunk)
        tmp.replace(CLOUDFLARED)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        print(f"[FAIL] could not download cloudflared: {exc}")
        print("       The phone probe needs it. Alternative: winget install --id Cloudflare.cloudflared")
        return 1
    v = version(CLOUDFLARED)
    print(f"[OK]   cloudflared installed: {v}" if v else "[FAIL] cloudflared downloaded but does not run")
    return 0 if v else 1


if __name__ == "__main__":
    sys.exit(main())
