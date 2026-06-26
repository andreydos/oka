#!/bin/sh
set -e

ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama..."
until ollama list >/dev/null 2>&1; do
  sleep 2
done

echo "Pulling models (requires network on first run)..."
ollama pull "${OLLAMA_MODEL:-llama3.2:3b}" || true
ollama pull "${EMBEDDING_MODEL:-nomic-embed-text}" || true

echo "Ollama ready."
wait $OLLAMA_PID
