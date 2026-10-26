"""Render one content module's blocks into a throw-away .docx and report word count / missing images / (optionally) report pages.

    python -m scripts.docs.preview ch1                  # from 8.ProjectCode; module exposes blocks()
    python -m scripts.docs.preview ch9_10 conclusion_blocks
    python -m scripts.docs.preview ch5 blocks --report  # compact report variant (F.REPORT=True) in the report layout; prints the real Word page count
"""
import importlib
import os
import sys
import tempfile
import time

from . import facts as F


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    report = "--report" in sys.argv
    F.REPORT = report
    from .blocks import plain_text, render
    from .kit import Doc

    mod = importlib.import_module(f"scripts.docs.{args[0]}")
    fn = getattr(mod, args[1] if len(args) > 1 else "blocks")
    blocks = fn()
    txt = plain_text(blocks)
    d = Doc("preview", report=report)
    render(d, blocks, h1_page_break=not report)
    out = os.path.join(tempfile.gettempdir(), f"preview_{args[0]}{'_report' if report else ''}.docx")
    d.save(out)
    words = len(txt.split())
    bad = [w for w in ("None", "[pending]", "{", "}", "nan") if w in txt]
    msg = f"{args[0]}: {words} words, {d.fig_no} figures, {d.tab_no} tables -> {out}"
    if report:
        import win32com.client

        from .comlock import com_lock

        for attempt in range(3):
            try:
                with com_lock():
                    w = win32com.client.DispatchEx("Word.Application")
                    w.Visible = False
                    w.DisplayAlerts = 0
                    doc = w.Documents.Open(os.path.abspath(out), ReadOnly=True, AddToRecentFiles=False)
                    doc.Repaginate()
                    pages = doc.ComputeStatistics(2)
                    doc.Close(False)
                    w.Quit()
                msg += f"  | REPORT PAGES: {pages}"
                break
            except Exception as e:  # noqa: BLE001
                time.sleep(8)
    print(msg)
    if bad:
        print("WARNING suspicious tokens in text:", bad)


if __name__ == "__main__":
    main()
