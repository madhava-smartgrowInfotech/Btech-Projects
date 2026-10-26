"""Render a deck to PNGs with PowerPoint COM (serialised through comlock). Usage: python -m scripts.docs.review2_render <abs deck.pptx> <abs out dir>"""
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
            pres.SaveAs(out_dir, 18)   # ppSaveAsPNG
            n = pres.Slides.Count
            pres.Close()
        finally:
            app.Quit()
    return n


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]))
