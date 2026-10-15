"""Microsoft Word automation (pywin32) plus PDF-based page lookup (PyMuPDF).

Word is used only to export a PDF / count pages (few COM calls, with retries because other processes may also be using Word);
page numbers of headings and captions are then found in the PDF text, which is fast and does not depend on a long COM session.
"""
import os
import re
import time

import pythoncom
import win32com.client


def _start_word():
    pythoncom.CoInitialize()
    for attempt in range(10):
        try:
            app = win32com.client.DispatchEx("Word.Application")
            app.Visible = False
            app.DisplayAlerts = 0
            return app
        except Exception:  # noqa: BLE001  Word may be busy starting for another process
            time.sleep(4)
    raise RuntimeError("could not start Word")


def export_pdf(path, pdf_path, tries=4):
    """Open a .docx in Word, export a PDF, return the page count."""
    last = None
    for _ in range(tries):
        app = None
        try:
            app = _start_word()
            doc = app.Documents.Open(os.path.abspath(path), ReadOnly=True, AddToRecentFiles=False, ConfirmConversions=False)
            doc.Repaginate()
            doc.ExportAsFixedFormat(os.path.abspath(pdf_path), 17)  # wdExportFormatPDF
            pages = doc.ComputeStatistics(2)
            doc.Close(False)
            return pages
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5)
        finally:
            try:
                if app is not None:
                    app.Quit()
            except Exception:  # noqa: BLE001
                pass
    raise RuntimeError(f"Word export failed: {last}")


def page_count(path):
    pdf = os.path.join(os.environ.get("TEMP", "."), "_pagecount.pdf")
    return export_pdf(path, pdf)


def _norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def locate_pages(pdf_path, heads, figs, tabs, body_marker="CHAPTER 1: INTRODUCTION"):
    """Find the (adjusted, body-relative) page of every heading and caption by reading the PDF text.

    heads: list of heading texts in document order; figs / tabs: caption texts ('Figure 5.1: ...') in order.
    Returns (pages dict {('h',i): n, ('f',i): n, ('t',i): n}, body_start_index, total_pdf_pages)."""
    import fitz
    d = fitz.open(pdf_path)
    lines = [[_norm(l) for l in d[i].get_text().splitlines() if l.strip()] for i in range(len(d))]
    marker = _norm(body_marker)
    body_start = max(i for i, ls in enumerate(lines) if any(l == marker for l in ls))
    pages = {}

    def find(texts, kind):
        ptr = body_start
        for i, t in enumerate(texts):
            key = _norm(t)[:38]
            for pg in range(ptr, len(d)):
                ls = lines[pg]
                if any(l.startswith(key) or (j + 1 < len(ls) and (l + " " + ls[j + 1]).startswith(key)) for j, l in enumerate(ls)):
                    pages[(kind, i)] = str(pg - body_start + 1)
                    ptr = pg
                    break
            else:
                pages[(kind, i)] = "?"
    find(heads, "h")
    find(figs, "f")
    find(tabs, "t")
    return pages, body_start, len(d)
