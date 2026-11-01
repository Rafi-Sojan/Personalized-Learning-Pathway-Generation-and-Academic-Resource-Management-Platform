def estimate_minutes(difficulty: int, confidence: float = 0.5) -> int:
    """Estimate study time from difficulty and confidence with a 15-minute floor."""
    return max(15, round(20 + difficulty * 12 + (1 - confidence) * 20))
