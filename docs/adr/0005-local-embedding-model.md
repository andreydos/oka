# ADR-0005: Embeddings via Ollama (nomic-embed-text)

## Status

Accepted

## Context

RAG requires local embedding generation. Target hardware is 16 GB RAM, CPU-only. Loading PyTorch/sentence-transformers in the Python backend adds ~1.5 GB RAM.

## Decision

Generate embeddings via **Ollama** using the `nomic-embed-text` model (768 dimensions). No PyTorch or sentence-transformers in the backend.

## Alternatives Considered

- **sentence-transformers in Python** — +1.5 GB RAM, second ML stack
- **Cloud embedding APIs** — violates offline requirement

## Consequences

**Positive:**
- Single ML runtime (Ollama) for both LLM and embeddings
- Backend stays lightweight (~256 MB)
- GPU acceleration applies automatically on stronger hardware

**Negative:**
- HTTP round-trip per embedding batch (acceptable for MVP scale)
- Embedding and LLM share Ollama — requires ML mutex on weak hardware
