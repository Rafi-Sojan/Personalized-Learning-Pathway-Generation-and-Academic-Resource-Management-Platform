def estimate_minutes(difficulty: int, confidence: float = 0.5) -> int:
    return max(15, round(20 + difficulty * 12 + (1 - confidence) * 20))
