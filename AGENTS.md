# Agent instructions — OKA

**Read first:** [docs/RUNBOOK.md](docs/RUNBOOK.md)

## Canonical local dev startup (macOS + Colima)

Do **not** install Ollama via Homebrew if Docker Ollama is used. Do **not** use system Python 3.9 — use **Python 3.12**.

### 1. Infrastructure (Docker)

```bash
# Colima must have >= 8 GB RAM or Ollama models get killed (signal: killed)
colima status    # check memory; if 2GiB → colima stop && colima start --memory 8 --cpu 4

# Preferred: docker compose (infra only)
docker compose up postgres qdrant ollama -d

# Verify
curl -s http://localhost:6333/healthz
curl -s http://localhost:11434/api/tags
docker exec oka-postgres pg_isready -U oka   # only if container named oka-postgres
```

If `docker compose` is unavailable, see **Plan B** in [docs/RUNBOOK.md](docs/RUNBOOK.md).

First Ollama start: pull models (needs network once):

```bash
docker exec oka-ollama ollama pull llama3.2:3b
docker exec oka-ollama ollama pull nomic-embed-text
```

### 2. Backend (host, not Docker)

```bash
cd backend
/opt/homebrew/bin/python3.12 -m venv .venv   # or python3.12
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql+asyncpg://oka:oka@localhost:5432/oka
export QDRANT_URL=http://localhost:6333
export OLLAMA_URL=http://localhost:11434
export UPLOAD_DIR="$(pwd)/../data/uploads"
export CORS_ORIGINS=http://localhost:5173
mkdir -p ../data/uploads

PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend (host)

```bash
cd frontend
npm install
npm run dev
```

### URLs

| Service | URL |
|---------|-----|
| **UI (dev)** | http://localhost:5173 |
| **API** | http://localhost:8000 |
| **Health** | http://localhost:8000/api/v1/health |
| **Swagger** | http://localhost:8000/docs |

Full Docker stack (production-like): UI on **port 3000**, not 5173.

### Health check (all must be ok)

```bash
curl -s http://localhost:8000/api/v1/health
# {"status":"ok","database":"ok","qdrant":"ok","ollama":"ok","ollama_busy":false}
```

### Common mistakes

| Wrong | Right |
|-------|-------|
| `python3` (3.9 on macOS) | Python **3.12** |
| Start backend before Docker infra | Postgres + Qdrant + Ollama first |
| `brew install ollama` + Docker Ollama on same port | One Ollama only, prefer Docker |
| Colima 2 GB RAM | **8 GB** minimum for llama3.2:3b |
| Open http://localhost:3000 in dev | Dev frontend is **5173** |
| Qdrant `client.search()` | Use `query_points()` (qdrant-client 1.18+) |
| `uvicorn` without `PYTHONPATH=.` from `backend/` | Always `PYTHONPATH=.` in backend dir |
| Run full `docker compose up` for quick dev | Infra in Docker, backend+frontend on host |

### Tests (no Ollama needed)

```bash
cd backend && source .venv/bin/activate
LLM_PROVIDER=mock PYTHONPATH=. pytest tests/ -q
```
