import aiofiles
from pathlib import Path

from app.config import settings
from app.storage.storage_interface import FileStorage


class LocalFileStorage(FileStorage):
    def __init__(self, base_dir: str | None = None) -> None:
        self._base_dir = Path(base_dir or settings.upload_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _document_dir(self, document_id: str, version: int) -> Path:
        return self._base_dir / document_id / f"v{version}"

    async def save(self, document_id: str, version: int, filename: str, content: bytes) -> str:
        doc_dir = self._document_dir(document_id, version)
        doc_dir.mkdir(parents=True, exist_ok=True)
        path = doc_dir / filename
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)
        return str(path)

    async def read(self, storage_path: str) -> bytes:
        async with aiofiles.open(storage_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists():
            path.unlink()
