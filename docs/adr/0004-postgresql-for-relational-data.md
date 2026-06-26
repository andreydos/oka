# ADR-0004: PostgreSQL for Relational Data

## Status

Accepted

## Context

The system stores documents with versions, chunk text, chat sessions, messages, and citations. Data integrity and query flexibility are required.

## Decision

Use **PostgreSQL 16** with SQLAlchemy 2.0 async and Alembic migrations.

## Alternatives Considered

- **SQLite** — simpler but weaker concurrent write performance
- **JSON files** — no ACID, no relational queries

## Consequences

**Positive:**
- ACID transactions for document versioning and citation storage
- Mature tooling, easy backup (`pg_dump`)
- Handles concurrent reads from multiple users

**Negative:**
- Additional container (~256 MB RAM)
- Requires migration management via Alembic
