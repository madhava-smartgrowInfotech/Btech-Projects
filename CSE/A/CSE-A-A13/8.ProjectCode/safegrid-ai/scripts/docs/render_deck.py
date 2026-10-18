"""
Renders a .pptx to PNG slides with PowerPoint (COM). A lock file serialises COM use across parallel sessions.

    python -m scripts.docs.render_deck "<deck.pptx>" "<out_dir>" [--width 1280]

Prints the PNG paths. Run from 8.ProjectCode/safegrid-ai.
"""

import argparse
import os
import time

LOCK = os.path.join(os.environ.get("TEMP", "."), "safegrid_office_com.lock")


class ComLock:
    def __enter__(self):
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                if time.time() - os.path.getmtime(LOCK) > 600:  # stale lock
                    try:
                        os.remove(LOCK)
                    except OSError:
                        pass
                if time.time() - t0 > 900:
                    raise TimeoutError("office COM lock busy")
                time.sleep(2)

    def __exit__(self, *a):
        os.close(self.fd)
        try:
            os.remove(LOCK)
        except OSError:
            pass


def render(deck, out_dir, width=1280):
    import win32com.client

    deck = os.path.abspath(deck)
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    with ComLock():
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            pres = app.Presentations.Open(deck, ReadOnly=True, Untitled=False, WithWindow=False)
            n = pres.Slides.Count
            h = int(width * pres.PageSetup.SlideHeight / pres.PageSetup.SlideWidth)
            paths = []
            for i in range(1, n + 1):
                p = os.path.join(out_dir, f"slide_{i:02d}.png")
                pres.Slides(i).Export(p, "PNG", width, h)
                paths.append(p)
            pres.Close()
            return paths
        finally:
            app.Quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("out_dir")
    ap.add_argument("--width", type=int, default=1280)
    a = ap.parse_args()
    for p in render(a.deck, a.out_dir, a.width):
        print(p)
