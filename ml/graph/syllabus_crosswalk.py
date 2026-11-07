"""Conservative syllabus-to-concept crosswalk generation."""

from ml.concept_mapping.semantic_matcher import ConceptDocument, ConceptMatcher, MatcherConfig


def crosswalk(syllabus_topics: list[str], concepts: list[str], threshold: float = 0.2) -> dict[str, list[str]]:
    """Map each topic only when the best existing concept is strong and separated."""
    minimum = max(0.0, min(1.0, threshold))
    matcher = ConceptMatcher(
        [ConceptDocument(str(index), concept) for index, concept in enumerate(concepts)],
        MatcherConfig(minimum_score=minimum),
    )
    result: dict[str, list[str]] = {}
    for topic in syllabus_topics:
        decision = matcher.match(topic)
        result[topic] = [decision.label] if decision.concept_id is not None else []
    return result
