# ADR-0008: Tesseract OCR for Images

## Status

Accepted

## Context

Users may upload screenshots or photos of English documentation. The MVP pipeline is text-only (chunk → embed → RAG). GPU and cloud vision APIs are out of scope (ADR-0007, offline-first requirement).

## Decision

- Support **PNG, JPEG, and WebP** uploads.
- Extract text at ingestion time with **Tesseract OCR** (`lang=eng`), CPU-only, fully offline after `tesseract-ocr-eng` is installed.
- Store only extracted text in PostgreSQL chunks; original image stays in local filesystem storage.
- Reject other image formats (GIF, BMP, TIFF) and non-image binaries.
- UI and README state **English-only** OCR limitation.

Configuration via `TESSERACT_CMD` and `OCR_LANGUAGE` (default `eng`).

## Consequences

**Positive:**
- Screenshots become searchable without changing RAG architecture
- No PyTorch or GPU; modest RAM/CPU overhead per image
- Works in Docker with `tesseract-ocr` + `tesseract-ocr-eng` packages

**Negative:**
- English only unless additional language packs are installed and configured
- OCR quality depends on image clarity; UI screenshots may be imperfect
- Ingestion slower per image than plain text files
- Tesseract must be present on host (local dev) or in container image
