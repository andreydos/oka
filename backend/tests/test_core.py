import pytest

from app.chat.citation_service import CitationService
from app.chat.prompt_builder import build_system_prompt, is_list_question
from app.chat.query_classifier import is_greeting
from app.chat.retrieval_filter import filter_search_results
from app.documents.document_formats import UnsupportedDocumentError, validate_document
from app.documents.document_parser import DocumentParser
from app.knowledge.chunking_service import ChunkingService
from app.documents.parsed_segment import ParsedSegment
from app.knowledge.vector_models import VectorSearchResult
from uuid import uuid4


def test_parse_plain_text():
    parser = DocumentParser()
    segments = parser.parse(b"Hello world", "text/plain", "test.txt")
    assert len(segments) == 1
    assert segments[0].text == "Hello world"


def test_rejects_png_renamed_as_plain_text():
    png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    validate_document("screenshot.png", "image/png", png_header)

    with pytest.raises(UnsupportedDocumentError, match="looks like an image"):
        DocumentParser().parse(png_header, "text/plain", "screenshot.txt")


def test_rejects_unsupported_gif():
    with pytest.raises(UnsupportedDocumentError, match="GIF"):
        validate_document("anim.gif", "image/gif", b"GIF89a" + b"\x00" * 20)


def test_parse_image_uses_ocr(monkeypatch):
    monkeypatch.setattr(
        "app.documents.document_parser.extract_text_from_image",
        lambda _content: "Architecture overview",
    )
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    segments = DocumentParser().parse(png, "image/png", "diagram.png")
    assert len(segments) == 1
    assert segments[0].text == "Architecture overview"
    assert segments[0].section == "OCR (English)"


def test_parse_markdown_headers():
    parser = DocumentParser()
    md = b"## Section A\nContent A\n\n### Section B\nContent B"
    segments = parser.parse(md, "text/plain", "test.md")
    assert len(segments) >= 2
    assert any(s.section and "Section" in s.section for s in segments)


def test_chunking_splits_long_text():
    chunker = ChunkingService(chunk_size=10, chunk_overlap=2)
    long_text = "word " * 100
    segments = [ParsedSegment(text=long_text, page=1)]
    chunks = chunker.chunk_segments(segments)
    assert len(chunks) > 1
    assert chunks[0].page == 1


def test_chunking_splits_numbered_list_entries():
    chunker = ChunkingService(chunk_size=200, chunk_overlap=10)
    text = (
        "1. Alpha entry — category A\n"
        "Details: first requirement, second requirement, third requirement.\n\n"
        "2. Beta entry — category B\n"
        "Details: first requirement, second requirement, third requirement.\n\n"
        "3. Gamma entry — category C\n"
        "Details: first requirement, second requirement, third requirement."
    )
    chunks = chunker.chunk_segments([ParsedSegment(text=text, page=1)])
    assert len(chunks) == 3
    assert all("entry" in chunk.text for chunk in chunks)


def test_build_retrieval_query_includes_prior_messages():
    from app.chat.retrieval_query import build_retrieval_query

    query = build_retrieval_query("any others?", ["open roles in Canada"])
    assert "Canada" in query
    assert "others" in query


def test_is_list_question_detection():
    assert is_list_question("which records match the filter?")
    assert is_list_question("show me all entries in section 2")
    assert is_list_question("any others?")
    assert not is_list_question("who wrote this document?")


def test_greeting_detection():
    assert is_greeting("hello")
    assert is_greeting("Hey!")
    assert not is_greeting("which sections mention exports?")


def test_get_messages_are_english():
    from app.chat.language_utils import get_messages

    messages = get_messages()
    assert messages["not_found"].startswith("Information")
    assert messages["off_topic"].startswith("I can only answer")


def test_system_prompt_is_english_only():
    prompt = build_system_prompt("Information was not found in the indexed documents.")
    assert "Respond in English" in prompt
    assert "same language" not in prompt


def test_merge_search_results_keeps_best_score_per_chunk():
    from app.chat.retrieval_query import merge_search_results

    chunk_a = uuid4()
    chunk_b = uuid4()
    doc = uuid4()
    first = [
        VectorSearchResult(chunk_a, doc, 1, None, 0, 0.61),
        VectorSearchResult(chunk_b, doc, 1, None, 1, 0.40),
    ]
    second = [
        VectorSearchResult(chunk_a, doc, 1, None, 0, 0.52),
        VectorSearchResult(chunk_b, doc, 1, None, 1, 0.78),
    ]
    merged = merge_search_results(first, second, limit=5)
    scores = {r.chunk_id: r.score for r in merged}
    assert scores[chunk_a] == 0.61
    assert scores[chunk_b] == 0.78


def test_filter_search_results_keeps_multiple_strong_keyword_matches():
    from app.db.models import DocumentChunk

    doc_id = uuid4()
    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=i,
            text=f"Record {i} — region north. Notes: alpha beta gamma.",
            page=1,
            section=None,
            token_count=20,
        )
        for i in range(3)
    ]
    results = [
        VectorSearchResult(chunks[i].id, doc_id, 1, None, i, 0.7 - i * 0.02)
        for i in range(3)
    ]
    filtered = filter_search_results(
        results,
        chunks,
        "records in north region",
        min_score=0.5,
        relative_gap=0.1,
        max_chunks=5,
    )
    assert len(filtered) == 3


def test_filter_search_results_keeps_top_relevant():
    results = [
        VectorSearchResult(uuid4(), uuid4(), 1, "a", 0, 0.72),
        VectorSearchResult(uuid4(), uuid4(), 2, "b", 1, 0.68),
        VectorSearchResult(uuid4(), uuid4(), 3, "c", 2, 0.55),
    ]
    filtered = filter_search_results(results, min_score=0.58, relative_gap=0.05, max_chunks=2)
    assert len(filtered) == 2
    assert filtered[0].score == 0.72


def test_keyword_overlap_uses_stems():
    from app.chat.keyword_utils import keyword_overlap

    assert keyword_overlap("billing exports", "The billing service handles exports.") >= 2
    assert keyword_overlap("billing exports", "The auth service handles sign-in.") == 0


def test_extract_relevant_quote():
    service = CitationService()
    text = (
        "Controllers handle HTTP. Services contain business logic. "
        "Integrations include exports for reporting and billing."
    )
    quote = service.extract_relevant_quote(text, "which modules handle exports?")
    assert "export" in quote.lower()


def test_citation_prefers_structured_bullet_over_intro():
    from app.db.models import DocumentChunk

    service = CitationService()
    doc_id = uuid4()
    intro_chunk = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        chunk_index=0,
        text=(
            "Platform overview for internal teams. "
            "Major areas include auth, billing, reporting, exports, and notifications."
        ),
        page=1,
        section="Intro",
        token_count=100,
    )
    detail_chunk = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        chunk_index=4,
        text="- **Billing** — invoices, payment providers\n- **Reporting** — dashboards, exports",
        page=3,
        section=None,
        token_count=50,
    )
    results = [
        VectorSearchResult(intro_chunk.id, doc_id, 1, "Intro", 0, 0.75),
        VectorSearchResult(detail_chunk.id, doc_id, 3, None, 4, 0.70),
    ]
    citations = service.build_citation_records(
        results, [intro_chunk, detail_chunk], "which modules are related to billing"
    )
    assert citations
    assert citations[0]["chunk_id"] == detail_chunk.id
    assert "billing" in citations[0]["quote"].lower()
