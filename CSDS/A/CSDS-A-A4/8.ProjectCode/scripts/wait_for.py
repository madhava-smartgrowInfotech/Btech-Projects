"""Wait until a URL answers with HTTP 200:  python scripts/wait_for.py URL [timeout_s]"""
import sys
import time
import urllib.request

url = sys.argv[1]
limit = float(sys.argv[2]) if len(sys.argv) > 2 else 120
t0 = time.time()
while time.time() - t0 < limit:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            if r.status == 200:
                print(f"[ok] {url} is up")
                sys.exit(0)
    except Exception:  # noqa: BLE001
        pass
    time.sleep(1)
print(f"[X] {url} did not come up within {limit:.0f}s")
sys.exit(1)
