"""Language-agnostic keyword overlap for retrieval reranking and citations."""

import re

_TERM_RE = re.compile(r"[a-zA-Z0-9_-]{4,}")
_STEM_LENGTHS = (6, 5, 4)


def extract_terms(text: str) -> list[str]:
    return _TERM_RE.findall(text.lower())


def term_stems(term: str) -> list[str]:
    """Prefix stems for approximate morphological overlap."""
    return [term[:length] for length in _STEM_LENGTHS if len(term) >= length]


def keyword_overlap(query: str, text: str) -> int:
    text_lower = text.lower()
    score = 0

    for term in extract_terms(query):
        if term in text_lower:
            score += 2
            continue
        if any(stem in text_lower for stem in term_stems(term)):
            score += 1

    return score


def search_terms_for_quote(query: str) -> list[str]:
    """Terms and stems used to locate the best sentence inside a chunk."""
    expanded: list[str] = []
    for term in extract_terms(query):
        expanded.append(term)
        expanded.extend(term_stems(term))
    return list(dict.fromkeys(expanded))
