import re


def clean_text(text: str) -> str:
    """Lowercase text and replace punctuation with spaces for matching."""
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()
