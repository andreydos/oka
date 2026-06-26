from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.chat_service import ChatService
from app.chat.citation_service import CitationService
from app.config import settings
from app.db.session import get_session
from app.documents.document_repository import ChatRepository, DocumentRepository
from app.documents.document_service import DocumentService
from app.knowledge.embedding_service import EmbeddingService
from app.knowledge.ingestion_service import IngestionService
from app.knowledge.qdrant_vector_repository import QdrantVectorRepository
from app.knowledge.vector_repository import VectorRepository
from app.llm.llm_client import LLMClient
from app.llm.mock_llm_client import MockLLMClient
from app.llm.ollama_client import OllamaClient
from app.storage.local_file_storage import LocalFileStorage
from app.storage.storage_interface import FileStorage


@lru_cache
def get_vector_repository() -> VectorRepository:
    return QdrantVectorRepository()


@lru_cache
def get_file_storage() -> FileStorage:
    return LocalFileStorage()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


@lru_cache
def get_llm_client() -> LLMClient:
    if settings.llm_provider == "mock":
        return MockLLMClient()
    return OllamaClient()


@lru_cache
def get_ingestion_service() -> IngestionService:
    return IngestionService(
        vector_repository=get_vector_repository(),
        embedding_service=get_embedding_service(),
        storage=LocalFileStorage(),
    )


def get_document_repository(session: AsyncSession = Depends(get_session)) -> DocumentRepository:
    return DocumentRepository(session)


def get_chat_repository(session: AsyncSession = Depends(get_session)) -> ChatRepository:
    return ChatRepository(session)


def get_document_service(
    session: AsyncSession = Depends(get_session),
) -> DocumentService:
    return DocumentService(
        repository=DocumentRepository(session),
        storage=get_file_storage(),
        ingestion_service=get_ingestion_service(),
        vector_repository=get_vector_repository(),
    )


def get_chat_service(
    session: AsyncSession = Depends(get_session),
) -> ChatService:
    return ChatService(
        chat_repository=ChatRepository(session),
        document_repository=DocumentRepository(session),
        vector_repository=get_vector_repository(),
        embedding_service=get_embedding_service(),
        llm_client=get_llm_client(),
        citation_service=CitationService(),
    )
