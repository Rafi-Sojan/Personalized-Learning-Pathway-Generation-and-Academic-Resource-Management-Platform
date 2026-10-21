import re


def extract_topics(text: str) -> list[str]:
    """Return plausible syllabus topics from headings or non-empty lines."""
    lines = [re.sub(r"^[#\-\d.\s]+", "", line).strip() for line in text.splitlines()]
    return [line for line in lines if len(line) >= 3][:50]
