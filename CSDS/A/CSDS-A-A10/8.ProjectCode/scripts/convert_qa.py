from __future__ import annotations

from pathlib import Path

import pythoncom
import win32com.client
from pypdf import PdfReader


BATCH = Path(__file__).resolve().parents[2]
QA = BATCH / "8.ProjectCode" / "docs" / "qa"
QA.mkdir(parents=True, exist_ok=True)

DOCS = [
    "9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx",
    "10.SCOPE & LIMITATIONS.docx",
    "11. BLOCK DIAGRAMS ALL.docx",
    "12.DESIGN &IMPLEMENTATION.docx",
    "14.RESULTS.docx",
    "15.CONCLUSION&FUTURE SCOPE&REFERENCES.docx",
    "17.Final Document.docx",
    "19.IEEE_Paper.docx",
]
DECKS = ["7.Review_1_PPT.pptx", "13.Review_2_PPT.pptx", "16.Final_PPT.pptx"]


def convert_word():
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for name in DOCS:
            src = (BATCH / name).resolve()
            pdf = (BATCH / "19.IEEE_Paper.pdf").resolve() if name.startswith("19.") else (QA / (src.stem + ".pdf")).resolve()
            doc = word.Documents.Open(str(src), ReadOnly=False, AddToRecentFiles=False)
            try:
                doc.Fields.Update()
                for toc in doc.TablesOfContents:
                    toc.Update()
                doc.Repaginate()
                doc.Save()
                doc.ExportAsFixedFormat(str(pdf), 17, OpenAfterExport=False, OptimizeFor=0)
            finally:
                doc.Close(SaveChanges=False)
            print(f"WORD {name}: {len(PdfReader(str(pdf)).pages)} pages -> {pdf}")
    finally:
        word.Quit()
        pythoncom.CoUninitialize()


def convert_powerpoint():
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        for name in DECKS:
            src = (BATCH / name).resolve()
            pdf = (QA / (src.stem + ".pdf")).resolve()
            deck = app.Presentations.Open(str(src), WithWindow=False)
            try:
                deck.SaveAs(str(pdf), 32)
            finally:
                deck.Close()
            print(f"PPT {name}: {len(PdfReader(str(pdf)).pages)} slides -> {pdf}")
    finally:
        app.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    convert_word()
    convert_powerpoint()
