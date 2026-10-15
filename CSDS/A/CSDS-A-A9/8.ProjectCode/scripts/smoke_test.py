"""End-to-end smoke test for the ForgetSafe JSON API.

Starts its own server on a spare port with a throw-away working directory (so the real
audit ledger is untouched), then walks the main flow: train -> generate -> unlearn ->
certificate -> audit verify -> error cases.  Use --url to test an already running server.

    python scripts/smoke_test.py
    python scripts/smoke_test.py --url http://127.0.0.1:8109
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def call(base: str, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode())


def check(condition: bool, label: str) -> None:
    print(("PASS  " if condition else "FAIL  ") + label)
    if not condition:
        raise SystemExit(1)


def run(base: str) -> None:
    status, health = call(base, "GET", "/api/health")
    check(status == 200 and health["status"] == "ok", "health endpoint")

    status, state = call(base, "GET", "/api/state")
    check(status == 200 and state["trained"] is False and len(state["contributions"]) == 5, "fresh state is untrained with 5 clients")

    status, body = call(base, "POST", "/api/unlearn", {"client_id": "client_finance"})
    check(status == 400 and "error" in body, "unlearn before training is rejected")

    status, body = call(base, "POST", "/api/generate", {"seed": "privacy"})
    check(status == 400, "generate before training is rejected")

    status, metrics = call(base, "POST", "/api/train")
    check(status == 200 and metrics["active_clients"] == 5 and metrics["epsilon"] > 0, "training returns metrics")

    status, sample = call(base, "POST", "/api/generate", {"seed": "privacy"})
    check(status == 200 and sample["text"].startswith("privacy"), "generate returns text")

    status, cert = call(base, "POST", "/api/unlearn", {"client_id": "client_finance"})
    check(status == 200 and cert["status"] == "CERTIFIED" and cert["clients_after"] == 4, "unlearning issues a certified certificate")
    check(cert["reference_retrain_l2"] <= 1e-10 and len(cert["audit_record_hash"]) == 64, "certificate verifies against clean recomputation")

    status, body = call(base, "POST", "/api/unlearn", {"client_id": "client_finance"})
    check(status == 400, "repeat unlearning of the same client is rejected")

    status, latest = call(base, "GET", "/api/certificate/latest")
    check(status == 200 and latest["certificate_id"] == cert["certificate_id"] and latest["audit_valid"], "latest certificate downloadable")

    status, verify = call(base, "POST", "/api/audit/verify")
    check(status == 200 and verify["valid"] is True, "audit hash chain verifies")

    status, state = call(base, "GET", "/api/state")
    events = [r["event_type"] for r in state["audit"]["records"]]
    check(events == ["FEDERATED_TRAINING", "CLIENT_UNLEARNING"], "audit ledger recorded training then unlearning")

    status, session = call(base, "POST", "/api/session")
    check(status == 200 and session["session_id"] != state["session_id"], "new session created")
    status, state = call(base, "GET", "/api/state")
    check(state["trained"] is False and len(state["audit"]["records"]) == 2, "new session is untrained, audit history preserved")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="test an already running server instead of starting one")
    parser.add_argument("--port", type=int, default=8199, help="port for the temporary server (default 8199)")
    args = parser.parse_args()

    if args.url:
        run(args.url.rstrip("/"))
        print("Smoke test passed.")
        return

    with tempfile.TemporaryDirectory(prefix="forgetsafe_smoke_") as workdir:
        server = subprocess.Popen(
            [sys.executable, str(ROOT / "app.py"), "--port", str(args.port)],
            cwd=workdir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{args.port}"
        try:
            for _ in range(50):
                try:
                    call(base, "GET", "/api/health")
                    break
                except OSError:
                    time.sleep(0.2)
            else:
                raise SystemExit("FAIL  server did not start")
            run(base)
        finally:
            server.terminate()
            server.wait(timeout=10)
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
