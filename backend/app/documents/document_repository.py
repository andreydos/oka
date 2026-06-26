import hashlib
import uuid
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ChatMessage, ChatSession, Citation, Document, DocumentChunk, DocumentStatus, DocumentVersion, MessageRole


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_document(
        self,
        title: str,
        filename: str,
        mime_type: str,
        storage_path: str,
        content: bytes,
    ) -> Document:
        checksum = hashlib.sha256(content).hexdigest()
        document = Document(
            title=title,
            filename=filename,
            mime_type=mime_type,
            version=1,
            status=DocumentStatus.PENDING,
        )
        version = DocumentVersion(
            document=document,
            version=1,
            storage_path=storage_path,
            checksum=checksum,
        )
        self._session.add(document)
        self._session.add(version)
        await self._session.commit()
        await self._session.refresh(document)
        return document

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self._session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def get_with_chunk_count(self, document_id: UUID) -> tuple[Document | None, int]:
        document = await self.get_by_id(document_id)
        if not document:
            return None, 0
        count_result = await self._session.execute(
            select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        return document, count_result.scalar_one()

    async def list_documents(self) -> list[tuple[Document, int]]:
        docs_result = await self._session.execute(
            select(Document)
            .where(Document.status != DocumentStatus.ARCHIVED)
            .order_by(Document.created_at.desc())
        )
        documents = list(docs_result.scalars().all())
        results: list[tuple[Document, int]] = []
        for doc in documents:
            count_result = await self._session.execute(
                select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            )
            results.append((doc, count_result.scalar_one()))
        return results

    async def update_status(self, document_id: UUID, status: DocumentStatus) -> None:
        document = await self.get_by_id(document_id)
        if document:
            document.status = status
            await self._session.commit()

    async def archive(self, document_id: UUID) -> None:
        document = await self.get_by_id(document_id)
        if document:
            document.status = DocumentStatus.ARCHIVED
            await self._session.commit()

    async def get_latest_version(self, document_id: UUID) -> DocumentVersion | None:
        result = await self._session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def replace_chunks(
        self,
        document_id: UUID,
        document_version: int,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        old_chunks_result = await self._session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        old_chunks = list(old_chunks_result.scalars().all())
        for old in old_chunks:
            await self._session.delete(old)
        for chunk in chunks:
            self._session.add(chunk)
        document = await self.get_by_id(document_id)
        if document:
            document.version = document_version
        await self._session.commit()
        return chunks

    async def get_chunks_by_ids(self, chunk_ids: list[UUID]) -> list[DocumentChunk]:
        if not chunk_ids:
            return []
        result = await self._session.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))
        chunks = list(result.scalars().all())
        order = {cid: i for i, cid in enumerate(chunk_ids)}
        return sorted(chunks, key=lambda c: order.get(c.id, 0))

    async def get_chunk_ids_for_document(self, document_id: UUID) -> list[UUID]:
        result = await self._session.execute(
            select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        )
        return list(result.scalars().all())


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, title: str = "New chat") -> ChatSession:
        session = ChatSession(title=title)
        self._session.add(session)
        await self._session.commit()
        await self._session.refresh(session)
        return session

    async def list_sessions(self) -> list[ChatSession]:
        result = await self._session.execute(
            select(ChatSession).order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_session_with_messages(self, session_id: UUID) -> ChatSession | None:
        result = await self._session.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(
                selectinload(ChatSession.messages).selectinload(ChatMessage.citations)
            )
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        citations: list[dict] | None = None,
    ) -> ChatMessage:
        message = ChatMessage(session_id=session_id, role=role, content=content)
        self._session.add(message)
        await self._session.flush()
        if citations:
            for c in citations:
                self._session.add(
                    Citation(
                        message_id=message.id,
                        document_id=c["document_id"],
                        chunk_id=c["chunk_id"],
                        page=c.get("page"),
                        quote=c["quote"],
                    )
                )
        await self._session.commit()
        result = await self._session.execute(
            select(ChatMessage)
            .where(ChatMessage.id == message.id)
            .options(selectinload(ChatMessage.citations))
        )
        return result.scalar_one()

    async def update_session_title(self, session_id: UUID, title: str) -> None:
        result = await self._session.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.title = title[:512]
            await self._session.commit()

    async def get_documents_by_ids(self, document_ids: list[UUID]) -> dict[UUID, Document]:
        if not document_ids:
            return {}
        result = await self._session.execute(select(Document).where(Document.id.in_(document_ids)))
        return {d.id: d for d in result.scalars().all()}
