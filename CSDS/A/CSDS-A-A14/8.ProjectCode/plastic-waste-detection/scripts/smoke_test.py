"""
scripts/smoke_test.py
---------------------
End-to-end smoke test of the PlastiScan API (the layer the React app talks to).

    python scripts/smoke_test.py

If the API is not already running on port 8114 it is started for the test and
stopped afterwards. The test does NOT clear your detection history. A synthetic
image is used, so it normally detects nothing and therefore logs nothing; it
only checks that the whole pipeline (upload -> preprocess -> YOLO -> response)
runs and that the error paths answer correctly.
"""

import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.getenv("BACKEND_PORT", "8114"))
API = f"http://127.0.0.1:{PORT}"
FRONT = f"http://localhost:{os.getenv('FRONTEND_PORT', '5114')}"

failures = []


def check(ok, message):
    print(("PASS  " if ok else "FAIL  ") + message)
    if not ok:
        failures.append(message)


def call(method, path, body=None, headers=None, base=API):
    req = urllib.request.Request(base + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def multipart(filename, content, fields):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n".encode()
        + content
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def api_up():
    try:
        return call("GET", "/api/health")[0] == 200
    except OSError:
        return False


def wait_model(timeout=180):
    end = time.time() + timeout
    while time.time() < end:
        status, raw = call("GET", "/api/health")
        model = json.loads(raw)["model"]
        if model["ready"] or model["status"] == "error":
            return model
        time.sleep(2)
    return {"ready": False, "status": "timeout"}


def main():
    proc = None
    if not api_up():
        python = ROOT / ".venv" / "Scripts" / "python.exe"
        exe = str(python) if python.exists() else sys.executable
        print(f"Starting API on port {PORT} ...")
        proc = subprocess.Popen([exe, "-m", "uvicorn", "backend.main:app", "--port", str(PORT)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            if api_up():
                break
            time.sleep(1)
    try:
        check(api_up(), f"API answers on :{PORT}")
        model = wait_model()
        check(model["ready"], f"model loaded (fallback={model.get('used_fallback')})")

        status, raw = call("GET", "/api/health")
        health = json.loads(raw)
        check(health["device"] in ("cpu", "cuda"), f"device reported: {health['device']}")

        # synthetic ocean-blue image
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (640, 480), (30, 90, 160)).save(buf, "JPEG")
        body, headers = multipart("smoke_ocean.jpg", buf.getvalue(), {"conf": "0.5", "preprocess": "true"})
        status, raw = call("POST", "/api/detect", body, headers)
        check(status == 200, f"POST /api/detect -> {status}")
        if status == 200:
            d = json.loads(raw)
            check(d["annotated_image"].startswith("data:image/jpeg;base64,"), "annotated image returned")
            check(d["detection_count"] == len(d["detections"]) == len(d["rows"]), "counts consistent")
            check(d["logged"] == (d["detection_count"] > 0), "history logged only when objects were detected")

        body, headers = multipart("notes.txt", b"hello", {"conf": "0.5", "preprocess": "true"})
        status, raw = call("POST", "/api/detect", body, headers)
        check(status == 400 and "Invalid file format" in json.loads(raw)["detail"], "wrong extension rejected (400)")

        body, headers = multipart("broken.png", b"not really a png", {"conf": "0.5", "preprocess": "true"})
        status, raw = call("POST", "/api/detect", body, headers)
        check(status == 422 and "corrupted" in json.loads(raw)["detail"], "corrupted image rejected (422)")

        body, headers = multipart("smoke_ocean.jpg", buf.getvalue(), {"conf": "0.95", "preprocess": "true"})
        status, _ = call("POST", "/api/detect", body, headers)
        check(status == 422, "confidence outside 0.1-0.9 rejected (422)")

        status, raw = call("GET", "/api/history")
        rows = json.loads(raw)
        check(status == 200 and isinstance(rows, list), f"GET /api/history -> {len(rows)} rows")
        if rows:
            check({"filename", "object_count", "avg_confidence", "timestamp"} <= set(rows[0]), "history row shape")

        status, raw = call("GET", "/api/evaluation")
        ev = json.loads(raw)
        check(status == 200 and "available" in ev, f"GET /api/evaluation -> available={ev['available']}")
        status, _ = call("GET", "/api/evaluation/plots/../../etc/passwd")
        check(status == 404, "plot endpoint only serves whitelisted names")

        try:
            status, _ = call("GET", "/api/health", base=FRONT)
            check(status == 200, "frontend dev server proxies /api to the backend")
        except OSError:
            print("SKIP  frontend not running on :5114 (start it with run.bat to also test the proxy)")
    finally:
        if proc:
            proc.terminate()

    print("\nSMOKE TEST " + ("FAILED: " + "; ".join(failures) if failures else "PASSED"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
