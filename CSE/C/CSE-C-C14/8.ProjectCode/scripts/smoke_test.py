"""End-to-end smoke test for VeriVision AI (API on 8414, optional frontend on 5414).

    python scripts/smoke_test.py

Exercises the main flow: health -> config/insights -> demo login -> analyze a real test
image -> robustness/Grad-CAM payload -> validation errors -> the unchanged classic pages
and /api/predict contract -> the Vite proxy. Exits non-zero on the first failed group.
"""
import glob
import io
import os
import sys

import requests
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.environ.get("API_URL", "http://127.0.0.1:8414")
WEB = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5414")
EMAIL = os.environ.get("VERIVISION_DEMO_EMAIL", "demo@verivision.ai")
PASSWORD = os.environ.get("VERIVISION_DEMO_PASSWORD", "Demo@1234")

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""), flush=True)
    if not cond:
        failures.append(name)


def sample(kind):
    files = sorted(glob.glob(os.path.join(ROOT, "data", "test", kind, "*.png")))
    if files:
        return files[0], open(files[0], "rb").read()
    buf = io.BytesIO()
    Image.new("RGB", (96, 96), (30, 140, 60) if kind == "real" else (90, 40, 200)).save(buf, format="PNG")
    return f"{kind}.png", buf.getvalue()


def main():
    # 1. health + public JSON
    r = requests.get(f"{API}/health", timeout=60)
    h = r.json()
    check("health reports models loaded", r.status_code == 200 and h["models_loaded"] is True, str(h))

    cfg = requests.get(f"{API}/api/config", timeout=30).json()
    check("config lists 4 branches and upload limits", len(cfg["branches"]) == 4 and cfg["max_mb"] > 0 and "png" in cfg["allowed_extensions"])
    check("config exposes the demo account", cfg["demo_account"]["email"] == EMAIL)

    ins = requests.get(f"{API}/api/insights", timeout=30).json()
    check("insights available with ensemble + models + robustness", ins["available"] and ins["ensemble"] and ins["models"] and ins["robustness"])
    check("confusion matrix image served", requests.get(f"{API}/artifacts/confusion_matrix.png", timeout=30).status_code == 200 or not ins["confusion_exists"])

    # 2. auth
    bad = requests.post(f"{API}/api/auth/login", json={"email": EMAIL, "password": "wrong"}, timeout=30)
    check("wrong password is rejected (401)", bad.status_code == 401 and "error" in bad.json())
    good = requests.post(f"{API}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    check("demo login succeeds and returns a token", good.status_code == 200 and good.json().get("token"))
    token = good.json()["token"]
    auth = {"Authorization": f"Bearer {token}"}
    me = requests.get(f"{API}/api/auth/me", headers=auth, timeout=30)
    check("token resolves to the demo user", me.status_code == 200 and me.json()["user"]["email"] == EMAIL)

    name, data = sample("fake")
    no_auth = requests.post(f"{API}/api/analyze", files={"image": (os.path.basename(name), data, "image/png")}, timeout=60)
    check("analyze without a token is rejected (401)", no_auth.status_code == 401)

    # 3. the main flow: analyze two real test images
    for kind in ("fake", "real"):
        name, data = sample(kind)
        r = requests.post(f"{API}/api/analyze", headers=auth, files={"image": (os.path.basename(name), data, "image/png")}, timeout=600)
        ok = r.status_code == 200
        check(f"analyze {kind} image returns 200", ok, r.text[:200])
        if not ok:
            continue
        d = r.json()
        check(f"{kind}: verdict + probabilities are consistent", d["predicted_label"] in ("REAL", "AI_GENERATED") and abs(d["prob_real"] + d["prob_fake"] - 1) < 1e-6)
        check(f"{kind}: 4 branch votes with weights", [b["key"] for b in d["branches"]] == ["a1", "a2", "b", "c"] and abs(sum(d["active_weights"].values()) - 1) < 1e-6)
        check(f"{kind}: Grad-CAM overlays for a1/b/c", all(str(d["cams"].get(k, "")).startswith("data:image/png;base64,") for k in ("a1", "b", "c")))
        check(f"{kind}: robustness outcomes + consistency", set(d["robustness"]["outcomes"]) >= {"original", "jpeg", "resize", "blur"} and "/" in d["robustness"]["consistency"])
        check(f"{kind}: original image echoed back", d["original_image"].startswith("data:image/"))

    # 4. validation errors
    r = requests.post(f"{API}/api/analyze", headers=auth, files={"image": ("notes.txt", b"hello", "text/plain")}, timeout=30)
    check("unsupported file type -> 400 with a message", r.status_code == 400 and "Unsupported" in r.json()["error"])
    r = requests.post(f"{API}/api/analyze", headers=auth, files={"image": ("broken.png", b"not really a png", "image/png")}, timeout=30)
    check("corrupt image -> 400 with a message", r.status_code == 400 and "decoded" in r.json()["error"])
    r = requests.post(f"{API}/api/analyze", headers=auth, timeout=30)
    check("no file -> 400 with a message", r.status_code == 400)

    # 5. the original (unchanged) surface
    name, data = sample("real")
    r = requests.post(f"{API}/api/predict", files={"image": (os.path.basename(name), data, "image/png")}, timeout=300)
    p = r.json()
    check("/api/predict keeps its JSON contract", r.status_code == 200 and {"predicted_label", "prob_real", "prob_fake", "confidence", "confidence_word", "branch_labels", "agreement_count"} <= set(p))
    check("classic HTML pages still render", all(requests.get(f"{API}{u}", timeout=30).status_code == 200 for u in ("/", "/insights")))
    r = requests.post(f"{API}/predict", files={"image": ("bad.txt", b"x", "text/plain")}, timeout=30)
    check("classic /predict still shows its error page", r.status_code == 400 and "couldn't complete" in r.text)

    # 6. frontend + proxy (skipped when the dev server is not running)
    try:
        page = requests.get(WEB, timeout=10)
    except requests.RequestException:
        print("SKIP frontend checks (dev server not running at " + WEB + ")")
    else:
        check("frontend serves the app shell", page.status_code == 200 and '<div id="root">' in page.text)
        check("frontend proxy reaches /health and /api/config", requests.get(f"{WEB}/health", timeout=30).status_code == 200 and requests.get(f"{WEB}/api/config", timeout=30).ok)

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: " + "; ".join(failures))
        sys.exit(1)
    print("Smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except requests.ConnectionError:
        print(f"Cannot reach the API at {API}. Start it with run.bat (or python run.py) and retry.")
        sys.exit(2)
