from pathlib import Path

SUPPORTED_EXTENSIONS = frozenset(
    {".pdf", ".docx", ".txt", ".md", ".markdown", ".html", ".htm", ".png", ".jpg", ".jpeg", ".webp"}
)

SUPPORTED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown",
        "text/html",
        "image/png",
        "image/jpeg",
        "image/webp",
    }
)

OCR_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})
OCR_IMAGE_MIME_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})

_OCR_IMAGE_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "PNG image"),
    (b"\xff\xd8\xff", "JPEG image"),
)

_UNSUPPORTED_IMAGE_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"GIF87a", "GIF image"),
    (b"GIF89a", "GIF image"),
    (b"BM", "BMP image"),
    (b"II*\x00", "TIFF image"),
    (b"MM\x00*", "TIFF image"),
)


class UnsupportedDocumentError(ValueError):
    pass


def sanitize_text(text: str) -> str:
    return text.replace("\x00", "")


def detect_ocr_image_format(content: bytes) -> str | None:
    if len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "WebP image"

    for signature, label in _OCR_IMAGE_SIGNATURES:
        if content.startswith(signature):
            return label

    return None


def detect_unsupported_image_format(content: bytes) -> str | None:
    for signature, label in _UNSUPPORTED_IMAGE_SIGNATURES:
        if content.startswith(signature):
            return label
    return None


def is_image_document(filename: str, mime_type: str, content: bytes) -> bool:
    ext = Path(filename).suffix.lower()
    mime = (mime_type or "").lower()
    return ext in OCR_IMAGE_EXTENSIONS or mime in OCR_IMAGE_MIME_TYPES


def validate_document(filename: str, mime_type: str, content: bytes) -> None:
    ext = Path(filename).suffix.lower()
    mime = (mime_type or "").lower()

    unsupported_image = detect_unsupported_image_format(content)
    if unsupported_image:
        raise UnsupportedDocumentError(
            f"Unsupported image type: {unsupported_image}. "
            "Supported images: PNG, JPEG, WebP (English OCR)."
        )

    if is_image_document(filename, mime_type, content):
        if not detect_ocr_image_format(content):
            raise UnsupportedDocumentError(
                "File does not look like a valid PNG, JPEG, or WebP image."
            )
        return

    if mime.startswith("image/"):
        raise UnsupportedDocumentError(
            f"Unsupported image type ({mime}). "
            "Supported images: PNG, JPEG, WebP (English OCR)."
        )

    if detect_ocr_image_format(content):
        raise UnsupportedDocumentError(
            "File looks like an image. Upload it with a .png, .jpg, or .webp extension for OCR."
        )

    if ext not in SUPPORTED_EXTENSIONS and mime not in SUPPORTED_MIME_TYPES:
        raise UnsupportedDocumentError(
            f"Unsupported file extension '{ext or '(none)'}'. "
            "Supported: PDF, DOCX, TXT, Markdown, HTML, PNG, JPEG, WebP."
        )
