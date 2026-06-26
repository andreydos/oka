MESSAGES = {
    "not_found": "Information was not found in the indexed documents.",
    "off_topic": (
        "I can only answer questions about uploaded documents. "
        "Please ask about the indexed documentation."
    ),
}


def get_messages() -> dict[str, str]:
    return MESSAGES
