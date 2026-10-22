"""Print the page on which each level-1 heading of a .docx starts (Word COM, read-only)."""
import sys

import win32com.client

w = win32com.client.DispatchEx("Word.Application")
w.Visible = False
w.DisplayAlerts = 0
try:
    d = w.Documents.Open(sys.argv[1], ReadOnly=True)
    for p in d.Paragraphs:
        if p.OutlineLevel == 1 and p.Range.Text.strip():
            print(p.Range.Information(3), p.Range.Text.strip()[:60])
    print("pages", d.ComputeStatistics(2), "images", d.InlineShapes.Count)
    d.Close(False)
finally:
    w.Quit()
