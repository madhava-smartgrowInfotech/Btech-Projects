"""Render PDF pages to PNG (PyMuPDF), cached under data/pages/<document id>/."""

from __future__ import annotations

import threading
from pathlib import Path

import pymupdf

from app.core.config import get_settings

_lock = threading.Lock()


def render_page(pdf_path: Path, document_id: int, page_number: int, scale: float = 1.5) -> Path:
    scale = min(3.0, max(0.5, round(scale * 4) / 4))
    folder = get_settings().pages_dir / str(document_id)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"p{page_number}@{scale:g}.png"
    if out.exists():
        return out
    with _lock:
        if out.exists():
            return out
        with pymupdf.open(str(pdf_path)) as doc:
            if not 1 <= page_number <= doc.page_count:
                raise IndexError(page_number)
            pix = doc[page_number - 1].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
            tmp = out.with_suffix(".tmp")
            pix.save(str(tmp), output="png")
            tmp.replace(out)
    return out


def clear_pages(document_id: int) -> None:
    folder = get_settings().pages_dir / str(document_id)
    if folder.exists():
        for f in folder.glob("*"):
            f.unlink(missing_ok=True)
        folder.rmdir()
