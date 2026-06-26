# OKA — Offline Knowledge Assistant

Production-quality MVP for isolated corporate environments. Upload internal documents, ask questions in natural language, receive answers with citations — fully offline after deployment.

## Features

- Document upload: PDF, DOCX, TXT, Markdown, HTML, and images (PNG, JPEG, WebP via offline OCR)
- Image OCR uses Tesseract on CPU — **English text only** (no GPU required)
- Local RAG pipeline with Ollama (`llama3.2:3b`) and `nomic-embed-text` embeddings
- Citations with document name, page number, and quote excerpt
- Chat history and documents in PostgreSQL; Qdrant for vector search only
- Modular monolith architecture with clear layer separation

## How to start

**Full guide:** [docs/RUNBOOK.md](docs/RUNBOOK.md)  
**For AI agents:** [AGENTS.md](AGENTS.md)

### Local dev (fastest for development)

```bash
# 1. Infra (Postgres + Qdrant + Ollama)
./scripts/start-infra.sh

# 2. Backend (Python 3.12)
./scripts/start-backend.sh

# 3. Frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** · API **http://localhost:8000/docs**

Requirements: Python **3.12**, Docker with **≥ 8 GB RAM** for Colima (Ollama needs it).

### Full Docker (production-like)

```bash
cp .env.example .env
docker compose up --build
```

Open **http://localhost:3000**

First startup pulls Ollama models — may take several minutes.

### Optional: OCR for images

```bash
brew install tesseract          # macOS
# sudo apt install tesseract-ocr tesseract-ocr-eng   # Linux
```

## Hardware Requirements

### Minimum (office PC)

| Spec | Value |
|------|-------|
| RAM | 16 GB |
| CPU | 4+ cores, no GPU |
| Storage | SSD, 20 GB free |

Expected: 15–40s per answer, 1–2 concurrent users.

### Recommended Settings by Tier

| Tier | OLLAMA_MODEL | ML_MUTEX_ENABLED | UVICORN_WORKERS |
|------|--------------|------------------|-----------------|
| Office PC (16 GB, CPU) | llama3.2:3b | true | 1 |
| Workstation (32 GB, GPU) | llama3.1:8b | false | 2 |
| Server (64 GB, GPU) | llama3.1:8b | false | 4 |

## Architecture

```
Controller → Service → Repository/Client
```

| Module | Responsibility |
|--------|----------------|
| documents | Upload, metadata, parsing |
| knowledge | Chunking, embeddings, Qdrant indexing |
| chat | RAG orchestration, citations |
| llm | Ollama abstraction |
| storage | Local filesystem |
| db | PostgreSQL models |

See [docs/architecture/](docs/architecture/) and [docs/adr/](docs/adr/) for details.

## Data Storage

| Data | Store |
|------|-------|
| Documents, chunks, chat, citations | PostgreSQL |
| Embedding vectors | Qdrant |
| Original files | Local filesystem (`upload_data` volume) |

Chat history is **never** stored in Qdrant.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | System health |
| POST | /api/v1/documents | Upload document |
| GET | /api/v1/documents | List documents |
| POST | /api/v1/chat/sessions/{id}/messages | Ask question |

Full contracts: [docs/architecture/api-contracts.md](docs/architecture/api-contracts.md)

## Operations

### Backup

```bash
docker compose exec postgres pg_dump -U oka oka > backup.sql
# Volumes: postgres_data, qdrant_data, upload_data, ollama_models
```

### Re-index a document

Use **Reindex** button in UI or `POST /api/v1/documents/{id}/reindex`.

### Offline deployment

1. On a machine with internet: `docker compose up` (pulls images and models)
2. Export volumes or pre-build image bundle
3. Deploy to isolated network — no external access required

## Tests

```bash
cd backend
pip install pytest pytest-asyncio
pytest
```

Set `LLM_PROVIDER=mock` for tests without Ollama.

## License

Proprietary — internal use.
