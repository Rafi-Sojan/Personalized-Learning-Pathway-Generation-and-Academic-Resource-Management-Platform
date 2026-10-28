def hit_rate(recommended: list[str], relevant: set[str], k: int = 5) -> float:
    return float(bool(set(recommended[:k]) & relevant))


def ndcg(recommended: list[str], relevant: set[str], k: int = 5) -> float:
    """Compute binary-relevance NDCG for a top-k recommendation list."""
    import math

    ranked = recommended[:k]
    dcg = sum((1.0 / math.log2(index + 2)) for index, item in enumerate(ranked) if item in relevant)
    ideal_hits = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    return dcg / ideal_dcg if ideal_dcg else 0.0
