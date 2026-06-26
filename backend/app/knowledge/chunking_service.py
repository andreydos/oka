import re
import uuid
from dataclasses import dataclass

from app.config import settings
from app.documents.parsed_segment import ParsedSegment

_NUMBERED_ENTRY = re.compile(r"^\d+\.\s", re.MULTILINE)
_BULLET_ENTRY = re.compile(r"^[-*•]\s", re.MULTILINE)
_MIN_ENTRY_CHARS = 40


@dataclass
class TextChunk:
    text: str
    page: int | None
    section: str | None
    chunk_index: int
    token_count: int


class ChunkingService:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self._chunk_size = chunk_size or settings.chunk_size
        self._chunk_overlap = chunk_overlap or settings.chunk_overlap
        self._chars_per_token = 4

    def chunk_segments(self, segments: list[ParsedSegment]) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        index = 0
        for segment in segments:
            entries = self._split_by_entries(segment.text)
            texts = entries if entries else [segment.text]
            for entry_text in texts:
                segment_chunks = self._split_text(entry_text)
                for text in segment_chunks:
                    chunks.append(
                        TextChunk(
                            text=text,
                            page=segment.page,
                            section=segment.section,
                            chunk_index=index,
                            token_count=max(1, len(text) // self._chars_per_token),
                        )
                    )
                    index += 1
        return chunks

    def _split_by_entries(self, text: str) -> list[str] | None:
        """Split list-like blocks so each vacancy/list item can be retrieved separately."""
        text = text.strip()
        if not text:
            return None

        if _NUMBERED_ENTRY.search(text):
            parts = [part.strip() for part in re.split(r"(?m)(?=^\d+\.\s)", text) if part.strip()]
            if len(parts) >= 2 and all(len(part) >= _MIN_ENTRY_CHARS for part in parts):
                return parts

        if _BULLET_ENTRY.search(text):
            parts = [part.strip() for part in re.split(r"(?m)(?=^[-*•]\s)", text) if part.strip()]
            if len(parts) >= 2 and all(len(part) >= _MIN_ENTRY_CHARS for part in parts):
                return parts

        blocks = [block.strip() for block in re.split(r"\n{2,}", text) if block.strip()]
        if len(blocks) >= 2 and all(len(block) >= _MIN_ENTRY_CHARS for block in blocks):
            return blocks

        return None

    def _split_text(self, text: str) -> list[str]:
        max_chars = self._chunk_size * self._chars_per_token
        overlap_chars = self._chunk_overlap * self._chars_per_token
        if len(text) <= max_chars:
            return [text]

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + max_chars
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            if end >= len(text):
                break
            start = end - overlap_chars
        return chunks
