import re
from uuid import UUID

from app.chat.keyword_utils import keyword_overlap, search_terms_for_quote
from app.config import settings
from app.db.models import Document, DocumentChunk
from app.knowledge.vector_models import VectorSearchResult


class CitationService:
    def build_citation_records(
        self,
        search_results: list[VectorSearchResult],
        chunks: list[DocumentChunk],
        query: str,
        max_citations: int | None = None,
    ) -> list[dict]:
        max_citations = max_citations or settings.max_citations
        chunk_map = {c.id: c for c in chunks}

        candidates: list[tuple[int, int, float, DocumentChunk, str, VectorSearchResult]] = []
        for result in search_results:
            chunk = chunk_map.get(result.chunk_id)
            if not chunk:
                continue
            kw = self._keyword_score(query, chunk)
            if kw == 0:
                continue
            quote = self.extract_relevant_quote(chunk.text, query)
            quote_score = self._quote_match_score(query, quote)
            if quote_score == 0:
                continue
            candidates.append((quote_score, kw, result.score, chunk, quote, result))

        candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)

        citations: list[dict] = []
        for _, _, vec_score, chunk, quote, result in candidates:
            if len(citations) >= max_citations:
                break
            citations.append(
                {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "page": chunk.page,
                    "section": chunk.section,
                    "quote": quote,
                    "score": round(vec_score, 3),
                }
            )
        return citations

    def _keyword_score(self, query: str, chunk: DocumentChunk | None) -> int:
        if not chunk:
            return 0
        return keyword_overlap(query, self._normalize_text(chunk.text))

    def _quote_match_score(self, query: str, quote: str) -> int:
        terms = search_terms_for_quote(query)
        quote_lower = quote.lower()
        score = sum(1 for term in terms if term in quote_lower)

        if re.search(r"\*\*[^*]+\*\*\s*—", quote):
            score += 3

        if len(quote) > 160 and score <= 2:
            score -= 2

        return max(score, 0)

    def extract_relevant_quote(self, text: str, query: str, max_length: int = 220) -> str:
        """Pick the sentence(s) from a chunk that best match the question."""
        text = self._normalize_text(text)
        search_terms = search_terms_for_quote(query)
        if not search_terms:
            return self._trim(text, max_length)

        sentences = re.split(r"(?<=[.!?])\s+|\n+|(?=\s*-\s+\*\*)", text)
        scored: list[tuple[int, str]] = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
            sentence_lower = sentence.lower()
            overlap = sum(1 for term in search_terms if term in sentence_lower)
            if overlap > 0:
                bonus = 3 if re.search(r"\*\*[^*]+\*\*\s*—", sentence) else 0
                scored.append((overlap + bonus, sentence))

        if not scored:
            return self._trim(text, max_length)

        scored.sort(key=lambda item: (item[0], -len(item[1])), reverse=True)
        quote = scored[0][1]
        return self._trim(quote, max_length)

    def to_response(
        self,
        citation_records: list[dict],
        documents: dict[UUID, Document],
    ) -> list[dict]:
        responses: list[dict] = []
        for c in citation_records:
            doc = documents.get(c["document_id"])
            responses.append(
                {
                    "document_id": c["document_id"],
                    "document_name": doc.filename if doc else "Unknown",
                    "chunk_id": c["chunk_id"],
                    "page": c.get("page"),
                    "section": c.get("section"),
                    "quote": c["quote"],
                }
            )
        return responses

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.split())

    @staticmethod
    def _trim(text: str, max_length: int) -> str:
        text = " ".join(text.split())
        if len(text) <= max_length:
            return text
        return text[: max_length - 3].rstrip() + "..."
