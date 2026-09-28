"""Opens a Cloudflare quick tunnel to the frontend and prints the https://...trycloudflare.com link.

No Cloudflare account needed. Keep this window open while using MediQueue on your phone.
"""
import os
import re
import shutil
import subprocess
import sys

PORT = os.getenv("FRONTEND_PORT", "5215")
exe = shutil.which("cloudflared") or r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not os.path.exists(exe) and not shutil.which("cloudflared"):
    sys.exit("cloudflared not found. Install it with:  winget install --id Cloudflare.cloudflared")

proc = subprocess.Popen([exe, "tunnel", "--no-autoupdate", "--url", f"http://localhost:{PORT}"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
shown = False
try:
    for line in proc.stdout:
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m and not shown:
            shown = True
            print("\n" + "=" * 64)
            print(f"  Open on your phone:  {m.group(0)}")
            print("=" * 64 + "\n  (keep this window open; Ctrl+C to stop)\n", flush=True)
        elif "ERR" in line:
            print(line.rstrip(), flush=True)
except KeyboardInterrupt:
    pass
finally:
    proc.terminate()
