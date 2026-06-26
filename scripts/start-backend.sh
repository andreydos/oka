#!/usr/bin/env bash
# Run FastAPI backend for local development (infra must be up).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  echo "Creating venv with python3.12..."
  python3.12 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://oka:oka@localhost:5432/oka}"
export QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
export UPLOAD_DIR="${UPLOAD_DIR:-$ROOT/data/uploads}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:5173}"
mkdir -p "$UPLOAD_DIR"

echo "Backend → http://localhost:8000"
echo "Health  → http://localhost:8000/api/v1/health"
PYTHONPATH=. exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
