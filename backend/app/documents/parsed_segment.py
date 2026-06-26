from dataclasses import dataclass


@dataclass
class ParsedSegment:
    text: str
    page: int | None = None
    section: str | None = None
