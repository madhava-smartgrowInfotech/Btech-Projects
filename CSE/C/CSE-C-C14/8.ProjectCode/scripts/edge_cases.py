"""Edge-case checks of POST /api/analyze with the real models -> docs/metrics/edge_cases.json.

Uses the Flask test client (no server needed). Each case sends one image and records the HTTP status, the verdict (when
analysed) and the error message (when refused). Run from the project folder:

    python scripts/edge_cases.py
"""
import io
import json
import os
import sys
import time

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import torch  # noqa: E402,F401  (import torch before the rest, as on this machine)

from app import config, create_app  # noqa: E402


def png(img, fmt="PNG", **kw):
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def noise(w, h, mode="RGB", seed=0):
    rng = np.random.RandomState(seed)
    ch = {"RGB": 3, "RGBA": 4, "L": 1}[mode]
    arr = rng.randint(0, 255, (h, w, ch) if ch > 1 else (h, w), dtype=np.uint8)
    return Image.fromarray(arr, mode)


def main():
    client = create_app().test_client()
    tok = client.post("/api/auth/login", json={"email": config.DEMO_EMAIL, "password": config.DEMO_PASSWORD}).get_json()["token"]
    hdr = {"Authorization": "Bearer " + tok}

    test_real = sorted(os.listdir(os.path.join(ROOT, "data", "cifake", "test", "real")))[0]
    sample = open(os.path.join(ROOT, "data", "cifake", "test", "real", test_real), "rb").read()
    jpg = png(noise(300, 200), "JPEG", quality=90)
    cases = [
        ("32 px CIFAKE test image (PNG)", "a.png", sample),
        ("Grayscale PNG 64 x 64", "gray.png", png(noise(64, 64, "L"))),
        ("RGBA PNG 64 x 64 with alpha channel", "rgba.png", png(noise(64, 64, "RGBA"))),
        ("WebP 64 x 64", "w.webp", png(noise(64, 64), "WEBP")),
        ("Smallest accepted size, 8 x 8 PNG", "tiny8.png", png(noise(8, 8))),
        ("7 x 7 PNG (below the minimum)", "tiny7.png", png(noise(7, 7))),
        ("Large JPEG 2,000 x 1,500", "big.jpg", png(noise(2000, 1500), "JPEG", quality=90)),
        ("Upper-case extension .PNG", "UPPER.PNG", sample),
        ("PNG bytes with a .jpg extension", "mislabelled.jpg", sample),
        ("Truncated JPEG (first half of the bytes)", "trunc.jpg", jpg[: len(jpg) // 2]),
        ("Text file named .png", "text.png", b"this is not an image" * 50),
        ("Empty file", "empty.png", b""),
        ("GIF image (extension not allowed)", "anim.gif", png(noise(32, 32), "GIF")),
        ("Path-like file name ../../x.png", "../../x.png", sample),
    ]
    out = []
    for name, fname, data in cases:
        t = time.perf_counter()
        r = client.post("/api/analyze", data={"image": (io.BytesIO(data), fname)}, headers=hdr, content_type="multipart/form-data")
        dt = time.perf_counter() - t
        j = r.get_json() or {}
        row = {"case": name, "status": r.status_code, "seconds": round(dt, 2)}
        if r.status_code == 200:
            row.update({"verdict": j["predicted_label"], "confidence_pct": j["confidence_pct"], "consistency": j["robustness"]["consistency"],
                        "cams_ok": all(bool(j["cams"].get(k)) for k in ("a1", "b", "c"))})
        else:
            row["error"] = j.get("error")
        out.append(row)
        print(row, flush=True)

    # determinism: the same image twice gives the same fused probability
    a = client.post("/api/analyze", data={"image": (io.BytesIO(sample), "a.png")}, headers=hdr, content_type="multipart/form-data").get_json()
    b = client.post("/api/analyze", data={"image": (io.BytesIO(sample), "a.png")}, headers=hdr, content_type="multipart/form-data").get_json()
    det = {"same_image_twice_identical_probability": a["prob_fake"] == b["prob_fake"], "prob_fake_first": a["prob_fake"], "prob_fake_second": b["prob_fake"]}
    # oversize request
    big = io.BytesIO(b"\0" * (config.MAX_CONTENT_LENGTH + 1024))
    r = client.post("/api/analyze", data={"image": (big, "big.png")}, headers=hdr, content_type="multipart/form-data")
    out.append({"case": "Upload of 10 MB + 1 KB", "status": r.status_code, "error": (r.get_json() or {}).get("error")})
    # token checks
    r1 = client.post("/api/analyze", data={"image": (io.BytesIO(sample), "a.png")}, content_type="multipart/form-data")
    r2 = client.post("/api/analyze", data={"image": (io.BytesIO(sample), "a.png")}, headers={"Authorization": "Bearer " + tok[:-3] + "xyz"}, content_type="multipart/form-data")
    out.append({"case": "No token", "status": r1.status_code})
    out.append({"case": "Token with altered signature", "status": r2.status_code})
    os.makedirs(os.path.join(ROOT, "docs", "metrics"), exist_ok=True)
    json.dump({"cases": out, "determinism": det, "device": "cpu"}, open(os.path.join(ROOT, "docs", "metrics", "edge_cases.json"), "w", encoding="utf-8"), indent=2)
    print(det)


if __name__ == "__main__":
    main()
