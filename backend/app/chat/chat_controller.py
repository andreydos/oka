from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.chat.citation_service import CitationService
from app.chat.chat_service import ChatService
from app.dependencies import get_chat_service
from app.schemas import (
    ChatMessageResponse,
    ChatSessionListItem,
    ChatSessionResponse,
    CitationResponse,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
_citation_service = CitationService()


def _message_to_response(
    message,
    documents: dict | None = None,
    citations: list[CitationResponse] | None = None,
) -> ChatMessageResponse:
    if citations is None:
        citations = []
        if message.citations and documents is not None:
            records = [
                {
                    "document_id": c.document_id,
                    "chunk_id": c.chunk_id,
                    "page": c.page,
                    "quote": c.quote,
                }
                for c in message.citations
            ]
            for item in _citation_service.to_response(records, documents):
                citations.append(CitationResponse(**item))
        elif message.citations:
            for c in message.citations:
                citations.append(
                CitationResponse(
                    document_id=c.document_id,
                    document_name="Unknown",
                    chunk_id=c.chunk_id,
                    page=c.page,
                    section=getattr(c, "section", None),
                    quote=c.quote,
                )
                )

    return ChatMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        citations=citations,
    )


@router.post("/sessions", response_model=ChatSessionListItem, status_code=201)
async def create_session(service: ChatService = Depends(get_chat_service)):
    session = await service.create_session()
    return ChatSessionListItem(id=session.id, title=session.title, created_at=session.created_at)


@router.get("/sessions", response_model=list[ChatSessionListItem])
async def list_sessions(service: ChatService = Depends(get_chat_service)):
    sessions = await service.list_sessions()
    return [
        ChatSessionListItem(id=s.id, title=s.title, created_at=s.created_at) for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    service: ChatService = Depends(get_chat_service),
):
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    documents = await service.get_documents_for_citations(session)

    messages = [_message_to_response(m, documents) for m in session.messages]
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        messages=messages,
    )


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse, status_code=201)
async def send_message(
    session_id: UUID,
    body: SendMessageRequest,
    service: ChatService = Depends(get_chat_service),
):
    try:
        result = await service.send_message(session_id, body.content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    documents = result.get("documents", {})
    citation_records = result.get("citations", [])
    citation_responses = [
        CitationResponse(**item)
        for item in _citation_service.to_response(citation_records, documents)
    ]

    assistant = _message_to_response(
        result["assistant_message"],
        citations=citation_responses,
    )

    return SendMessageResponse(
        user_message=_message_to_response(result["user_message"]),
        assistant_message=assistant,
    )
