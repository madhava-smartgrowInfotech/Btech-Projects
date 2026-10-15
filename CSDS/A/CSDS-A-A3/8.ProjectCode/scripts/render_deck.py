"""Export every slide of a .pptx to PNG with PowerPoint COM (visual check).  python scripts/render_deck.py deck.pptx out_dir"""
from __future__ import annotations

import sys
from pathlib import Path

import win32com.client as win32

deck, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
app = win32.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(str(deck), WithWindow=False)
try:
    for i in range(1, pres.Slides.Count + 1):
        pres.Slides(i).Export(str(out / f"s{i:02d}.png"), "PNG", 1280, 720)
    print(pres.Slides.Count, "slides ->", out)
finally:
    pres.Close()
    app.Quit()
