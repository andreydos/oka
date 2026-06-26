from dataclasses import dataclass
from uuid import UUID


@dataclass
class VectorSearchResult:
    chunk_id: UUID
    document_id: UUID
    page: int | None
    section: str | None
    chunk_index: int
    score: float


@dataclass
class VectorPoint:
    chunk_id: UUID
    document_id: UUID
    page: int | None
    section: str | None
    chunk_index: int
    vector: list[float]
