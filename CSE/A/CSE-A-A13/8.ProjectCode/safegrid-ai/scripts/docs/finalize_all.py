"""Updates fields (TOC, lists, page numbers) in the chapter documents and the report through Word COM; PDF of the report for page counting."""
import glob
import os
import sys
import time

from . import facts as F
from .render_deck import ComLock
from .word_finalize import finalize

NAMES = ["9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx", "10.SCOPE & LIMITATIONS.docx", "11. BLOCK DIAGRAMS ALL.docx", "12.DESIGN &IMPLEMENTATION.docx",
         "14.RESULTS.docx", "15.CONCLUSION&FUTURE SCOPE&REFERENCES.docx", "17.Final Document.docx"]

if __name__ == "__main__":
    only = sys.argv[1:] or NAMES
    for n in only:
        p = os.path.join(F.BATCH, n)
        pdf = os.path.join(F.DOCS, "_pdf", os.path.splitext(n)[0] + ".pdf")
        os.makedirs(os.path.dirname(pdf), exist_ok=True)
        for attempt in range(4):
            try:
                with ComLock():
                    pages, words = finalize(p, pdf)
                print(f"{n}: {pages} pages, {words} words")
                break
            except Exception as e:  # Word COM is flaky right after another COM user
                print("retry", n, type(e).__name__, str(e)[:80])
                time.sleep(12)
