from uuid import UUID

from app.knowledge.vector_models import VectorSearchResult


def build_search_queries(question: str) -> list[str]:
    cleaned = question.strip()
    return [cleaned] if cleaned else []


def merge_search_results(
    *result_sets: list[VectorSearchResult],
    limit: int,
) -> list[VectorSearchResult]:
    best: dict[UUID, VectorSearchResult] = {}
    for results in result_sets:
        for result in results:
            existing = best.get(result.chunk_id)
            if existing is None or result.score > existing.score:
                best[result.chunk_id] = result
    merged = sorted(best.values(), key=lambda item: item.score, reverse=True)
    return merged[:limit]


def build_retrieval_query(question: str, prior_user_messages: list[str], *, max_prior: int = 2) -> str:
    """Combine recent user turns so follow-ups inherit keywords from earlier questions."""
    current = question.strip()
    prior = [message.strip() for message in prior_user_messages if message.strip()][-max_prior:]
    if not prior:
        return current
    return f"{' '.join(prior)} {current}".strip()
