from ml.concept_mapping.semantic_matcher import similarity


def crosswalk(syllabus_topics: list[str], concepts: list[str], threshold: float = 0.2) -> dict[str, list[str]]:
    """Map each syllabus topic to concepts meeting the token-similarity threshold."""
    return {topic: [concept for concept in concepts if similarity(topic, concept) >= threshold] for topic in syllabus_topics}
