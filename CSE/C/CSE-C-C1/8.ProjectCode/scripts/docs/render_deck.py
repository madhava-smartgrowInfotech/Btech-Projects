"""Render a deck to PNGs with PowerPoint COM (under the shared COM lock) so every slide can be looked at.

    python -m scripts.docs.render_deck "<deck.pptx>" "<out_dir>"      # slide PNGs 1280 wide
"""
import os
import sys
import time

from .comlock import com_lock


def render(pptx, out_dir, width=1280, retries=4):
    import win32com.client

    pptx, out_dir = os.path.abspath(pptx), os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(out_dir, f))
    last = None
    for _ in range(retries):
        try:
            with com_lock():
                app = win32com.client.DispatchEx("PowerPoint.Application")
                try:
                    pres = app.Presentations.Open(pptx, True, False, False)
                    n = pres.Slides.Count
                    for i in range(1, n + 1):
                        pres.Slides(i).Export(os.path.join(out_dir, f"slide_{i:02d}.png"), "PNG", width, int(width * 9 / 16))
                    pres.Close()
                finally:
                    app.Quit()
            return n
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(8)
    raise RuntimeError(f"render failed: {last}")


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]), "slides rendered")
