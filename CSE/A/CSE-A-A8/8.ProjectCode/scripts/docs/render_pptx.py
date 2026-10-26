"""
Render a .pptx to one PNG per slide with PowerPoint COM (serialised with ComLock).

    python -m scripts.docs.render_pptx "<deck.pptx>" "<out_dir>"
"""

import os
import sys
import time

import win32com.client

from .comlock import ComLock


def render(path, out_dir, retries=3):
    path = os.path.abspath(path)
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(out_dir, f))
    last = None
    for attempt in range(retries):
        with ComLock():
            app = None
            try:
                app = win32com.client.DispatchEx("PowerPoint.Application")
                pres = app.Presentations.Open(path, True, False, False)
                n = pres.Slides.Count
                pres.SaveAs(out_dir, 18)  # ppSaveAsPNG
                pres.Close()
                return n
            except Exception as exc:  # COM "Server execution failed" etc.
                last = exc
            finally:
                try:
                    if app is not None:
                        app.Quit()
                except Exception:
                    pass
        time.sleep(5)
    raise last


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]), "slides rendered")
