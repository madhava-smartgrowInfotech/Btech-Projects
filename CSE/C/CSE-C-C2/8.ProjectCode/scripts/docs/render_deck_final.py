"""Render a .pptx to PNGs with PowerPoint COM (absolute paths, serialised through comlock).

    python -m scripts.docs.render_deck_final "<abs path to deck.pptx>" "<abs output dir>"
"""
import os
import sys
import time

import win32com.client

from .comlock import com_lock


def render(pptx, outdir, width=1280):
    pptx, outdir = os.path.abspath(pptx), os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    for attempt in range(3):
        try:
            with com_lock():
                app = win32com.client.DispatchEx("PowerPoint.Application")
                pres = app.Presentations.Open(pptx, True, False, False)
                n = pres.Slides.Count
                for i in range(1, n + 1):
                    pres.Slides(i).Export(os.path.join(outdir, f"s{i:02d}.png"), "PNG", width, int(width * 9 / 16))
                pres.Close()
                app.Quit()
            return n
        except Exception as e:  # noqa: BLE001
            print("render retry:", e)
            time.sleep(8)
    raise RuntimeError("render failed")


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]), "slides")
