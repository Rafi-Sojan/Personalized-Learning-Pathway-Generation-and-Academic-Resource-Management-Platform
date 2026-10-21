from dataclasses import dataclass


@dataclass(frozen=True)
class TopicPrediction:
    label: str
    confidence: float


def classify(text: str) -> TopicPrediction:
    lowered = text.lower()
    labels = {"python": ["python", "function", "variable"], "data-structures": ["tree", "graph", "array"]}
    label, hits = max(((name, sum(word in lowered for word in words)) for name, words in labels.items()), key=lambda item: item[1], default=("general", 0))
    return TopicPrediction(label, min(1.0, 0.35 + hits * 0.2))
