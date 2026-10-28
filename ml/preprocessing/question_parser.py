import re


def parse_questions(text: str) -> list[str]:
    """Split common exam-paper formats into bounded question prompts."""
    normalized = text.replace("\r\n", "\n").strip()
    blocks = re.split(r"\n\s*\n|(?=^\s*(?:Q(?:uestion)?\s*)?\d+[.)])", normalized, flags=re.MULTILINE | re.IGNORECASE)
    questions: list[str] = []
    for block in blocks:
        cleaned = re.sub(r"^\s*(?:Q(?:uestion)?\s*)?\d+[.)]\s*", "", block.strip(), flags=re.IGNORECASE)
        if cleaned:
            questions.append(cleaned[:20000])
    return questions[:1000]
