"""
Opens a .docx in Word (COM), updates every field (table of contents, list of figures and tables, page numbers),
saves it and optionally exports a PDF.

    python -m scripts.docs.word_finalize "<file.docx>" [--pdf <out.pdf>]
"""

import argparse
import os
import sys
import time

import win32com.client


def finalize(path, pdf=None, visible=False):
    path = os.path.abspath(path)
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = visible
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(path, ReadOnly=False, AddToRecentFiles=False)
        for sid, size in ((-20, 10.5), (-21, 10.5), (-36, 10.5)):    # TOC 1, TOC 2, Table of Figures: compact single spacing
            try:
                st = doc.Styles(sid)
                st.Font.Size = size
                st.ParagraphFormat.SpaceAfter = 0
                st.ParagraphFormat.SpaceBefore = 0
                st.ParagraphFormat.LineSpacingRule = 0
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
        for tof in doc.TablesOfFigures:
            tof.Update()
        doc.Repaginate()
        pages = doc.ComputeStatistics(2)  # wdStatisticPages
        words = doc.ComputeStatistics(0)
        doc.Save()
        if pdf:
            doc.ExportAsFixedFormat(os.path.abspath(pdf), 17)  # wdExportFormatPDF
        doc.Close(False)
        return pages, words
    finally:
        word.Quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--pdf")
    a = ap.parse_args()
    p, w = finalize(a.path, a.pdf)
    print(f"{os.path.basename(a.path)}: {p} pages, {w} words")
