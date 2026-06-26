#!/usr/bin/env bash
# Start Postgres, Qdrant, Ollama for local development.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if docker compose version >/dev/null 2>&1; then
  echo "Starting infra via docker compose..."
  docker compose up postgres qdrant ollama -d
else
  echo "docker compose not found — using docker run..."
  docker rm -f oka-postgres oka-qdrant oka-ollama 2>/dev/null || true
  docker run -d --name oka-postgres \
    -e POSTGRES_USER=oka -e POSTGRES_PASSWORD=oka -e POSTGRES_DB=oka \
    -p 5432:5432 postgres:16-alpine
  docker run -d --name oka-qdrant \
    -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
  docker run -d --name oka-ollama \
    -p 11434:11434 \
    -v oka_ollama_models:/root/.ollama \
    ollama/ollama:latest
fi

echo "Waiting for services..."
for i in $(seq 1 30); do
  curl -sf http://localhost:6333/healthz >/dev/null 2>&1 && break
  sleep 1
done

OLLAMA_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'ollama|oka-ollama' | head -1)
if [[ -n "$OLLAMA_CONTAINER" ]]; then
  echo "Pulling Ollama models (first run needs network)..."
  docker exec "$OLLAMA_CONTAINER" ollama pull llama3.2:3b || true
  docker exec "$OLLAMA_CONTAINER" ollama pull nomic-embed-text || true
fi

echo ""
echo "Infra ready. Next:"
echo "  Backend:  cd backend && source .venv/bin/activate && see docs/RUNBOOK.md"
echo "  Frontend: cd frontend && npm run dev"
echo "  Health:   curl -s http://localhost:11434/api/tags"
