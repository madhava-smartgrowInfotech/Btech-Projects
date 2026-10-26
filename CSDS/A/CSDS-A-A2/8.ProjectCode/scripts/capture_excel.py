"""Download the real Excel export of the live demo session and render each sheet to PNG with Excel + PyMuPDF.
    python scripts\capture_excel.py        (API on :8102, after capture_screenshots.py)"""
from pathlib import Path
import sys, httpx, fitz, win32com.client as w32

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
API = "http://127.0.0.1:8102"
tmp = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "_tmp"
tmp.mkdir(parents=True, exist_ok=True)
h = {"X-Device-Id": "xl", "User-Agent": "xl"}
tok = httpx.post(API + "/api/auth/login", headers=h, json={"username": "faculty@college.edu", "password": "faculty123", "role": "faculty"}).json()["token"]
h["Authorization"] = f"Bearer {tok}"
sessions = httpx.get(API + "/api/sessions", headers=h).json()
sid = [s for s in sessions if s["course_code"] == "CS604"][0]["id"]
xlsx = tmp / "attendance_CS604.xlsx"
xlsx.write_bytes(httpx.get(f"{API}/api/sessions/{sid}/export", headers=h).content)
xl = w32.Dispatch("Excel.Application"); xl.Visible = False; xl.DisplayAlerts = False
wb = xl.Workbooks.Open(str(xlsx))
pdf = tmp / "x.pdf"
for ws in wb.Worksheets:
    ws.PageSetup.Orientation = 2; ws.PageSetup.Zoom = False; ws.PageSetup.FitToPagesWide = 1; ws.PageSetup.FitToPagesTall = 1
wb.ExportAsFixedFormat(0, str(pdf))
wb.Close(False); xl.Quit()
doc = fitz.open(pdf)
for i, name in enumerate(["32_excel_summary", "33_excel_attendance", "34_excel_verification_log"]):
    if i < len(doc):
        pix = doc[i].get_pixmap(dpi=130, clip=doc[i].get_text("dict")["bbox"] if False else None)
        pix.save(SHOTS / f"{name}.png"); print("shot", name)

from PIL import Image, ImageChops
for n in ["32_excel_summary", "33_excel_attendance", "34_excel_verification_log"]:
    f = SHOTS / f"{n}.png"
    im = Image.open(f).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    im.crop((max(0, bb[0] - 20), max(0, bb[1] - 20), min(im.width, bb[2] + 20), min(im.height, bb[3] + 20))).save(f)
