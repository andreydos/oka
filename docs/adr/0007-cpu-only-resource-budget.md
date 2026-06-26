# ADR-0007: CPU-Only Resource Budget

## Status

Accepted

## Context

Target deployment: office workstation, 16 GB RAM, CPU only, no dedicated GPU. The system must remain usable without exceeding memory limits.

## Decision

Default configuration optimized for weak hardware:

- Model: `llama3.2:3b` (fallback: `llama3.2:1b` via env)
- `UVICORN_WORKERS=1`
- `ML_MUTEX_ENABLED=true` — serializes Ollama usage between chat and ingestion
- `TOP_K=5`, chunk size 512 tokens, overlap 64
- Docker memory limits per service
- No PyTorch in backend

All parameters tunable via environment variables for stronger hardware (see README hardware tiers).

## Consequences

**Positive:**
- Runs reliably on 16 GB office PCs (~8–10 GB total usage)
- Prevents OOM from parallel ML operations
- Clear upgrade path via env config on GPU servers

**Negative:**
- 15–40 second response time on CPU
- 1–2 concurrent users maximum with defaults
- Ingestion pauses during active chat when mutex enabled
