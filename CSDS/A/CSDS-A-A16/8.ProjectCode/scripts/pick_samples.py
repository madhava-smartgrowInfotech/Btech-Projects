"""Select real FER2013 test faces (upscaled 4x onto a 16:9 canvas) as upload samples for the output-screen captures."""
import io, json, pickle, sys
from pathlib import Path
import torch
import numpy as np, cv2
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.inference import analyze_image_bytes
items = pickle.load((ROOT / "backend/data/test.pt").open("rb"))
out = ROOT / "docs/screenshots/inputs"; out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(3)
order = rng.permutation(len(items))[:1500]
found = {}
for i in order:
    ex = items[i]
    g = np.array(Image.open(io.BytesIO(ex["img_bytes"])).convert("L"))
    g = cv2.resize(g, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    canvas = np.full((360 * 1, 640), 235, np.uint8)
    y0 = (360 - g.shape[0]) // 2; x0 = (640 - g.shape[1]) // 2
    canvas[y0:y0 + g.shape[0], x0:x0 + g.shape[1]] = g[:360, :]
    buf = io.BytesIO(); Image.fromarray(canvas).save(buf, format="JPEG", quality=92); b = buf.getvalue()
    ok, basic, comp, dom, _ = analyze_image_bytes(b)
    if not ok: continue
    key = (ex["labels"], dom["kind"])
    if key in found or sum(1 for k in found if k[0] == ex["labels"]) >= 2: continue
    name = f"{ex['labels']}_{len(found)+1:02d}.jpg"
    (out / name).write_bytes(b)
    found[key] = dict(file=name, true=ex["labels"], index=int(i), dominant=dom["label"], conf=round(dom["confidence"], 3), kind=dom["kind"],
                      top_basic=basic[0]["label"], top_compound=comp[0]["label"], top_compound_conf=round(comp[0]["confidence"], 3))
    print(found[key])
json.dump(list(found.values()), (out / "samples.json").open("w"), indent=1)
