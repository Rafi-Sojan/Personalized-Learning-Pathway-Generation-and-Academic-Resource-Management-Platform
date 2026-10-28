def precision(predicted: set[str], expected: set[str]) -> float:
    return len(predicted & expected) / len(predicted) if predicted else 0.0


def recall(predicted: set[str], expected: set[str]) -> float:
    return len(predicted & expected) / len(expected) if expected else 0.0


def f1_score(predicted: set[str], expected: set[str]) -> float:
    precision_score = precision(predicted, expected)
    recall_score = recall(predicted, expected)
    return 2 * precision_score * recall_score / (precision_score + recall_score) if precision_score + recall_score else 0.0
