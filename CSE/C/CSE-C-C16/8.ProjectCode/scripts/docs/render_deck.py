"""Render every slide of a deck to PNG with PowerPoint COM (under the shared COM lock): python -m scripts.docs.render_deck <abs deck path> <out dir>"""
import os
import sys
import time

from .comlock import com_lock


def render(deck, out_dir, retries=4):
    import win32com.client

    os.makedirs(out_dir, exist_ok=True)
    deck = os.path.abspath(deck)
    last = None
    with com_lock():
        for _ in range(retries):
            app = None
            try:
                app = win32com.client.DispatchEx("PowerPoint.Application")
                pres = app.Presentations.Open(deck, True, False, False)
                n = pres.Slides.Count
                for i in range(1, n + 1):
                    pres.Slides(i).Export(os.path.join(out_dir, f"s{i:02d}.png"), "PNG", 1280, 720)
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
    print(render(sys.argv[1], sys.argv[2]), "slides rendered")
