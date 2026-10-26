"""
Photo-bank attack against the FULL verification chain (liveness + frame consistency + identity).

Scenario: an attacker holds several real photographs of the victim (LFW identities with >= 10 photos) and,
after seeing which challenge was issued, submits the best pair they own. The victim's enrolled reference
face is one further photo of the victim that the attacker does not hold. The attacker tries up to
5 neutral-quality photos as "photo 1". A pair succeeds when:
  liveness.verify_challenge passes AND cosine(emb1, emb2) >= FRAME_CONSISTENCY_THRESHOLD
  AND cosine(emb1, enrolled) >= IDENTITY_THRESHOLD   (single-face embeddings required)
Geo-fence, device and duplicate checks are NOT modelled here (they are independent of the photos).

    venv\\Scripts\\python scripts\\eval_photo_bank_attack.py --lfw DIR   ->  docs/evaluation/photo_bank_attack.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from core import face_match, liveness  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--lfw", required=True)
args = ap.parse_args()
LFW = Path(args.lfw) / "lfw"
OUT = ROOT / "docs" / "evaluation"
CH = list(liveness.CHALLENGES)


def main() -> None:
    res = {c: {"liveness_only": 0, "full_chain": 0} for c in CH}
    victims = 0
    for d in sorted(LFW.iterdir()):
        imgs = sorted(d.glob("*.jpg"))
        if len(imgs) < 10:
            continue
        ms = {p: liveness.analyze(cv2.imread(str(p))) for p in imgs}
        cache = {}

        def emb(p):
            if p not in cache:
                try:
                    cache[p] = face_match.embed(cv2.imread(str(p)))
                except face_match.FaceError:
                    cache[p] = None
            return cache[p]

        neutral_ok = [p for p in imgs if liveness.check_neutral(ms[p]) is None]
        # the enrolled reference photo is held out from the attacker
        enrolled = next((p for p in neutral_ok if emb(p) is not None), None)
        if enrolled is None:
            continue
        bank = [p for p in imgs if p != enrolled]
        neutrals = [p for p in bank if liveness.check_neutral(ms[p]) is None][:5]
        if not neutrals:
            continue
        victims += 1
        e_enr = emb(enrolled)
        for c in CH:
            live_hit = full_hit = False
            for n in neutrals:
                for p in bank:
                    if p == n or not ms[p].ok or not liveness.verify_challenge(c, ms[n], ms[p]).passed:
                        continue
                    live_hit = True
                    e1, e2 = emb(n), emb(p)
                    if (e1 is not None and e2 is not None
                            and face_match.cosine(e1, e2) >= config.FRAME_CONSISTENCY_THRESHOLD
                            and face_match.cosine(e1, e_enr) >= config.IDENTITY_THRESHOLD):
                        full_hit = True
                        break
                if full_hit:
                    break
            res[c]["liveness_only"] += live_hit
            res[c]["full_chain"] += full_hit
        print(d.name, flush=True)
    out = {"dataset": "LFW identities with >= 10 photos", "victims": victims,
           "thresholds": {"identity": config.IDENTITY_THRESHOLD, "frame_consistency": config.FRAME_CONSISTENCY_THRESHOLD},
           "by_challenge": {c: {**v, "liveness_only_rate": v["liveness_only"] / victims,
                                "full_chain_rate": v["full_chain"] / victims} for c, v in res.items()}}
    (OUT / "photo_bank_attack.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["by_challenge"], indent=1))


if __name__ == "__main__":
    main()
