"""End-to-end smoke test against the running API.

Usage: python scripts/smoke_test.py   (backend must be running on BACKEND_PORT, default 8216)
"""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8216')}/api"
PASSWORD = os.getenv("DEMO_PASSWORD", "RetinaGuard@123")

CLINICAL = {"age": 62, "sex": 1, "cp": 0, "trestbps": 160, "chol": 286, "fbs": 0, "restecg": 0, "thalach": 108,
            "exang": 1, "oldpeak": 1.5, "slope": 1, "ca": 3, "thal": 2}


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)
    print("  ok -", msg)


def main():
    t0 = time.time()
    r = requests.get(f"{BASE}/health", timeout=10)
    check(r.ok and r.json()["retina_model"] and r.json()["heart_model"], "health: both models present")

    r = requests.post(f"{BASE}/auth/login", json={"email": "clinician@retinaguard.local", "password": "wrong"})
    check(r.status_code == 401, "login rejects a wrong password")
    r = requests.post(f"{BASE}/auth/login", json={"email": "clinician@retinaguard.local", "password": PASSWORD})
    check(r.ok, "clinician login")
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    check(requests.get(f"{BASE}/patients").status_code == 401, "patients endpoint requires login")

    r = requests.post(f"{BASE}/patients", json={"name": "Smoke Test Patient", "age": 62, "sex": "Male"}, headers=h)
    check(r.ok, f"create patient {r.json().get('code')}")
    pid = r.json()["id"]

    samples = requests.get(f"{BASE}/samples", headers=h).json()
    check(len(samples) > 0, f"{len(samples)} labelled sample images listed")
    sample = next((s for s in samples if s["label"] == 1), samples[0])
    img = requests.get(f"{BASE}/samples/{sample['name']}").content
    check(img[:4] == b"\x89PNG", f"download sample {sample['name']}")

    r = requests.post(f"{BASE}/screenings/image", headers=h, data={"patient_id": pid, "eye": "Right"},
                      files={"file": (sample["name"], img, "image/png")})
    check(r.ok, "upload fundus image -> pipeline ran")
    s = r.json()
    check(s["quality"]["passed"], f"quality check passed (sharpness {s['quality']['sharpness']})")
    check(all(s["images"]["steps"].values()), "4 preprocessing step images returned")
    check(len([v for v in s["images"]["wavelet"].values() if v]) == 8, "8 Haar sub-band images (2 levels x LL/LH/HL/HH)")
    check(s["images"]["heatmap"] and s["images"]["vessels"], "Grad-CAM heatmap and Frangi vessel map returned")
    check(0 <= s["retina"]["probability"] <= 1, f"retinopathy probability {s['retina']['probability']:.1%} ({s['retina']['label']})")

    bad = requests.post(f"{BASE}/screenings/image", headers=h, data={"patient_id": pid},
                        files={"file": ("x.png", b"not an image", "image/png")})
    check(bad.status_code == 400, "non-image upload rejected")
    bad = requests.post(f"{BASE}/screenings/{s['id']}/clinical", headers=h, json={**CLINICAL, "trestbps": 500})
    check(bad.status_code == 422, "out-of-range clinical value rejected")

    r = requests.post(f"{BASE}/screenings/{s['id']}/clinical", headers=h, json=CLINICAL)
    check(r.ok, "clinical form scored")
    s = r.json()
    check(0 <= s["heart"]["probability"] <= 1 and len(s["heart"]["factors"]) > 0,
          f"heart risk {s['heart']['probability']:.1%}, top factor: {s['heart']['factors'][0]['label']}")
    check(s["stage"] in ("Low", "Moderate", "High", "Very high") and s["stage_detail"]["recommendations"],
          f"combined stage {s['stage']} with {len(s['stage_detail']['recommendations'])} recommendations")

    r = requests.get(f"{BASE}/screenings/{s['id']}/report", headers=h)
    check(r.ok and r.content[:4] == b"%PDF" and len(r.content) > 20000, f"PDF report ({len(r.content) // 1024} KB)")

    p = requests.get(f"{BASE}/patients/{pid}", headers=h).json()
    check(p["screening_count"] == 1 and p["screenings"][0]["stage"] == s["stage"], "patient history shows the screening")
    check(any(x["id"] == s["id"] for x in requests.get(f"{BASE}/screenings", headers=h).json()), "screening in recent list")

    m = requests.get(f"{BASE}/metrics", headers=h).json()
    check("retina" in m and "heart" in m and "roc_auc" in m["retina"]["test"], "model performance metrics available")

    r = requests.post(f"{BASE}/auth/login", json={"email": "technician@retinaguard.local", "password": PASSWORD})
    check(r.ok and r.json()["user"]["role"] == "technician", "technician login")
    print(f"SMOKE TEST PASSED in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
