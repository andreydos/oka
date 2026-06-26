from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.vector_models import VectorPoint, VectorSearchResult


class VectorRepository(ABC):
    @abstractmethod
    async def ensure_collection(self) -> None:
        """Create collection if it does not exist."""

    @abstractmethod
    async def upsert_points(self, points: list[VectorPoint]) -> None:
        """Insert or update vector points."""

    @abstractmethod
    async def search(self, vector: list[float], top_k: int) -> list[VectorSearchResult]:
        """Similarity search returning scored results."""

    @abstractmethod
    async def delete_by_document(self, document_id: UUID) -> None:
        """Remove all vectors for a document."""

    @abstractmethod
    async def delete_by_chunk_ids(self, chunk_ids: list[UUID]) -> None:
        """Remove vectors by chunk IDs."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if vector store is reachable."""
