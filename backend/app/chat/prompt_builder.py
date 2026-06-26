import re

NOT_FOUND_MESSAGE = "Information was not found in the indexed documents."

_LIST_QUESTION_PATTERN = re.compile(
    r"\b(?:all|every|list|enumerate|how many|which|other|others|more|remaining)\b",
    re.IGNORECASE,
)


def is_list_question(question: str) -> bool:
    return bool(_LIST_QUESTION_PATTERN.search(question.strip()))


def build_system_prompt(not_found_message: str, *, list_question: bool = False) -> str:
    length_rule = (
        "- Enumerate every matching item from the excerpts.\n"
        "- Use Markdown list formatting: one item per bullet, each on its own line.\n"
        "- Put supporting details on indented sub-bullets under each item.\n"
        "- Add a blank line between items. Never put multiple items on the same line.\n"
        if list_question
        else "- Be concise: 1-3 sentences maximum.\n"
    )
    return (
        "You are an offline knowledge assistant. Answer ONLY using the provided document excerpts. "
        "Rules:\n"
        "- Respond in English.\n"
        "- Keep original proper names, identifiers, and technical terms unchanged.\n"
        f"{length_rule}"
        "- Do NOT greet the user or engage in small talk.\n"
        "- If excerpts do not contain the answer, respond exactly with: "
        f'"{not_found_message}"\n'
        "- Do not invent facts. Do not use outside knowledge."
    )


def build_user_prompt(
    question: str,
    contexts: list[dict],
    *,
    list_question: bool = False,
) -> str:
    context_blocks: list[str] = []
    for i, ctx in enumerate(contexts, start=1):
        header = f"[Source {i}: {ctx['document_name']}"
        if ctx.get("section"):
            header += f", section: {ctx['section']}"
        if ctx.get("page"):
            header += f", page {ctx['page']}"
        header += "]"
        context_blocks.append(f"{header}\n{ctx['text']}")

    context_text = "\n\n---\n\n".join(context_blocks)
    answer_hint = (
        "List every matching item. Format exactly like this example:\n"
        "- Item title — summary\n"
        "  - Detail: ...\n"
        "  - Detail: ...\n\n"
        "- Next item title — summary\n"
        "  - Detail: ...\n"
        "  - Detail: ...\n"
        "Use a blank line between items. Do not stop after the first match:"
        if list_question
        else "Be specific and brief:"
    )
    return (
        f"Document excerpts:\n\n{context_text}\n\n"
        f"Question: {question}\n\n"
        f"Answer in English using only the excerpts above. {answer_hint}"
    )
