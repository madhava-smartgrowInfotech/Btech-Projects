from __future__ import annotations

import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


BATCH = Path(__file__).resolve().parents[2]
QA = BATCH / "8.ProjectCode" / "docs" / "qa"
OUT = QA / "rendered"
OUT.mkdir(parents=True, exist_ok=True)

PDFS = [
    QA / "9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.pdf",
    QA / "10.SCOPE & LIMITATIONS.pdf",
    QA / "11. BLOCK DIAGRAMS ALL.pdf",
    QA / "12.DESIGN &IMPLEMENTATION.pdf",
    QA / "14.RESULTS.pdf",
    QA / "15.CONCLUSION&FUTURE SCOPE&REFERENCES.pdf",
    QA / "17.Final Document.pdf",
    BATCH / "19.IEEE_Paper.pdf",
    QA / "7.Review_1_PPT.pdf",
    QA / "13.Review_2_PPT.pdf",
    QA / "16.Final_PPT.pdf",
]


def safe_name(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem)


def selected_pages(path: Path, count: int) -> list[int]:
    if "PPT" in path.name or path.name == "19.IEEE_Paper.pdf":
        return list(range(1, count + 1))
    if path.name.startswith("17."):
        return sorted({1, 2, 3, 5, 9, 10, 20, 35, 50, 65, 80, 90, count})
    return sorted({1, 2, max(1, count // 2), count})


def render_pdf(path: Path) -> Path:
    page_count = len(PdfReader(str(path)).pages)
    pages = selected_pages(path, page_count)
    folder = OUT / safe_name(path)
    folder.mkdir(parents=True, exist_ok=True)
    rendered: list[tuple[int, Path]] = []
    for page in pages:
        prefix = folder / f"page_{page:03d}"
        subprocess.run(
            ["pdftoppm", "-f", str(page), "-l", str(page), "-r", "90", "-png", "-singlefile", str(path), str(prefix)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        rendered.append((page, prefix.with_suffix(".png")))

    thumb_w, thumb_h = 320, 230
    label_h, gap, columns = 28, 16, 4
    rows = (len(rendered) + columns - 1) // columns
    sheet = Image.new("RGB", (gap + columns * (thumb_w + gap), gap + rows * (thumb_h + label_h + gap)), "#e8edf3")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for idx, (page, image_path) in enumerate(rendered):
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        col, row = idx % columns, idx // columns
        x = gap + col * (thumb_w + gap) + (thumb_w - image.width) // 2
        y = gap + row * (thumb_h + label_h + gap)
        sheet.paste(image, (x, y))
        draw.text((gap + col * (thumb_w + gap), y + thumb_h + 6), f"Page {page} of {page_count}", fill="#111827", font=font)
    contact = OUT / f"CONTACT_{safe_name(path)}.png"
    sheet.save(contact)
    print(f"{path.name}: {page_count} pages, rendered {len(rendered)} -> {contact}")
    return contact


if __name__ == "__main__":
    for pdf in PDFS:
        render_pdf(pdf)
