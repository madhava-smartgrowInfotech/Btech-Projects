"""Render a deck to PNG (PowerPoint COM) and write contact sheets.  python scripts/render_deck.py <pptx> <out_dir>"""
import sys
from pathlib import Path
import win32com.client as w32
from PIL import Image

src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
for f in out.glob("*.png"):
    f.unlink()
app = w32.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(str(src), WithWindow=False)
n = pres.Slides.Count
for i in range(1, n + 1):
    pres.Slides(i).Export(str(out / f"s{i:02d}.png"), "PNG", 960, 540)
pres.Close(); app.Quit()
ims = [Image.open(out / f"s{i:02d}.png") for i in range(1, n + 1)]
per = 6
for k in range(0, n, per):
    chunk = ims[k:k + per]
    W, H = chunk[0].size
    sheet = Image.new("RGB", (W * 2, H * 3), "white")
    for j, im in enumerate(chunk):
        sheet.paste(im, ((j % 2) * W, (j // 2) * H))
    sheet.save(out / f"sheet{k // per + 1}.png")
print(n, "slides")
