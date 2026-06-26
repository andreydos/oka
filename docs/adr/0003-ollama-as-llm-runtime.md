# ADR-0003: Ollama as LLM Runtime

## Status

Accepted

## Context

The system must run fully offline with a local LLM on office hardware (CPU-only, 16 GB RAM). LLM access must be abstracted for future replacement.

## Decision

Use **Ollama** as the LLM runtime, accessed via HTTP API. Implement `LLMClient` protocol with `OllamaClient` and `MockLLMClient` for tests. Default model: `llama3.2:3b`.

## Alternatives Considered

- **llama.cpp direct** — lower-level, more setup, no model management UI
- **vLLM** — requires GPU, overkill for target hardware
- **Cloud APIs** — violates offline requirement

## Consequences

**Positive:**
- Simple model management (`ollama pull`)
- Automatic GPU detection on stronger hardware
- HTTP API keeps chat module decoupled from Ollama internals
- Same runtime serves embeddings (`nomic-embed-text`)

**Negative:**
- Additional container in Docker Compose (~3–4 GB RAM for 3b model)
- HTTP overhead negligible compared to inference time on CPU
