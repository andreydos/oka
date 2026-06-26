# Architecture Overview

## System Purpose

Offline Knowledge Assistant — upload internal documents, ask questions, receive cited answers. Fully offline after deployment.

## Module Diagram

```
frontend (React)
    │
    ▼
FastAPI (modular monolith)
├── documents/   upload, metadata, versions, parsing
├── knowledge/   chunking, embeddings, vector indexing
├── chat/        RAG orchestration, citations
├── llm/         LLM client abstraction (Ollama)
├── storage/     local filesystem for original files
└── db/          PostgreSQL models and migrations
    │
    ├── PostgreSQL  — documents, chunks, chat, citations
    ├── Qdrant      — embedding vectors only
    ├── Filesystem  — original uploaded files
    └── Ollama      — LLM + embeddings
```

## Layer Rules

Every module follows **controller → service → repository/client**:

- **Controllers** — HTTP routing, request/response validation only
- **Services** — business logic, orchestration
- **Repositories** — PostgreSQL access
- **Clients** — external system access (Qdrant, Ollama, filesystem)

Never access Qdrant, PostgreSQL, or Ollama directly from controllers.

## Data Flow: Document Upload

1. Controller receives multipart upload
2. DocumentService saves file via LocalFileStorage
3. DocumentRepository creates Document + DocumentVersion records
4. IngestionService (background): parse → chunk → embed → upsert Qdrant + save chunks to PG
5. Document status: `pending → processing → indexed | failed`

## Data Flow: Question Answering

1. User message saved to PostgreSQL
2. Question embedded via Ollama
3. Qdrant similarity search (top_k=5)
4. If best score < threshold → "not found" (no LLM call)
5. Else fetch chunk texts from PostgreSQL
6. LLM generates answer from context
7. Assistant message + citations saved to PostgreSQL

## ML Mutex

When `ML_MUTEX_ENABLED=true`, ingestion and chat share an asyncio lock around Ollama calls. Prevents OOM on 16 GB hardware.
