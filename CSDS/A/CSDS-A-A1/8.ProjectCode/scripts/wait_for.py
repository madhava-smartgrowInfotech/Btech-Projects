"""Wait until a URL answers with HTTP 200 (used by run.bat). Usage: wait_for.py <url> [timeout-seconds]"""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request


def main() -> int:
    url = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 120
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:  # noqa: S310 - local URL only
                if resp.status == 200:
                    print(f"[OK]   {url} is up")
                    return 0
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            pass
        print(".", end="", flush=True)
        time.sleep(1.5)
    print(f"\n[X]    {url} did not respond within {timeout:.0f}s - check the server window for errors.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
