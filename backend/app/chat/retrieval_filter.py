from app.config import settings
from app.db.models import DocumentChunk
from app.chat.keyword_utils import keyword_overlap
from app.knowledge.vector_models import VectorSearchResult


def filter_search_results(
    results: list[VectorSearchResult],
    chunks: list[DocumentChunk] | None = None,
    query: str = "",
    *,
    min_score: float | None = None,
    relative_gap: float | None = None,
    max_chunks: int | None = None,
) -> list[VectorSearchResult]:
    """Keep chunks ranked by keyword overlap first, then vector similarity."""
    if not results:
        return []

    min_score = min_score if min_score is not None else settings.min_relevance_score
    relative_gap = relative_gap if relative_gap is not None else settings.relevance_relative_gap
    max_chunks = max_chunks if max_chunks is not None else settings.max_context_chunks

    chunk_map = {c.id: c for c in chunks} if chunks else {}

    if not chunk_map or not query:
        ranked = sorted(results, key=lambda r: r.score, reverse=True)
        if ranked[0].score < min_score:
            return []
        return ranked[:max_chunks]

    def keyword_score(chunk: DocumentChunk | None) -> int:
        if not chunk:
            return 0
        return keyword_overlap(query, chunk.text)

    def rank_key(r: VectorSearchResult) -> tuple[int, float]:
        chunk = chunk_map.get(r.chunk_id)
        return (keyword_score(chunk), r.score)

    ranked = sorted(results, key=rank_key, reverse=True)
    best_kw, best_vec = rank_key(ranked[0])

    if best_kw == 0 and best_vec < min_score:
        return []

    filtered = [ranked[0]]
    for result in ranked[1:]:
        if len(filtered) >= max_chunks:
            break
        kw, vec = rank_key(result)
        best_kw_f, _ = rank_key(filtered[0])
        if kw >= best_kw_f - 1 or vec >= best_vec - relative_gap:
            filtered.append(result)

    return filtered
