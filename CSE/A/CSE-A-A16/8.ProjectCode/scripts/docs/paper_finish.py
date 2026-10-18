"""Exports 19.IEEE_Paper.docx to PDF with Word (COM), prints the page count and renders the pages to PNG for a visual check.

    python -m scripts.docs.paper_finish [--png-dir DIR]
"""

import argparse
import os
import time

from . import facts as F


def export(docx, pdf, retries=4):
    import win32com.client

    last = None
    for i in range(retries):
        word = None
        try:
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            doc = word.Documents.Open(os.path.abspath(docx), ReadOnly=True, AddToRecentFiles=False)
            doc.Repaginate()
            pages = doc.ComputeStatistics(2)
            words = doc.ComputeStatistics(0)
            doc.ExportAsFixedFormat(os.path.abspath(pdf), 17)
            doc.Close(False)
            return pages, words
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(8)
        finally:
            if word is not None:
                try:
                    word.Quit()
                except Exception:  # noqa: BLE001
                    pass
    raise last


def render(pdf, out_dir):
    import pymupdf

    os.makedirs(out_dir, exist_ok=True)
    d = pymupdf.open(pdf)
    paths = []
    for i, pg in enumerate(d, 1):
        p = os.path.join(out_dir, f"paper_p{i}.png")
        pg.get_pixmap(dpi=90).save(p)
        paths.append(p)
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", default=None)
    a = ap.parse_args()
    docx = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    pdf = os.path.join(F.BATCH, "19.IEEE_Paper.pdf")
    pages, words = export(docx, pdf)
    print("Word pages:", pages, "words:", words)
    import pymupdf

    d = pymupdf.open(pdf)
    print("PDF pages:", len(d))
    last = d[len(d) - 1].get_text("blocks")
    print("last page text blocks:", len(last))
    if a.png_dir:
        print(render(pdf, a.png_dir))
