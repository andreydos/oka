import uuid
from uuid import UUID

from app.documents.document_formats import UnsupportedDocumentError, sanitize_text
from app.db.models import DocumentChunk, DocumentStatus
from app.db.session import async_session_factory
from app.documents.document_parser import DocumentParser
from app.documents.document_repository import DocumentRepository
from app.knowledge.chunking_service import ChunkingService
from app.knowledge.embedding_service import EmbeddingService
from app.knowledge.vector_models import VectorPoint
from app.knowledge.vector_repository import VectorRepository
from app.storage.local_file_storage import LocalFileStorage


class IngestionService:
    def __init__(
        self,
        vector_repository: VectorRepository,
        embedding_service: EmbeddingService | None = None,
        chunking_service: ChunkingService | None = None,
        parser: DocumentParser | None = None,
        storage: LocalFileStorage | None = None,
    ) -> None:
        self._vector_repository = vector_repository
        self._embedding_service = embedding_service or EmbeddingService()
        self._chunking_service = chunking_service or ChunkingService()
        self._parser = parser or DocumentParser()
        self._storage = storage or LocalFileStorage()

    async def ingest(self, document_id: UUID) -> None:
        async with async_session_factory() as session:
            repository = DocumentRepository(session)
            document = await repository.get_by_id(document_id)
            if not document or document.status == DocumentStatus.ARCHIVED:
                return

            version_record = await repository.get_latest_version(document_id)
            if not version_record:
                await repository.update_status(document_id, DocumentStatus.FAILED)
                return

            await repository.update_status(document_id, DocumentStatus.PROCESSING)

            try:
                content = await self._storage.read(version_record.storage_path)
                segments = self._parser.parse(content, document.mime_type, document.filename)
                if not segments:
                    await repository.update_status(document_id, DocumentStatus.FAILED)
                    return

                text_chunks = self._chunking_service.chunk_segments(segments)
                old_chunk_ids = await repository.get_chunk_ids_for_document(document_id)
                if old_chunk_ids:
                    await self._vector_repository.delete_by_chunk_ids(old_chunk_ids)

                db_chunks: list[DocumentChunk] = []
                for tc in text_chunks:
                    db_chunks.append(
                        DocumentChunk(
                            id=uuid.uuid4(),
                            document_id=document_id,
                            document_version=version_record.version,
                            page=tc.page,
                            section=tc.section,
                            chunk_index=tc.chunk_index,
                            text=sanitize_text(tc.text),
                            token_count=tc.token_count,
                        )
                    )

                embeddings = await self._embedding_service.embed_batch([c.text for c in db_chunks])
                vector_points = [
                    VectorPoint(
                        chunk_id=db_chunks[i].id,
                        document_id=document_id,
                        page=db_chunks[i].page,
                        section=db_chunks[i].section,
                        chunk_index=db_chunks[i].chunk_index,
                        vector=embeddings[i],
                    )
                    for i in range(len(db_chunks))
                ]

                await repository.replace_chunks(document_id, version_record.version, db_chunks)
                await self._vector_repository.upsert_points(vector_points)
                await repository.update_status(document_id, DocumentStatus.INDEXED)
            except UnsupportedDocumentError:
                await session.rollback()
                await repository.update_status(document_id, DocumentStatus.FAILED)
            except Exception:
                await session.rollback()
                await repository.update_status(document_id, DocumentStatus.FAILED)
                raise
