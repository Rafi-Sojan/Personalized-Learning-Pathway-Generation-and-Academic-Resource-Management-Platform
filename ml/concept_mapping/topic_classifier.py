"""Taxonomy-driven topic classification built on the explainable matcher."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .semantic_matcher import ConceptDocument, ConceptMatcher


@dataclass(frozen=True)
class TopicPrediction:
    """Return the selected label, confidence, and abstention status."""

    label: str
    confidence: float
    status: str = "matched"
    alternatives: tuple[str, ...] = ()


def classify(text: str, taxonomy: Mapping[str, Sequence[str]] | None = None) -> TopicPrediction:
    """Classify text against a caller-supplied course taxonomy or abstain safely.

    A fixed Python/data-structures taxonomy is not valid across RVCE subjects.
    Callers therefore provide labels and their aliases/keywords from the current
    verified syllabus. No taxonomy means no evidence and returns ``unclassified``.
    """
    if not taxonomy:
        return TopicPrediction("unclassified", 0.0, "no_taxonomy")
    documents = [
        ConceptDocument(concept_id=label, name=label.replace("-", " "), aliases=tuple(aliases))
        for label, aliases in taxonomy.items()
        if label.strip()
    ]
    decision = ConceptMatcher(documents).match(text)
    alternatives = tuple(candidate.concept_id for candidate in decision.candidates[:3])
    return TopicPrediction(
        decision.concept_id or "unclassified",
        decision.confidence or 0.0,
        decision.status,
        alternatives,
    )
