def score_concept(difficulty: int, progress: float) -> float:
    """Fallback implementation matching the C++ engine's simple scoring contract."""
    return round((difficulty * 20) + max(0, 100 - progress) * 0.6, 2)
