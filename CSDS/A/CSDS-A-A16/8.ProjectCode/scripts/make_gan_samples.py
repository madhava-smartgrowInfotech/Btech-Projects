"""Writes upload samples from the shipped cEmoGAN generator (clearly synthetic) for the compound-emotion output screens."""
import io, sys, json
from pathlib import Path
import torch, numpy as np, cv2
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.synthesize_compound import load_generator
from app.ml.gan_model import NOISE_DIM
from app.ml.taxonomy import BASIC_INDEX, COMPOUND_COMPONENTS, NUM_BASIC
from app.ml.inference import analyze_image_bytes
out = ROOT / "docs/screenshots/inputs"; out.mkdir(parents=True, exist_ok=True)
gen = load_generator(); torch.manual_seed(2026)
res = []
for key in ["happily_surprised", "sadly_fearful", "angrily_disgusted"]:
    a, b = COMPOUND_COMPONENTS[key]
    best = None
    for t in range(150):
        cond = torch.zeros(1, NUM_BASIC); cond[0, BASIC_INDEX[a]] = .5; cond[0, BASIC_INDEX[b]] = .5
        with torch.no_grad(): im = gen(torch.randn(1, NOISE_DIM), cond)
        g = ((im[0, 0].numpy() * .5 + .5) * 255).clip(0, 255).astype(np.uint8)
        g = cv2.resize(g, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
        canvas = np.full((360, 640), 235, np.uint8)
        gg = g[:320, :]; y0 = (360 - gg.shape[0]) // 2; x0 = (640 - gg.shape[1]) // 2
        canvas[y0:y0+gg.shape[0], x0:x0+gg.shape[1]] = gg
        buf = io.BytesIO(); Image.fromarray(canvas).save(buf, format="JPEG", quality=92); bts = buf.getvalue()
        ok, basic, comp, dom, _ = analyze_image_bytes(bts)
        if ok and comp[0]["key"] == key and (best is None or comp[0]["confidence"] > best[0]):
            best = (comp[0]["confidence"], bts, dom["label"], round(dom["confidence"], 3))
    if best:
        (out / f"gan_{key}.jpg").write_bytes(best[1])
        res.append(dict(file=f"gan_{key}.jpg", condition=key, top_compound_conf=round(best[0], 3), dominant=best[2], dominant_conf=best[3]))
        print(res[-1])
    else:
        print("no sample for", key)
json.dump(res, (out / "gan_samples.json").open("w"), indent=1)
