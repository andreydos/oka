# OKA — Runbook: how to start the project

This document describes the **verified** startup path. Follow it in order.

---

## Two modes

| Mode | When | UI URL |
|------|------|--------|
| **Local dev** (recommended for development) | Backend + frontend on host, infra in Docker | http://localhost:5173 |
| **Full Docker** | Production-like, everything in containers | http://localhost:3000 |

---

## Prerequisites

- **Python 3.12** (not 3.9 — type hints and deps require 3.12)
- **Node.js 18+** and npm
- **Docker** (Colima on macOS is fine)
- **~8 GB RAM** allocated to Docker/Colima for Ollama
- Internet on **first run only** (pull Docker images + Ollama models)

Optional for image OCR:
- macOS: `brew install tesseract`
- Debian/Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-eng`

---

## Local development (recommended)

### Step 0 — Colima memory (macOS)

```bash
colima list
# MEMORY must be >= 8GiB. If not:
colima stop
colima start --memory 8 --cpu 4
```

Without enough RAM, Ollama returns `500` and logs show `signal: killed`.

### Step 1 — Start infrastructure

From repo root `/path/to/oka`:

```bash
docker compose up postgres qdrant ollama -d
```

Wait until services respond:

```bash
curl -sf http://localhost:6333/healthz && echo "qdrant ok"
curl -sf http://localhost:11434/api/tags && echo "ollama ok"
```

**First time — pull LLM models** (requires network, ~2–5 min):

```bash
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text
```

If container name differs, use `docker ps` and `docker exec <ollama-container> ollama pull ...`.

Postgres is exposed on `localhost:5432`, Qdrant on `6333`, Ollama on `11434` when compose publishes default ports. If ports are not mapped, add to `docker-compose.yml` or use Plan B below.

### Step 2 — Backend

```bash
cd backend

# One-time setup
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Every session
source .venv/bin/activate
export DATABASE_URL=postgresql+asyncpg://oka:oka@localhost:5432/oka
export QDRANT_URL=http://localhost:6333
export OLLAMA_URL=http://localhost:11434
export UPLOAD_DIR="$(pwd)/../data/uploads"
export CORS_ORIGINS=http://localhost:5173
mkdir -p ../data/uploads

PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:

```bash
curl -s http://localhost:8000/api/v1/health
```

Expected: `"status":"ok"` for database, qdrant, ollama.

API docs: http://localhost:8000/docs

### Step 3 — Frontend

New terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

Vite proxies `/api` → `http://localhost:8000` (see `frontend/vite.config.ts`).

### Step 4 — Smoke test

1. http://localhost:5173/documents — upload a `.md` or `.txt` file
2. Wait until status = `indexed`
3. http://localhost:5173/chat — ask a question about the document

---

## Full Docker (production-like)

```bash
cp .env.example .env
docker compose up --build
```

Open **http://localhost:3000** (nginx → backend).

First start pulls Ollama models via `docker/init-ollama.sh`.

---

## Plan B — `docker compose` unavailable

If `docker compose` command fails, start containers manually:

```bash
docker rm -f oka-postgres oka-qdrant oka-ollama 2>/dev/null

docker run -d --name oka-postgres \
  -e POSTGRES_USER=oka -e POSTGRES_PASSWORD=oka -e POSTGRES_DB=oka \
  -p 5432:5432 postgres:16-alpine

docker run -d --name oka-qdrant \
  -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest

docker run -d --name oka-ollama \
  -p 11434:11434 \
  -v oka_ollama_models:/root/.ollama \
  ollama/ollama:latest
```

Then pull models and run backend/frontend on host (Step 2–3 above).

---

## Environment variables

| Variable | Local dev value |
|----------|-----------------|
| `DATABASE_URL` | `postgresql+asyncpg://oka:oka@localhost:5432/oka` |
| `QDRANT_URL` | `http://localhost:6333` |
| `OLLAMA_URL` | `http://localhost:11434` |
| `UPLOAD_DIR` | `../data/uploads` (absolute path OK) |
| `CORS_ORIGINS` | `http://localhost:5173` |
| `LLM_PROVIDER` | `ollama` (use `mock` for tests) |

Full list: [.env.example](../.env.example)

---

## Troubleshooting

### Chat returns 500

1. Check backend logs in terminal running uvicorn
2. Common causes:
   - **Qdrant API**: use `query_points`, not `search` (already fixed in code)
   - **Ollama OOM**: increase Colima memory to 8 GB
   - **Ollama not ready**: `curl http://localhost:11434/api/tags`

### `docker compose` / `docker compose up` fails

- Try `docker compose` (with space) — Compose V2 plugin
- If missing, use Plan B (`docker run`)
- On Colima: ensure `colima status` shows Running

### Backend `TypeError` on startup (Python)

- Wrong Python version. Use 3.12: `python3.12 -m venv .venv`

### Health shows `ollama: error`

```bash
docker ps | grep ollama
docker logs oka-ollama --tail 30
docker exec oka-ollama ollama list
```

### Health shows `database: error`

```bash
docker ps | grep postgres
docker exec oka-postgres pg_isready -U oka
```

### Frontend calls wrong API URL

- Dev: use http://localhost:5173 (Vite proxy handles `/api`)
- Do not open `file://` or wrong port

### Slow first answer (15–40 s)

Normal on CPU with `llama3.2:3b`. UI shows loading state.

---

## Tests (no Docker/Ollama required)

```bash
cd backend
source .venv/bin/activate
LLM_PROVIDER=mock PYTHONPATH=. pytest tests/ -q
```

---

## Stop services

```bash
# Frontend/backend: Ctrl+C in terminals

# Infra
docker compose down
# or
docker stop oka-postgres oka-qdrant oka-ollama
```

---

## Architecture reminder

- **PostgreSQL** — documents, chunks, chat, citations
- **Qdrant** — vectors only (never chat history)
- **Ollama** — LLM + embeddings
- **Filesystem** — original uploaded files

See [architecture/overview.md](architecture/overview.md) and [adr/](../adr/).
