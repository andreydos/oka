# ADR-0001: Modular Monolith Architecture

## Status

Accepted

## Context

The Offline Knowledge Assistant must run in isolated corporate environments with minimal operational overhead. The system includes document management, knowledge indexing, RAG-based chat, and local LLM integration.

## Decision

Build a **modular monolith** with clear module boundaries (documents, knowledge, chat, llm, storage, db) and layered architecture (controller → service → repository).

## Consequences

**Positive:**
- Single deployable unit via Docker Compose
- Simpler offline operations — no service mesh, no inter-service networking
- Clear module boundaries enable future extraction if needed
- Easier debugging on constrained hardware

**Negative:**
- All modules scale together; cannot scale LLM and API independently without config changes
- Single process failure affects entire API (mitigated by Docker restart policies)
