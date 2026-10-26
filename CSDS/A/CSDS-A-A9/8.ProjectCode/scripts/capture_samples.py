"""Capture real request/response samples from the ForgetSafe API for the Results chapter.

Starts its own server on port 8197 from a throw-away working directory (the real audit ledger is untouched),
walks train -> generate -> unlearn -> generate -> audit verify -> error cases and writes
docs/sample_io/samples.json.   python scripts/capture_samples.py
"""
from __future__ import annotations

import http.client
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8197


def call(method, path, body=None):
    conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=20)
    data = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=data, headers={"Content-Type": "application/json"} if data else {})
    resp = conn.getresponse()
    payload = json.loads(resp.read().decode())
    conn.close()
    return resp.status, payload


def main():
    work = tempfile.mkdtemp(prefix="forgetsafe_samples_")
    proc = subprocess.Popen([sys.executable, str(ROOT / "app.py"), "--port", str(PORT)], cwd=work,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                call("GET", "/api/health")
                break
            except OSError:
                time.sleep(0.2)
        out = {}
        out["train"] = {"request": "POST /api/train", **dict(zip(("status", "response"), call("POST", "/api/train")))}
        out["generate_before"] = {"request": 'POST /api/generate {"seed": "privacy"}', **dict(zip(("status", "response"), call("POST", "/api/generate", {"seed": "privacy"})))}
        out["unlearn"] = {"request": 'POST /api/unlearn {"client_id": "client_finance"}', **dict(zip(("status", "response"), call("POST", "/api/unlearn", {"client_id": "client_finance"})))}
        out["generate_after"] = {"request": 'POST /api/generate {"seed": "privacy"}', **dict(zip(("status", "response"), call("POST", "/api/generate", {"seed": "privacy"})))}
        out["audit_verify"] = {"request": "POST /api/audit/verify", **dict(zip(("status", "response"), call("POST", "/api/audit/verify")))}
        out["repeat_unlearn"] = {"request": 'POST /api/unlearn {"client_id": "client_finance"}', **dict(zip(("status", "response"), call("POST", "/api/unlearn", {"client_id": "client_finance"})))}
        s, state = call("GET", "/api/state")
        out["state_audit_records"] = [{k: r[k] for k in ("sequence", "event_type", "previous_hash", "record_hash")} for r in state["audit"]["records"]]
        dest = ROOT / "docs" / "sample_io"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "samples.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("wrote docs/sample_io/samples.json")
    finally:
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    main()
