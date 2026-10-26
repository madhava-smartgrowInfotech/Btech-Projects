"""Render a deck to PNGs with PowerPoint COM (serialised by comlock). Usage: python -m scripts.docs.review1_render <abs deck.pptx> <abs out dir>"""
import os
import sys

import win32com.client

from .comlock import com_lock


def render(deck, out_dir):
    deck, out_dir = os.path.abspath(deck), os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(out_dir, f))
    with com_lock():
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            pres = app.Presentations.Open(deck, True, False, False)
            n = pres.Slides.Count
            for i in range(1, n + 1):
                pres.Slides(i).Export(os.path.join(out_dir, f"slide{i:02d}.png"), "PNG", 1600, 900)
            pres.Close()
        finally:
            app.Quit()
    return n


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]))
