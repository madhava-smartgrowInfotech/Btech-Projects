"""Open each generated .docx in Word, update its fields (table of contents, lists of figures and tables), save, and report pages.

    python scripts/docs_finish.py [pdf_dir]

Needs Microsoft Word (COM). With pdf_dir, each document is also exported to PDF there (used for visual checks).
"""
from __future__ import annotations

import sys
from pathlib import Path

import time

import pythoncom
import win32com.client as win32
from pywintypes import com_error

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docs_build import NAMES  # noqa: E402
from doc_common import BATCH  # noqa: E402


def retry(fn, *a, tries=30, **kw):
    for i in range(tries):
        try:
            return fn(*a, **kw)
        except com_error as e:
            if i == tries - 1:
                raise
            time.sleep(2)


def main():
    pdf_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if pdf_dir:
        pdf_dir.mkdir(parents=True, exist_ok=True)
    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for num, name in NAMES.items():
            path = BATCH / name
            if not path.exists():
                continue
            doc = retry(lambda: word.Documents.Open(str(path), ReadOnly=False))
            for sty in ('TOC 1', 'TOC 2', 'Table of Figures'):
                try:
                    pf = doc.Styles(sty).ParagraphFormat
                    pf.LineSpacingRule = 0
                    pf.SpaceAfter = 1
                    pf.SpaceBefore = 0
                    doc.Styles(sty).Font.Size = 11
                except Exception:
                    pass
            retry(lambda: doc.Repaginate())
            for toc in doc.TablesOfContents:
                retry(lambda: toc.Update())
            for tof in doc.TablesOfFigures:
                retry(lambda: tof.Update())
            retry(lambda: doc.Fields.Update())
            for toc in doc.TablesOfContents:
                retry(lambda: toc.Update())
            retry(lambda: doc.Repaginate())
            pages = retry(lambda: doc.ComputeStatistics(2))
            words = retry(lambda: doc.ComputeStatistics(0))
            retry(lambda: doc.Save())
            if pdf_dir:
                retry(lambda: doc.ExportAsFixedFormat(str(pdf_dir / (path.stem + ".pdf")), 17))
            retry(lambda: doc.Close(False))
            print(f"{name}: {pages} pages, {words} words, {path.stat().st_size // 1024} KB")
    finally:
        try:
            word.Quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
