from abc import ABC, abstractmethod


class FileStorage(ABC):
    @abstractmethod
    async def save(self, document_id: str, version: int, filename: str, content: bytes) -> str:
        """Save file and return storage path."""

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Read file content by path."""

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete file by path."""
