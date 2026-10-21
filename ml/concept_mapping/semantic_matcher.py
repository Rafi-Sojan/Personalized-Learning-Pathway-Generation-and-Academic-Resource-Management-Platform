from .text_cleaner import clean_text


def similarity(left: str, right: str) -> float:
    a, b = set(clean_text(left).split()), set(clean_text(right).split())
    return round(len(a & b) / len(a | b), 4) if a | b else 0.0
