import io
import re
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from pypdf import PdfReader

from app.documents.document_formats import is_image_document, sanitize_text, validate_document
from app.documents.image_ocr import extract_text_from_image
from app.documents.parsed_segment import ParsedSegment

HEADER_SPLIT = re.compile(r"(?=^#{1,4}\s+)", re.MULTILINE)


class DocumentParser:
    def parse(self, content: bytes, mime_type: str, filename: str) -> list[ParsedSegment]:
        validate_document(filename, mime_type, content)
        ext = Path(filename).suffix.lower()
        if mime_type == "application/pdf" or ext == ".pdf":
            return self._parse_pdf(content)
        if mime_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ) or ext == ".docx":
            return self._parse_docx(content)
        if mime_type in ("text/html",) or ext in (".html", ".htm"):
            return self._parse_html(content)
        if is_image_document(filename, mime_type, content):
            return self._parse_image(content)
        return self._parse_plain(content)

    def _parse_pdf(self, content: bytes) -> list[ParsedSegment]:
        reader = PdfReader(io.BytesIO(content))
        segments: list[ParsedSegment] = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                segments.extend(self._split_by_headers(text, page=page_num))
        return segments

    def _split_by_headers(self, text: str, page: int | None = None) -> list[ParsedSegment]:
        text = sanitize_text(text).strip()
        if not text:
            return []
        parts = [p.strip() for p in HEADER_SPLIT.split(text) if p.strip()]
        if not parts:
            return [ParsedSegment(text=text, page=page)]

        segments: list[ParsedSegment] = []
        for part in parts:
            lines = part.split("\n", 1)
            if lines[0].startswith("#"):
                section = lines[0].lstrip("#").strip()
                body = lines[1].strip() if len(lines) > 1 else ""
            else:
                section = None
                body = part
            if body:
                segments.append(ParsedSegment(text=body, page=page, section=section))
        return segments or [ParsedSegment(text=text, page=page)]

    def _parse_docx(self, content: bytes) -> list[ParsedSegment]:
        doc = DocxDocument(io.BytesIO(content))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            return []
        return [ParsedSegment(text="\n".join(paragraphs), section="Document")]

    def _parse_html(self, content: bytes) -> list[ParsedSegment]:
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        sections: list[ParsedSegment] = []
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            section_name = heading.get_text(strip=True)
            parts: list[str] = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ["h1", "h2", "h3", "h4"]:
                    break
                text = sibling.get_text(" ", strip=True)
                if text:
                    parts.append(text)
            if parts:
                sections.append(ParsedSegment(text="\n".join(parts), section=section_name))
        if not sections:
            body_text = soup.get_text("\n", strip=True)
            if body_text:
                sections.append(ParsedSegment(text=body_text, section="Document"))
        return sections

    def _parse_image(self, content: bytes) -> list[ParsedSegment]:
        text = extract_text_from_image(content)
        return [ParsedSegment(text=text, page=1, section="OCR (English)")]

    def _parse_plain(self, content: bytes) -> list[ParsedSegment]:
        text = content.decode("utf-8", errors="replace")
        if not text.strip():
            return []
        return self._split_by_headers(text, page=None)
