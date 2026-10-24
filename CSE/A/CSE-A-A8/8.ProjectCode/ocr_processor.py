"""
ocr_processor.py
-----------------
Handles text extraction from uploaded lab reports.

- PDFs: text-layer extraction via PyMuPDF (fitz). Falls back to
  rendering each page to an image and running OCR if the PDF has
  no embedded text layer (i.e. it's a scanned PDF).
- Images (JPG/JPEG/PNG): preprocessed with OpenCV (grayscale,
  denoising, thresholding, deskew) then OCR'd with Tesseract via
  pytesseract.

All functions raise OCRError on failure so the calling code
(report_processor.py / app.py) can show a clean Streamlit error
message instead of a raw traceback.
"""

import io
import os

import numpy as np
import cv2
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - handled gracefully at runtime
    fitz = None

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None


class OCRError(Exception):
    """Raised when text could not be extracted from a document."""
    pass


SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# Minimum number of characters we consider a PDF "has a real text layer".
MIN_TEXT_LAYER_CHARS = 30


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_file(filename: str, file_bytes: bytes, max_size_mb: int = 15):
    """Raise OCRError if the file is not a supported / sane upload."""
    ext = get_file_extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        raise OCRError(
            f"Unsupported file format '{ext}'. Please upload a PDF, JPG, JPEG or PNG file."
        )
    if not file_bytes or len(file_bytes) == 0:
        raise OCRError("The uploaded file is empty.")
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise OCRError(f"File is too large ({size_mb:.1f} MB). Maximum allowed is {max_size_mb} MB.")
    return ext


# ---------------------------------------------------------------------------
# Image preprocessing (OpenCV)
# ---------------------------------------------------------------------------

def preprocess_image_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Apply a standard OpenCV preprocessing pipeline to improve OCR accuracy:
    grayscale -> denoise -> adaptive threshold -> deskew.
    Accepts a BGR or grayscale numpy array, returns a cleaned grayscale array.
    """
    if image is None:
        raise OCRError("Could not read image data for preprocessing.")

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Denoise while preserving edges/text strokes
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive threshold handles uneven lighting/scan shadows better than a
    # single global threshold.
    thresh = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )

    deskewed = _deskew(thresh)
    return deskewed


def _deskew(image: np.ndarray) -> np.ndarray:
    """Estimate and correct small rotation angles using the minAreaRect of text pixels."""
    coords = np.column_stack(np.where(image < 255))
    if coords.shape[0] < 20:
        return image  # not enough foreground pixels to estimate skew safely

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Ignore negligible skew to avoid introducing artifacts
    if abs(angle) < 0.5:
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def _ocr_image_array(image: np.ndarray) -> str:
    if pytesseract is None:
        raise OCRError(
            "pytesseract/Tesseract is not installed on this system. "
            "Install the 'tesseract-ocr' system package and the 'pytesseract' pip package."
        )
    processed = preprocess_image_for_ocr(image)
    try:
        # PSM 6: assume a uniform block of text — works well for lab report tables/lines
        text = pytesseract.image_to_string(processed, config="--psm 6")
    except Exception as exc:
        raise OCRError(f"OCR engine failed: {exc}") from exc
    return text


# ---------------------------------------------------------------------------
# Public extraction entry points
# ---------------------------------------------------------------------------

def extract_text_from_image_bytes(file_bytes: bytes) -> str:
    """OCR an uploaded JPG/PNG image (given as raw bytes)."""
    try:
        pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        image_np = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except Exception as exc:
        raise OCRError(f"Could not read image file: {exc}") from exc

    text = _ocr_image_array(image_np)
    if not text or not text.strip():
        raise OCRError("OCR completed but no text could be detected in the image.")
    return text


def extract_text_from_pdf_bytes(file_bytes: bytes, ocr_dpi: int = 300) -> str:
    """
    Extract text from a PDF.

    1. Try the embedded text layer for every page (fast, accurate — works
       for digitally-generated lab report PDFs).
    2. For any page with little/no embedded text (i.e. a scanned page),
       render it to an image and OCR it instead.
    """
    if fitz is None:
        raise OCRError(
            "PyMuPDF (fitz) is not installed. Install it with `pip install pymupdf`."
        )

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise OCRError(f"Could not open PDF file: {exc}") from exc

    if doc.page_count == 0:
        raise OCRError("The PDF has no pages.")

    all_text_parts = []
    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        layer_text = page.get_text("text") or ""

        if len(layer_text.strip()) >= MIN_TEXT_LAYER_CHARS:
            all_text_parts.append(layer_text)
        else:
            # Likely a scanned page -> render to image and OCR it
            try:
                zoom = ocr_dpi / 72.0
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB)
                img_bytes = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                image_np = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                ocr_text = _ocr_image_array(image_np)
                all_text_parts.append(ocr_text)
            except OCRError:
                raise
            except Exception as exc:
                raise OCRError(f"Failed to OCR scanned page {page_index + 1}: {exc}") from exc

    doc.close()
    full_text = "\n".join(all_text_parts)

    if not full_text or not full_text.strip():
        raise OCRError("No text could be extracted from this PDF (empty or unreadable).")

    return full_text


def extract_text(filename: str, file_bytes: bytes) -> str:
    """
    Unified entry point: dispatches to the PDF or image extractor based on
    file extension, after validating the upload.
    """
    ext = validate_file(filename, file_bytes)
    if ext == ".pdf":
        return extract_text_from_pdf_bytes(file_bytes)
    elif ext in (".jpg", ".jpeg", ".png"):
        return extract_text_from_image_bytes(file_bytes)
    else:
        raise OCRError(f"Unsupported file extension: {ext}")
