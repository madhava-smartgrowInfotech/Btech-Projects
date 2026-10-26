"""Download the two public real-image sets used to evaluate the vision layer (git-ignored, data/external).

* visaitech/vehicle-mixed-traffic-detection (CC BY 4.0): 293 dashcam frames, 4 classes, YOLO labels.
* shravya11/ambulance-images (CC BY 4.0): 2,121 ambulance and 2,628 non-ambulance photos; first N of each are fetched.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "external"
N_AMB = int(sys.argv[1]) if len(sys.argv) > 1 else 300


def listing(repo):
    with urllib.request.urlopen(f"https://huggingface.co/api/datasets/{repo}?blobs=true", timeout=60) as r:
        return sorted(s["rfilename"] for s in json.load(r)["siblings"])


def fetch(args):
    repo, rel, dest = args
    if dest.exists() and dest.stat().st_size:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/datasets/{repo}/resolve/main/" + urllib.parse.quote(rel)
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                dest.write_bytes(r.read())
            return
        except Exception:
            pass
    print("failed", rel)


def main():
    jobs = []
    repo = "visaitech/vehicle-mixed-traffic-detection"
    for f in listing(repo):
        if f.startswith(("images/", "labels/")) and f.endswith((".jpg", ".txt")):
            jobs.append((repo, f, OUT / "mixed_traffic" / f))
    for f in ("classes.txt", "README.md"):
        jobs.append((repo, f, OUT / "mixed_traffic" / f))
    repo = "shravya11/ambulance-images"
    files = listing(repo)
    for cls in ("ambulance", "noambulance"):
        sel = [f for f in files if f.startswith(cls + "/") and f.lower().endswith((".jpg", ".jpeg", ".png"))][:N_AMB]
        for f in sel:
            jobs.append((repo, f, OUT / "ambulance_cls" / f))
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(fetch, jobs))
    print(len(jobs), "files ->", OUT)


if __name__ == "__main__":
    main()
