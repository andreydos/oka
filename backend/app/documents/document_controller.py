from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.dependencies import get_document_service
from app.documents.document_formats import UnsupportedDocumentError
from app.documents.document_service import DocumentService
from app.schemas import DocumentResponse

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _to_document_response(document, chunk_count: int) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        title=document.title,
        filename=document.filename,
        mime_type=document.mime_type,
        version=document.version,
        status=document.status,
        chunk_count=chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    title: str | None = Form(default=None),
    service: DocumentService = Depends(get_document_service),
):
    try:
        document = await service.upload(file, title)
    except UnsupportedDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    background_tasks.add_task(service.run_ingestion, document.id)
    return _to_document_response(document, 0)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(service: DocumentService = Depends(get_document_service)):
    items = await service.list_documents()
    return [_to_document_response(doc, count) for doc, count in items]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    document, chunk_count = await service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_document_response(document, chunk_count)


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    result = await service.get_document_file(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    document, storage_path = result
    return FileResponse(
        path=storage_path,
        media_type=document.mime_type,
        filename=document.filename,
        content_disposition_type="inline",
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    deleted = await service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    service: DocumentService = Depends(get_document_service),
):
    document = await service.trigger_reindex(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    background_tasks.add_task(service.run_ingestion, document.id)
    document, chunk_count = await service.get_document(document_id)
    return _to_document_response(document, chunk_count)
