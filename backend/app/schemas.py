from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models import DocumentStatus, MessageRole


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    filename: str
    mime_type: str
    version: int
    status: DocumentStatus
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class CitationResponse(BaseModel):
    document_id: UUID
    document_name: str
    chunk_id: UUID
    page: int | None
    section: str | None = None
    quote: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime
    citations: list[CitationResponse] = []


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    messages: list[ChatMessageResponse] = []


class ChatSessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class HealthResponse(BaseModel):
    status: str
    database: str
    qdrant: str
    ollama: str
    ollama_busy: bool
