"""
Render a .pptx to PNG slides with PowerPoint COM (serialised with a lock file so only one Office job runs at a time).

    python -m scripts.docs.render_deck "<deck.pptx>" "<out_dir>"

Also provides audit_package(path): searches every XML part, relationship target and embedded workbook of a pptx for
words that belong to the institution templates' old subject matter.
"""
import os
import sys
import time
import zipfile

FORBIDDEN = ["Hidden Risk", "Social Media", "social media", "Fakeddit", "PHEME", "Snopes", "MCNN", "manipulation", "Manipulation",
             "bank transaction", "fraud", "Fraud", "pneumonia", "Pneumonia", "X-ray", "Grad-CAM", "CLAHE", "PneumoDetect"]

LOCK = os.path.join(os.environ.get("TEMP", "."), "office_com.lock")


class ComLock:
    def __enter__(self):
        for _ in range(600):
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(LOCK) > 900:
                        os.remove(LOCK)
                except OSError:
                    pass
                time.sleep(1)
        raise TimeoutError("could not take the Office COM lock")

    def __exit__(self, *a):
        os.close(self.fd)
        try:
            os.remove(LOCK)
        except OSError:
            pass


def render(path, out_dir):
    import win32com.client

    path, out_dir = os.path.abspath(path), os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    with ComLock():
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            pres = app.Presentations.Open(path, True, False, False)
            pres.SaveAs(out_dir, 18)  # ppSaveAsPNG
            n = pres.Slides.Count
            pres.Close()
        finally:
            app.Quit()
    return n


def audit_package(path, words=None):
    """Return {part_name: [words]} for every part of the package that contains a forbidden word."""
    words = words or FORBIDDEN
    hits = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            data = z.read(name)
            if name.endswith((".xlsx", ".xlsm")):
                import io

                with zipfile.ZipFile(io.BytesIO(data)) as zz:
                    data = b"".join(zz.read(n) for n in zz.namelist())
            try:
                text = data.decode("utf-8", "ignore")
            except Exception:
                continue
            found = sorted({w for w in words if w in text})
            if found:
                hits[name] = found
        parts = [n for n in z.namelist() if n.startswith(("ppt/charts/", "ppt/embeddings/")) and not n.endswith("/")]
    return hits, parts


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2]), "slides rendered")


def contact_sheets(src_dir, per=4, width=1500):
    """Combine Slide<N>.PNG files into 2x2 sheets (sheet_1.png ...). Returns the sheet paths."""
    import re

    from PIL import Image

    files = sorted((f for f in os.listdir(src_dir) if re.match(r"Slide\d+\.PNG", f, re.I)), key=lambda f: int(re.findall(r"\d+", f)[0]))
    out = []
    for k in range(0, len(files), per):
        ims = [Image.open(os.path.join(src_dir, f)).convert("RGB") for f in files[k:k + per]]
        w = width // 2
        h = int(w * ims[0].height / ims[0].width)
        sheet = Image.new("RGB", (w * 2 + 6, h * 2 + 6), "white")
        for i, im in enumerate(ims):
            sheet.paste(im.resize((w, h)), ((i % 2) * (w + 6), (i // 2) * (h + 6)))
        p = os.path.join(src_dir, f"sheet_{k // per + 1}.png")
        sheet.save(p)
        out.append(p)
    return out
