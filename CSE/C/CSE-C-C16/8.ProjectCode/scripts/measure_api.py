"""Latency of the running API on 127.0.0.1 (localhost adds ~2 s per call on this PC): writes experiments/plantdoc/latency.json.

Starts its own backend (throw-away DB) on port 18418, measures start-up to /api/health, then POST /api/v1/detect/upload for 100 real
PlantDoc test photos (crop = tomato/potato/corn/apple/grape per photo) and GET /api/v1/history, /diseases, /dashboard.
Usage: python scripts/measure_api.py   (run while the PC is idle)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import smoke_test as S  # noqa: E402

S.PORT = 18418
S.BASE = f"http://127.0.0.1:{S.PORT}"
FOLDERS = [("Tomato_leaf_late_blight", "tomato"), ("Potato_leaf_early_blight", "potato"), ("Corn_rust_leaf", "corn"),
           ("Apple_Scab_Leaf", "apple"), ("grape_leaf_black_rot", "grape")]


def stats(v):
    v = np.asarray(v, float)
    return dict(n=len(v), mean=float(v.mean()), median=float(np.median(v)), p95=float(np.percentile(v, 95)), max=float(v.max()))


def main():
    tmp = Path(tempfile.mkdtemp(prefix="agrivision_lat_"))
    env = dict(os.environ, AGRIVISION_DB=str(tmp / "l.db"), AGRIVISION_UPLOADS=str(tmp / "up"), PYTHONHASHSEED="0")
    t0 = time.time()
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(S.PORT)], cwd=ROOT, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(200):
            try:
                if S.call("GET", "/api/health")[0] == 200:
                    break
            except Exception:
                time.sleep(0.25)
        startup = time.time() - t0
        tok = S.call("POST", "/api/v1/auth/login", {"email": "demo@agrivision.ai", "password": "demo1234"})[1]["token"]
        files = []
        for folder, crop in FOLDERS:
            ims = sorted((ROOT / "datasets" / "plantdoc-images" / "test" / folder).iterdir())[:8]
            files += [(p, crop) for p in ims]
        files = (files * 3)[:100]
        for p, crop in files[:5]:
            b, h = S.multipart(p.name, p.read_bytes(), {"crop_type": crop})
            S.call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)
        client, server, sizes = [], [], []
        for p, crop in files:
            data = p.read_bytes()
            sizes.append(len(data))
            b, h = S.multipart(p.name, data, {"crop_type": crop})
            a = time.perf_counter()
            s, r, _ = S.call("POST", "/api/v1/detect/upload", b, token=tok, headers=h)
            client.append((time.perf_counter() - a) * 1000)
            server.append(r["processing_time_ms"])
        out = dict(startup_s=startup, detect_client_ms=stats(client), detect_server_ms=stats(server), upload_kb=stats(np.array(sizes) / 1024))
        for name, path in (("health", "/api/health"), ("diseases", "/api/v1/diseases"), ("dashboard", "/api/v1/dashboard"),
                           ("history", "/api/v1/history?limit=20"), ("analytics", "/api/v1/analytics/dashboard")):
            v = []
            for _ in range(40):
                a = time.perf_counter()
                S.call("GET", path, token=tok)
                v.append((time.perf_counter() - a) * 1000)
            out[f"get_{name}_ms"] = stats(v)
        (ROOT / "experiments" / "plantdoc" / "latency.json").write_text(json.dumps(out, indent=1))
        print(json.dumps(out, indent=1))
    finally:
        srv.terminate()


if __name__ == "__main__":
    main()
