"""Why does core.face_match.embed() reject some LFW images?  (reads the embedding cache of eval_face_verification.py)
    venv\Scripts\python scripts\eval_face_failures.py --cache lfw_emb.npz   ->  docs/evaluation/face_failures.json"""
import argparse, json, sys
from collections import Counter
from pathlib import Path
import cv2, numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from core import face_match
ap = argparse.ArgumentParser(); ap.add_argument("--cache", required=True); a = ap.parse_args()
cache = dict(np.load(a.cache, allow_pickle=True)["cache"].item())
bad = [k for k, v in cache.items() if v is None]
c = Counter()
for k in bad:
    try:
        face_match.embed(cv2.imread(k)); c["ok_on_retry"] += 1
    except face_match.FaceError as e:
        c["no_face" if "No face" in str(e) else "multiple_faces"] += 1
out = {"images": len(cache), "rejected": len(bad), "rate": len(bad) / len(cache), "reasons": dict(c)}
(ROOT / "docs" / "evaluation" / "face_failures.json").write_text(json.dumps(out, indent=1)); print(out)
