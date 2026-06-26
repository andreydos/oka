# ADR-0002: Qdrant for Vector Search Only

## Status

Accepted

## Context

The system needs vector similarity search for RAG retrieval. It also stores documents, chat history, and citations. Some RAG implementations store all data in the vector database.

## Decision

Use **Qdrant exclusively for embedding vectors and minimal search payload** (`chunk_id`, `document_id`, `page`, `section`, `chunk_index`). Store all relational data — documents, chunks (full text), chat sessions, messages, citations — in **PostgreSQL**.

Chat history must never be stored in Qdrant.

## Consequences

**Positive:**
- Each database used for its strength: PG for ACID/queries, Qdrant for similarity search
- Chat history queries remain simple SQL
- Clear data boundary reduces architectural confusion

**Negative:**
- Two databases to backup and operate
- Chunk text fetched from PG after vector search (acceptable latency for MVP)
