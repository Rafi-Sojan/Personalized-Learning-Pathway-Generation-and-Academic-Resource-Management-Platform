from .text_cleaner import clean_text


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "briefly", "by", "describe", "discuss",
    "explain", "for", "from", "how", "in", "is", "list", "of", "on", "or", "the", "to",
    "using", "what", "when", "where", "which", "with",
}


def _topic_tokens(text: str) -> list[str]:
    """Normalize lightweight word variants while excluding common exam-command words."""
    tokens: list[str] = []
    for token in clean_text(text).split():
        if token in _STOP_WORDS:
            continue
        if len(token) > 5 and token.endswith("ies"):
            token = f"{token[:-3]}y"
        elif len(token) > 5 and token.endswith("ing"):
            token = token[:-3]
        elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        tokens.append(token)
    return tokens


def similarity(left: str, right: str) -> float:
    """Return rounded Jaccard similarity between normalized token sets."""
    a, b = set(clean_text(left).split()), set(clean_text(right).split())
    return round(len(a & b) / len(a | b), 4) if a | b else 0.0


def topic_similarity(prompt: str, concept_name: str) -> float:
    """Score how completely a question covers the meaningful tokens of one syllabus concept."""
    prompt_tokens = _topic_tokens(prompt)
    concept_tokens = _topic_tokens(concept_name)
    if not prompt_tokens or not concept_tokens:
        return 0.0
    prompt_set, concept_set = set(prompt_tokens), set(concept_tokens)
    overlap = prompt_set & concept_set
    coverage = len(overlap) / len(concept_set)
    jaccard = len(overlap) / len(prompt_set | concept_set)
    phrase = " ".join(concept_tokens) in " ".join(prompt_tokens)
    return round(max(0.95 if phrase and len(concept_tokens) > 1 else 0.0, coverage * 0.8 + jaccard * 0.2), 4)
