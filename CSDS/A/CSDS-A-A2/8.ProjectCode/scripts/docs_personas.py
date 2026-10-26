"""
Pick stand-in face photographs for the documentation screenshots.

The product ships no student photos. For the screenshots every demo student is given real photographs of
one LFW identity (public benchmark): one reference photo for enrolment, one neutral photo for check-in, and
for every liveness challenge a second photo of the same person that actually satisfies that challenge
(checked with core.liveness.verify_challenge). TILT challenges fall back to a rotated copy of the neutral
photo, exactly as scripts/smoke_test.py does.

    venv\\Scripts\\python scripts\\docs_personas.py --lfw <dir with lfw/> --out personas.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import face_match, liveness  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--lfw", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--count", type=int, default=7)
ap.add_argument("--names", default="", help="comma list of LFW identities to consider (default: all with >= 12 photos)")
args = ap.parse_args()

LFW = Path(args.lfw) / "lfw"
CH = list(liveness.CHALLENGES)
cands = []
for d in sorted(LFW.iterdir()):
    imgs = sorted(d.glob("*.jpg"))
    if len(imgs) < 12 or (args.names and d.name not in args.names.split(",")):
        continue
    ms = {p: liveness.analyze(cv2.imread(str(p))) for p in imgs}
    emb_cache = {}

    def emb(p):
        if p not in emb_cache:
            try:
                emb_cache[p] = face_match.embed(cv2.imread(str(p)))
            except face_match.FaceError:
                emb_cache[p] = None
        return emb_cache[p]

    neutrals = [p for p in imgs if liveness.check_neutral(ms[p]) is None and abs(ms[p].yaw) < 0.04 and emb(p) is not None]
    if len(neutrals) < 2:
        continue
    best = None
    for n in neutrals[:5]:
        enr = next((p for p in neutrals if p != n and face_match.cosine(emb(p), emb(n)) >= 0.55), None)
        if enr is None:
            continue
        cover = {}
        for c in CH:
            for p in imgs:
                if p != n and ms[p].ok and liveness.verify_challenge(c, ms[n], ms[p]).passed:
                    e = emb(p)
                    if e is not None and face_match.cosine(e, emb(n)) >= 0.55:
                        cover[c] = p
                        break
        if best is None or len(cover) > len(best[1]):
            best = (n, cover, enr)
    if best is None:
        continue
    n, cover, enroll = best
    cands.append({"name": d.name, "enroll": str(enroll), "neutral": str(n),
                  "challenge": {c: str(p) for c, p in cover.items()}, "coverage": len(cover)})
    print(d.name, len(cover), flush=True)

cands.sort(key=lambda c: -c["coverage"])
chosen = cands[: args.count]
Path(args.out).write_text(json.dumps(chosen, indent=1))
print("chosen:", [(c["name"], c["coverage"]) for c in chosen])
