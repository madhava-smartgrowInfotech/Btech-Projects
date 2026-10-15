"""Render a deck to PNG through PowerPoint (COM) and build contact sheets for a visual check.

    python scripts/render_deck.py "<deck.pptx>" <out_dir> [columns]
"""
from __future__ import annotations

import sys
from pathlib import Path

import win32com.client as win32
from PIL import Image


def main():
    deck, out = Path(sys.argv[1]), Path(sys.argv[2])
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    out.mkdir(parents=True, exist_ok=True)
    app = win32.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(deck), WithWindow=False)
    n = pres.Slides.Count
    for i in range(1, n + 1):
        pres.Slides(i).Export(str(out / f"s{i:02d}.png"), "PNG", 1280, 720)
    pres.Close()
    app.Quit()
    files = sorted(out.glob("s*.png"))
    per = cols * 2
    for k in range(0, len(files), per):
        chunk = files[k:k + per]
        ims = [Image.open(f) for f in chunk]
        w, h = ims[0].size
        sheet = Image.new("RGB", (cols * w // 2, ((len(ims) + cols - 1) // cols) * h // 2), "white")
        for j, im in enumerate(ims):
            sheet.paste(im.resize((w // 2, h // 2)), ((j % cols) * w // 2, (j // cols) * h // 2))
        sheet.save(out / f"sheet_{k // per + 1:02d}.png")
    print(n, "slides rendered to", out)


if __name__ == "__main__":
    main()
