"""Export a docx to PDF through Word (ComLock). python -m scripts.docs.pdf_export <docx> <pdf>"""
import os, sys
from .comlock import ComLock
import win32com.client

def export(docx, pdf):
    with ComLock():
        w = win32com.client.DispatchEx("Word.Application"); w.Visible = False; w.DisplayAlerts = 0
        try:
            d = w.Documents.Open(os.path.abspath(docx), ReadOnly=True)
            d.ExportAsFixedFormat(os.path.abspath(pdf), 17)
            d.Close(False)
        finally:
            w.Quit()

if __name__ == "__main__":
    export(sys.argv[1], sys.argv[2])
