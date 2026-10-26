"""Open 19.IEEE_Paper.docx in Word, repaginate, report the page and word counts and export 19.IEEE_Paper.pdf (batch root)."""
from __future__ import annotations

import sys
from pathlib import Path

import win32com.client as win32

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_common import BATCH  # noqa: E402


def main():
    path = BATCH / "19.IEEE_Paper.docx"
    word = win32.DispatchEx("Word.Application")  # own instance: other builders may be using Word
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(path), ReadOnly=False)
        doc.Repaginate()
        pages = doc.ComputeStatistics(2)
        words = doc.ComputeStatistics(0)
        # how full is the last page? vertical position (points from the top of the page) of the end of the document
        end = doc.Content
        end.Collapse(0)
        last_y = end.Information(6)  # wdVerticalPositionRelativeToPage
        doc.ExportAsFixedFormat(str(BATCH / "19.IEEE_Paper.pdf"), 17)
        doc.Close(False)
        print(f"{pages} pages, {words} words, last text at {last_y / 72:.2f} in from the top of the last page (page body ends at 10.0 in)")
    finally:
        word.Quit()


if __name__ == "__main__":
    main()
