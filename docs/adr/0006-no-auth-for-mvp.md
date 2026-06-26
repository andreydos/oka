# ADR-0006: No Authentication for MVP

## Status

Accepted

## Context

The system targets isolated corporate networks. Authentication adds complexity (user management, sessions, roles) that is not required for initial deployment validation.

## Decision

Deploy as a **single shared instance without authentication** on the local network. All users share the same document corpus and chat sessions.

## Consequences

**Positive:**
- Faster MVP delivery
- Simpler deployment and testing
- No credential management in isolated environment

**Negative:**
- No per-user document isolation
- Chat sessions visible to all users on the instance
- Auth must be added before multi-tenant production use (future ADR)
