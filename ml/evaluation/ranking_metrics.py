def hit_rate(recommended: list[str], relevant: set[str], k: int = 5) -> float:
    return float(bool(set(recommended[:k]) & relevant))
