import uuid
from uuid import UUID

from fastapi import UploadFile

from app.db.models import Document, DocumentChunk, DocumentStatus
from app.documents.document_formats import validate_document
from app.documents.document_parser import DocumentParser
from app.documents.document_repository import DocumentRepository
from app.knowledge.ingestion_service import IngestionService
from app.knowledge.vector_repository import VectorRepository
from app.storage.storage_interface import FileStorage


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        storage: FileStorage,
        ingestion_service: IngestionService,
        vector_repository: VectorRepository,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._ingestion = ingestion_service
        self._vector_repository = vector_repository
        self._parser = DocumentParser()

    async def upload(self, file: UploadFile, title: str | None = None) -> Document:
        content = await file.read()
        filename = file.filename or "untitled"
        mime_type = file.content_type or "application/octet-stream"
        validate_document(filename, mime_type, content)
        doc_title = title or filename

        document_id = str(uuid.uuid4())
        storage_path = await self._storage.save(document_id, 1, filename, content)
        document = await self._repository.create_document(
            title=doc_title,
            filename=filename,
            mime_type=mime_type,
            storage_path=storage_path,
            content=content,
        )
        return document

    async def list_documents(self) -> list[tuple[Document, int]]:
        return await self._repository.list_documents()

    async def get_document(self, document_id: UUID) -> tuple[Document | None, int]:
        return await self._repository.get_with_chunk_count(document_id)

    async def get_document_file(self, document_id: UUID) -> tuple[Document, str] | None:
        document = await self._repository.get_by_id(document_id)
        if not document or document.status == DocumentStatus.ARCHIVED:
            return None
        version = await self._repository.get_latest_version(document_id)
        if not version:
            return None
        return document, version.storage_path

    async def delete_document(self, document_id: UUID) -> bool:
        document = await self._repository.get_by_id(document_id)
        if not document:
            return False
        await self._vector_repository.delete_by_document(document_id)
        await self._repository.archive(document_id)
        return True

    async def trigger_reindex(self, document_id: UUID) -> Document | None:
        document = await self._repository.get_by_id(document_id)
        if not document:
            return None
        await self._repository.update_status(document_id, DocumentStatus.PENDING)
        return await self._repository.get_by_id(document_id)

    async def run_ingestion(self, document_id: UUID) -> None:
        await self._ingestion.ingest(document_id)
