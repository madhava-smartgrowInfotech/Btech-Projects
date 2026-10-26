"""Render a deck to PNGs with PowerPoint COM (serialised through comlock). Usage: python -m scripts.docs.final_render <abs deck.pptx> <abs out dir>"""
import os
import sys
import time

import win32com.client

from .comlock import com_lock


def render(deck, out_dir):
    deck, out_dir = os.path.abspath(deck), os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(out_dir, f))
    with com_lock():
        last = None
        for _ in range(4):
            app = None
            try:
                app = win32com.client.DispatchEx("PowerPoint.Application")
                pres = app.Presentations.Open(deck, True, False, False)
                pres.SaveAs(out_dir, 18)   # ppSaveAsPNG
                n = pres.Slides.Count
                pres.Close()
                return n
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(6)
            finally:
                if app is not None:
                    try:
                        app.Quit()
                    except Exception:  # noqa: BLE001
                        pass
        raise last


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]))
