import re

GREETING_PATTERN = re.compile(
    r"^(?:hello|hi|hey|good morning|good afternoon)[\s!.?,]*$",
    re.IGNORECASE,
)


def is_greeting(text: str) -> bool:
    return bool(GREETING_PATTERN.match(text.strip()))


def is_too_vague(text: str) -> bool:
    """Very short non-question messages unlikely to be document queries."""
    cleaned = text.strip()
    return len(cleaned) < 4 and not cleaned.endswith("?")
