"""End-to-end smoke test of the SignSpeak API (collect -> train -> report -> recognize).

It copies `sign_language_app/` and `backend/` into a temporary folder and starts its own API there,
so the real `data/` and `models/` folders are never touched. It uses synthetic frames (a disc for
class A, a square for class B inside the ROI box) - this proves the wiring, not recognition quality.

    pip install httpx   # once
    python scripts/smoke_test.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import httpx
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PORT = 8399
BASE = f"http://127.0.0.1:{PORT}/api"
ROI = (620, 90, 920, 390)          # get_roi_box(960, 540)

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def frame_jpeg(kind: str, rng: np.random.Generator) -> bytes:
    img = np.zeros((540, 960, 3), np.uint8)
    x1, y1, x2, y2 = ROI
    cx = int(rng.integers(x1 + 100, x2 - 100))
    cy = int(rng.integers(y1 + 100, y2 - 100))
    r = int(rng.integers(55, 85))
    if kind == "disc":
        cv2.circle(img, (cx, cy), r, (230, 230, 230), -1)
    else:
        cv2.rectangle(img, (cx - r, cy - r), (cx + r, cy + r), (230, 230, 230), -1)
    img = cv2.add(img, rng.integers(0, 12, img.shape, dtype=np.uint8))
    ok, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="signspeak_smoke_"))
    for folder in ("sign_language_app", "backend"):
        shutil.copytree(ROOT / folder, work / folder, ignore=shutil.ignore_patterns("__pycache__", "gui"))
    # the desktop GUI package is not needed by the API
    (work / "sign_language_app" / "gui").mkdir(exist_ok=True)
    (work / "sign_language_app" / "gui" / "__init__.py").write_text("")
    log = open(work / "api.log", "w")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=work, stdout=log, stderr=subprocess.STDOUT, env={**os.environ, "TF_CPP_MIN_LOG_LEVEL": "2"},
    )
    try:
        client = httpx.Client(base_url=BASE, timeout=60)
        for _ in range(90):
            try:
                if client.get("/health").status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(1)
        else:
            print("API did not start. Log:\n" + (work / "api.log").read_text())
            return 1

        r = client.get("/health").json()
        check("health", r["status"] == "ok" and not r["model_loaded"], str(r))
        cfg = client.get("/config").json()
        check("config", len(cfg["classes"]) == 29 and cfg["roi"]["x1"] == ROI[0], f"{len(cfg['classes'])} classes, roi={cfg['roi']}")
        about = client.get("/about").json()
        check("about", len(about["pipeline"]) == 8 and "DOI" in about["base_paper"])
        ds = client.get("/dataset").json()
        check("dataset empty", ds["total"] == 0 and not ds["ready_to_train"])
        check("model before training", client.get("/model").json() == {"trained": False})
        check("train needs 2 classes", client.post("/train/start", json={"epochs": 1, "batch_size": 8, "learning_rate": 0.001}).status_code == 409)
        check("train validation", client.post("/train/start", json={"epochs": 0, "batch_size": 8, "learning_rate": 0.001}).status_code == 400)
        check("unknown class rejected", client.post("/collect/ZZ", files={"frame": ("f.jpg", b"x", "image/jpeg")}).status_code == 404)
        check("bad frame rejected", client.post("/collect/A", files={"frame": ("f.jpg", b"not an image", "image/jpeg")}).status_code == 400)
        check("speak empty rejected", client.post("/tts/speak", json={"text": "  "}).status_code == 400)
        check("recognize without model", client.post("/recognize/frame", files={"frame": ("f.jpg", b"x", "image/jpeg")}, data={"session_id": "x"}).status_code == 409)

        rng = np.random.default_rng(0)
        for cls, kind in (("A", "disc"), ("B", "square")):
            for _ in range(40):
                r = client.post(f"/collect/{cls}", files={"frame": ("f.jpg", frame_jpeg(kind, rng), "image/jpeg")})
                assert r.status_code == 200, r.text
        ds = client.get("/dataset").json()
        check("collect saved images", ds["counts"]["A"] == 40 and ds["counts"]["B"] == 40 and ds["ready_to_train"], str(ds["total"]))
        imgs = client.get("/dataset/A/images?limit=5").json()
        check("image list", imgs["total"] == 40 and len(imgs["images"]) == 5)
        first = client.get(imgs["images"][0]["url"].removeprefix("/api"))
        check("image fetch", first.status_code == 200 and first.headers["content-type"] == "image/png")
        prev = client.post("/preview", files={"frame": ("f.jpg", frame_jpeg("disc", rng), "image/jpeg")}).json()
        check("preview mask", prev["mask"].startswith("data:image/png;base64,"))

        # stop request: start a long run, stop it after the first epoch
        r = client.post("/train/start", json={"epochs": 40, "batch_size": 8, "learning_rate": 0.001})
        check("train start (long run)", r.status_code == 200)
        check("second start rejected while running", client.post("/train/start", json={"epochs": 1, "batch_size": 8, "learning_rate": 0.001}).status_code == 409)
        for _ in range(120):
            if client.get("/train/status").json()["epoch"] >= 1:
                break
            time.sleep(1)
        client.post("/train/stop")
        for _ in range(120):
            status = client.get("/train/status").json()
            if status["state"] in ("done", "error"):
                break
            time.sleep(1)
        check("train stopped early", status["state"] == "done" and status["epoch"] < 40, f"stopped at epoch {status['epoch']}")

        r = client.post("/train/start", json={"epochs": 3, "batch_size": 8, "learning_rate": 0.001})
        check("train start", r.status_code == 200, r.text[:100])
        status = {}
        for _ in range(240):
            status = client.get("/train/status").json()
            if status["state"] in ("done", "error"):
                break
            time.sleep(1)
        check("train finished", status.get("state") == "done", status.get("error") or f"epochs run: {len(status['history']['accuracy'])}")
        if status.get("state") != "done":
            print((work / "api.log").read_text()[-2000:])
            return 1
        check("train history", len(status["history"]["accuracy"]) >= 1 and status["summary"]["test_accuracy"] >= 0)

        m = client.get("/model").json()
        check("model report", m["trained"] and m["test_accuracy"] is not None and len(m["report_rows"]) >= 2 and m["confusion_matrix"] is not None,
              f"test acc {m['test_accuracy']}")
        check("model loaded after training", client.get("/health").json()["model_loaded"])

        sid = client.post("/recognize/session").json()["session_id"]
        last = None
        for _ in range(25):
            last = client.post("/recognize/frame", files={"frame": ("f.jpg", frame_jpeg("disc", rng), "image/jpeg")}, data={"session_id": sid}).json()
        check("recognize frames", last is not None and last["label"] in ("A", "B") and 0 <= last["confidence"] <= 1, str(last and (last["label"], round(last["confidence"], 2))))
        check("recognize smoothing fields", isinstance(last["stable_label"], str) and "committed" in last and last["mask"].startswith("data:image/png"))
        check("recognize unknown session", client.post("/recognize/frame", files={"frame": ("f.jpg", frame_jpeg("disc", rng), "image/jpeg")}, data={"session_id": "nope"}).status_code == 404)
    finally:
        server.terminate()
        try:
            server.wait(10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()
        shutil.rmtree(work, ignore_errors=True)

    print("\nALL PASSED" if not failures else f"\nFAILED: {', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
