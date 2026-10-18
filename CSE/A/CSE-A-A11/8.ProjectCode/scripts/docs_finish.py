"""Open each generated .docx in Word, update its fields (table of contents, lists of figures and tables), save, and report pages.

    python scripts/docs_finish.py [pdf_dir] [numbers...]      e.g.  python scripts/docs_finish.py out 14 17

Needs Microsoft Word (COM). With pdf_dir, each document is also exported to PDF there (used for visual checks).
Word's automation is flaky after a kill ('Call was rejected by callee'): every document is retried with a fresh Word instance.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import win32com.client as win32

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docs_build import NAMES  # noqa: E402
from doc_common import BATCH  # noqa: E402


def kill_word():
    subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], capture_output=True)
    time.sleep(12)


def finish_one(path: Path, pdf_dir: Path | None):
    word = win32.Dispatch("Word.Application")
    try:
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(str(path), ReadOnly=False)
        for sty in ("TOC 1", "TOC 2"):
            try:
                pf = doc.Styles(sty).ParagraphFormat
                pf.LineSpacingRule = 0
                pf.SpaceAfter = 2
                pf.SpaceBefore = 0
            except Exception:
                pass
        doc.Repaginate()
        for toc in doc.TablesOfContents:
            toc.Update()
        for tof in doc.TablesOfFigures:
            tof.Update()
        doc.Fields.Update()
        for toc in doc.TablesOfContents:
            toc.Update()
        doc.Repaginate()
        pages = doc.ComputeStatistics(2)
        words = doc.ComputeStatistics(0)
        doc.Save()
        if pdf_dir:
            doc.ExportAsFixedFormat(str(pdf_dir / (path.stem + ".pdf")), 17)
        doc.Close(False)
        return pages, words
    finally:
        try:
            word.Quit()
        except Exception:
            pass


def main():
    args = [a for a in sys.argv[1:]]
    pdf_dir = None
    if args and not args[0].isdigit():
        pdf_dir = Path(args.pop(0))
        pdf_dir.mkdir(parents=True, exist_ok=True)
    only = {int(a) for a in args}
    kill_word()
    for num, name in NAMES.items():
        if only and num not in only:
            continue
        path = BATCH / name
        if not path.exists():
            continue
        for attempt in range(1, 6):
            try:
                pages, words = finish_one(path, pdf_dir)
                print(f"{name}: {pages} pages, {words} words, {path.stat().st_size // 1024} KB", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"  retry {attempt} for {name}: {str(e)[:70]}", flush=True)
                kill_word()
        else:
            print(f"FAILED: {name}")


if __name__ == "__main__":
    main()
