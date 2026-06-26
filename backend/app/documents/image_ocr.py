import io
import shutil

import pytesseract
from PIL import Image

from app.config import settings
from app.documents.document_formats import UnsupportedDocumentError, sanitize_text


class OcrNotAvailableError(UnsupportedDocumentError):
    pass


def is_tesseract_available() -> bool:
    cmd = settings.tesseract_cmd or "tesseract"
    return shutil.which(cmd) is not None


def extract_text_from_image(content: bytes) -> str:
    """Extract English text from an image using offline Tesseract OCR."""
    cmd = settings.tesseract_cmd or "tesseract"
    if not shutil.which(cmd):
        raise OcrNotAvailableError(
            "Tesseract OCR is not installed. "
            "Install tesseract and the English language pack (tesseract-ocr-eng)."
        )

    pytesseract.pytesseract.tesseract_cmd = cmd

    try:
        image = Image.open(io.BytesIO(content))
    except OSError as e:
        raise UnsupportedDocumentError("File does not contain a valid image.") from e

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    text = pytesseract.image_to_string(image, lang=settings.ocr_language)
    text = sanitize_text(text).strip()
    if not text:
        raise UnsupportedDocumentError(
            "No English text could be extracted from the image. "
            "Use clear screenshots with readable Latin text."
        )
    return text
