"""Pick real tomato / onion / potato photos from the Vegetable Classification (Bangladesh) dataset for the demo and the report.

Source: Project-AgML/vegetable_classification_bangladesh on Hugging Face (CC BY 4.0), shards copied to C:/cs17/data.
Every candidate is graded by the shipped pipeline; a spread of grades is kept so that the screens show more than one outcome.
Writes resized JPEGs to docs/sample_inputs/ and a JSON log of what was chosen and why.

    venv\\Scripts\\python scripts/pick_sample_photos.py
"""
from __future__ import annotations

import io
import json

import pyarrow.parquet as pq
from PIL import Image

from exp_common import DATA, PROJECT

from app.ml.quality.infer import grade_image

LABELS = {7: "Onion", 9: "Potato", 11: "Tomato"}
PER_CROP_SCAN = 40
OUT = PROJECT / "docs" / "sample_inputs"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cands = {c: [] for c in LABELS.values()}
    for shard in sorted(DATA.glob("veg_*.parquet")):
        try:
            pf = pq.ParquetFile(shard)
        except Exception as e:  # a shard still downloading
            print("skip", shard.name, e)
            continue
        for batch in pf.iter_batches(batch_size=16):
            d = batch.to_pydict()
            for img, lab in zip(d["image"], d["label"]):
                if lab in LABELS and len(cands[LABELS[lab]]) < PER_CROP_SCAN:
                    im = Image.open(io.BytesIO(img["bytes"])).convert("RGB")
                    im.thumbnail((900, 900))
                    buf = io.BytesIO()
                    im.save(buf, "JPEG", quality=88)
                    cands[LABELS[lab]].append(buf.getvalue())
    log = {}
    for crop, imgs in cands.items():
        graded = []
        for i, b in enumerate(imgs):
            g = grade_image(b)
            graded.append((i, g["grade"], g["confidence"], b))
        log[crop] = {"scanned": len(graded), "grade_counts": {k: sum(1 for x in graded if x[1] == k) for k in ["A", "B", "C", "Reject"]}}
        # keep the first image of each grade found, up to 3 per crop
        kept = []
        seen = set()
        for i, grade, conf, b in graded:
            if grade not in seen and len(kept) < 3:
                seen.add(grade)
                kept.append((i, grade, conf, b))
        for n, (i, grade, conf, b) in enumerate(kept, 1):
            name = f"{crop.lower()}_{n}.jpg"
            (OUT / name).write_bytes(b)
            log[crop].setdefault("kept", []).append({"file": name, "candidate_index": i, "grade": grade, "confidence": round(conf, 3)})
    (OUT / "_chosen.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
