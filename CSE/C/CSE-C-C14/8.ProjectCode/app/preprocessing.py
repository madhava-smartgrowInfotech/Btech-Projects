"""Image upload validation and preprocessing for VeriVision AI."""
import io
import os
import tempfile

from PIL import Image, UnidentifiedImageError

from . import config

_MIME_BY_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


class PreprocessingError(ValueError):
    """User-facing preprocessing failure."""


def allowed_extension(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in config.ALLOWED_EXTENSIONS


def validate_upload(file_storage):
    """Validate a Flask FileStorage upload. Returns (bytes, ext)."""
    if file_storage is None or not getattr(file_storage, "filename", ""):
        raise PreprocessingError("No image file was provided. Please choose an image to analyze.")
    filename = file_storage.filename
    if not allowed_extension(filename):
        raise PreprocessingError(
            "Unsupported file type. Please upload a PNG, JPG/JPEG or WEBP image."
        )
    data = file_storage.read()
    if not data:
        raise PreprocessingError("The uploaded file is empty. Please try a different image.")
    if len(data) > config.MAX_CONTENT_LENGTH:
        raise PreprocessingError(
            f"Image exceeds the {config.MAX_UPLOAD_MB} MB size limit. Please upload a smaller file."
        )
    ext = filename.rsplit(".", 1)[-1].lower()
    return data, ext


def decode_image(image_bytes):
    """Decode raw bytes to an RGB PIL image, rejecting corrupt content."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except (UnidentifiedImageError, OSError, ValueError, IOError):
        raise PreprocessingError(
            "This file could not be decoded as an image. It may be corrupted or unsupported."
        )
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, IOError):
        raise PreprocessingError(
            "This file could not be decoded as an image. It may be corrupted or unsupported."
        )
    if img.width < 8 or img.height < 8:
        raise PreprocessingError("The image is too small to analyze. Please upload a larger image.")
    return img


def load_pil_from_bytes(image_bytes):
    return decode_image(image_bytes)


def save_temp_file(image_bytes, suffix):
    """Save bytes to a secure temp file; caller must delete it."""
    fd, path = tempfile.mkstemp(suffix="." + suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(image_bytes)
    except OSError:
        try:
            os.remove(path)
        except OSError:
            pass
        raise PreprocessingError("Could not process the uploaded image. Please try again.")
    return path


def get_imagenet_normalize():
    return config.IMAGENET_MEAN, config.IMAGENET_STD
