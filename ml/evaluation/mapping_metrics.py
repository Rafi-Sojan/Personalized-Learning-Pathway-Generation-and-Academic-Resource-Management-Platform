def precision(predicted: set[str], expected: set[str]) -> float:
    return len(predicted & expected) / len(predicted) if predicted else 0.0
