"""Export every slide of the three decks to PNG (PowerPoint COM) for visual checks: python scripts/render_decks.py <out_dir>"""
import sys
from pathlib import Path
import win32com.client as win32
BATCH = Path(__file__).resolve().parents[2]
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
app = win32.Dispatch("PowerPoint.Application")
try:
    for name in ["7.Review_1_PPT", "13.Review_2_PPT", "16.Final_PPT"]:
        pres = app.Presentations.Open(str(BATCH / f"{name}.pptx"), WithWindow=False)
        d = out / name; d.mkdir(exist_ok=True)
        for i, s in enumerate(pres.Slides, 1):
            s.Export(str(d / f"{i:02d}.png"), "PNG", 960, 540)
        pres.Close()
        print(name, "exported")
finally:
    app.Quit()
