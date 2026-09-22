"""Waits until a URL answers (used by run.bat before opening the browser).

Usage: python scripts/wait_for.py <url> [timeout_seconds]
"""
from __future__ import annotations

import sys
import time
import urllib.request


def main() -> int:
    url = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 90
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status < 500:
                    return 0
        except Exception:
            pass
        time.sleep(1)
    print(f"[!] {url} did not answer within {int(timeout)} seconds - check the server windows for errors.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
