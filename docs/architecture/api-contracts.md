# API Contracts

Base URL: `/api/v1`

OpenAPI spec available at `/docs` when backend is running.

## Health

### GET /health

```json
{
  "status": "ok",
  "database": "ok",
  "qdrant": "ok",
  "ollama": "ok",
  "ollama_busy": false
}
```

## Documents

### POST /documents

Upload a document (multipart/form-data).

**Form fields:**
- `file` — required
- `title` — optional, defaults to filename

**Response 201:**
```json
{
  "id": "uuid",
  "title": "VPN Manual",
  "filename": "vpn-manual.pdf",
  "mime_type": "application/pdf",
  "version": 1,
  "status": "pending",
  "chunk_count": 0,
  "created_at": "2026-06-23T10:00:00Z",
  "updated_at": "2026-06-23T10:00:00Z"
}
```

### GET /documents

List all non-archived documents.

### GET /documents/{id}

Document detail with chunk count.

### DELETE /documents/{id}

Soft-delete: archive document, remove vectors from Qdrant.

**Response 204**

### POST /documents/{id}/reindex

Re-index current version from stored file.

**Response 200:** Updated document object with status `pending`.

## Chat

### POST /chat/sessions

Create a new chat session.

**Response 201:**
```json
{
  "id": "uuid",
  "title": "New chat",
  "created_at": "2026-06-23T10:00:00Z"
}
```

### GET /chat/sessions

List sessions ordered by created_at desc.

### GET /chat/sessions/{id}

Session with all messages and citations.

### POST /chat/sessions/{id}/messages

Ask a question.

**Request:**
```json
{ "content": "How do I reset the VPN?" }
```

**Response 201:**
```json
{
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "How do I reset the VPN?",
    "created_at": "..."
  },
  "assistant_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "To reset the VPN...",
    "created_at": "...",
    "citations": [
      {
        "document_id": "uuid",
        "document_name": "vpn-manual.pdf",
        "chunk_id": "uuid",
        "page": 12,
        "quote": "To reset the VPN connection..."
      }
    ]
  }
}
```

When no relevant chunks found:
```json
{
  "assistant_message": {
    "content": "Information was not found in the indexed documents.",
    "citations": []
  }
}
```

**Response 503** when Ollama is unavailable.
