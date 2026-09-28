"""End-to-end smoke test against the running API (start it with run.bat first).

  venv\\Scripts\\python scripts/smoke_test.py [--base http://127.0.0.1:8108]
"""
import argparse
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
ok = True


def check(name, cond, detail=""):
    global ok
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
    ok &= bool(cond)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8108")
    base = ap.parse_args().base
    s = requests.Session()

    r = s.get(f"{base}/api/health", timeout=10)
    check("health", r.status_code == 200)

    email = f"smoke{int(time.time())}@example.com"
    r = s.post(f"{base}/api/auth/register", json={"name": "Smoke Test", "email": email, "password": "secret123"})
    check("register", r.status_code == 200)
    r = s.post(f"{base}/api/auth/login", json={"email": "demo@biosight.app", "password": "Demo@1234"})
    check("demo login", r.status_code == 200)
    s.headers["Authorization"] = f"Bearer {r.json()['token']}"
    check("auth required", requests.get(f"{base}/api/mri/samples").status_code == 401)
    check("me", s.get(f"{base}/api/auth/me").json().get("email") == "demo@biosight.app")

    # F1-F3 + F6: MRI
    models = s.get(f"{base}/api/mri/models").json()
    check("mri models available", all(m["available"] for m in models), str([m["key"] for m in models]))
    samples = s.get(f"{base}/api/mri/samples").json()
    pos = max(samples, key=lambda x: x["tumour_pixels"])
    r = s.post(f"{base}/api/mri/segment-sample", json={"name": pos["file"], "model": "jepa_10"}, timeout=180)
    res = r.json()
    check("segment sample", r.status_code == 200 and res["tumour_detected"],
          f"area={res.get('area_pixels')} dice_vs_gt={res.get('ground_truth', {}).get('dice')}")
    check("mri report", res.get("report", {}).get("report", {}).get("summary"), f"source={res['report']['source']}")
    with open(ROOT / "data" / "sample" / "lgg" / pos["file"], "rb") as f:
        r = s.post(f"{base}/api/mri/segment", files={"file": (pos["file"], f, "image/png")},
                   data={"model": "jepa_100", "pixel_spacing_mm": "0.9"}, timeout=180)
    check("segment upload", r.status_code == 200 and r.json()["overlay_png"].startswith("data:image/png"),
          f"area_mm2={r.json().get('area_mm2')}")
    r = s.post(f"{base}/api/mri/segment", files={"file": ("bad.png", b"not an image", "image/png")})
    check("bad upload rejected", r.status_code == 400)
    le = s.get(f"{base}/api/metrics/label-efficiency").json()["finetune"]
    check("label efficiency metrics", "jepa_10" in le and "unet_100" in le,
          f"jepa_10={le.get('jepa_10', {}).get('dice')} unet_100={le.get('unet_100', {}).get('dice')}")

    # F4: DNA
    dsamples = s.get(f"{base}/api/dna/samples").json()
    tri = next(d for d in dsamples if "trinucleotide" in d["name"])
    r = s.post(f"{base}/api/dna/classify", json={"sequence": tri["sequence"]}, timeout=180)
    res = r.json()
    check("dna classify", r.status_code == 200 and res["repeat_type"]["prediction"],
          f"repeat={res['repeat_type']['prediction']} organism={res['organism_class']['prediction']} "
          f"report={res.get('report', {}).get('source')}")
    check("dna repeat scan", len(res["repeat_scan"]) >= 1)
    r = s.post(f"{base}/api/dna/classify", json={"sequence": "ACGTXYZ"})
    check("bad sequence rejected", r.status_code == 400)

    # F5 + F6: STR
    loci = s.get(f"{base}/api/str/loci").json()
    check("str loci", len(loci["loci"]) == 20)
    sq = s.get(f"{base}/api/str/sample-query").json()
    r = s.post(f"{base}/api/str/match", json={"profile": sq["profile"]}, timeout=180)
    res = r.json()
    top = res["matches"][0]
    check("str match ranks source first", r.status_code == 200 and top["id"] == sq["source_id"],
          f"top={top['id']} log10LR={top['log10_lr']} second={res['matches'][1]['log10_lr']}")
    check("str report", res.get("report", {}).get("report", {}).get("summary"), f"source={res['report']['source']}")

    hist = s.get(f"{base}/api/history").json()
    check("history saved", len(hist) >= 4)
    check("all metrics", s.get(f"{base}/api/metrics/all").json().get("dna") is not None)
    print("\nSMOKE TEST", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
