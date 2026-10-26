"""Render a .pptx to PNG slides with PowerPoint COM (serialised with ComLock).

    python -m scripts.docs.render_final <deck.pptx> <out_dir>
"""

import os
import shutil
import sys
import time

import win32com.client

from .comlock import ComLock


def render(pptx, out_dir, retries=4):
    pptx = os.path.abspath(pptx)
    out_dir = os.path.abspath(out_dir)
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    last = None
    for attempt in range(retries):
        try:
            with ComLock():
                app = win32com.client.DispatchEx("PowerPoint.Application")
                try:
                    pres = app.Presentations.Open(pptx, True, False, False)
                    pres.SaveAs(out_dir, 18)  # ppSaveAsPNG
                    n = pres.Slides.Count
                    pres.Close()
                finally:
                    app.Quit()
            return n
        except Exception as e:  # "Server execution failed" and friends
            last = e
            time.sleep(3)
    raise last


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]), "slides rendered")
