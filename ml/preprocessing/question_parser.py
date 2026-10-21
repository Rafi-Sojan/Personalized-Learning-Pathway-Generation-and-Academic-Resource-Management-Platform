import re


def parse_questions(text: str) -> list[str]:
    return [match.strip() for match in re.split(r"\n\s*\n", text) if match.strip()]
