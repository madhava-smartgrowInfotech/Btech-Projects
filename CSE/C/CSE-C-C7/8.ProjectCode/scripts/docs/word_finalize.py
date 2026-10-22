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
        for i in range(1, doc.TablesOfContents.Count + 1):
            doc.TablesOfContents(i).Update()
        for i in range(1, doc.TablesOfFigures.Count + 1):
            doc.TablesOfFigures(i).Update()
        doc.Fields.Update()
        pages = doc.ComputeStatistics(2)  # wdStatisticPages
        words = doc.ComputeStatistics(0)
        doc.Save()
        if pdf:
            doc.ExportAsFixedFormat(os.path.abspath(pdf), 17)  # wdExportFormatPDF
        doc.Close(False)
        return pages, words
    except Exception as e:  # noqa: BLE001
        print('Word error:', repr(e)[:400])
        raise
    finally:
        try:
            word.Quit()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--pdf")
    a = ap.parse_args()
    p, w = finalize(a.path, a.pdf)
    print(f"{os.path.basename(a.path)}: {p} pages, {w} words")
