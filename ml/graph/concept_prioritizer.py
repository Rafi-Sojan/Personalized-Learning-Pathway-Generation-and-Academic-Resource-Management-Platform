"""Dependency-safe, evidence-aware prioritization for learner roadmaps."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import math


ROADMAP_ALGORITHM_VERSION = "rvce-evidence-priority-v2"


@dataclass(frozen=True)
class QuestionEvidence:
    """Represent one reviewed historical question used by roadmap ranking."""

    year: int
    marks: float | None = None


@dataclass(frozen=True)
class ConceptPriorityInput:
    """Contain bounded, explainable features for one incomplete concept."""

    concept_id: str
    name: str
    difficulty: int = 1
    mastery_score: float | None = None
    source_page: int | None = None
    unit_label: str | None = None
    unit_sequence: int | None = None
    evidence: tuple[QuestionEvidence, ...] = ()


@dataclass(frozen=True)
class PriorityDecision:
    """Return a concept's constrained order, score components, and rationale."""

    concept_id: str
    score: float
    evidence_score: float
    mastery_gap: float
    difficulty_score: float
    unlock_count: int
    reasons: tuple[str, ...]


def _clamp(value: float, lower: float, upper: float) -> float:
    """Bound a numeric feature before it contributes to a priority score."""
    return max(lower, min(upper, value))


def _evidence_score(evidence: Sequence[QuestionEvidence], current_year: int) -> float:
    """Normalize reviewed recurrence, recency, and marks without unbounded growth."""
    weighted = sum(
        (1 / (1 + max(current_year - item.year, 0) * 0.15))
        * (1 + _clamp(item.marks or 0.0, 0.0, 100.0) / 100)
        for item in evidence
    )
    return 1 - math.exp(-weighted / 3.0)


def _descendant_counts(concept_ids: set[str], prerequisites: Mapping[str, Sequence[str]]) -> dict[str, int]:
    """Count downstream concepts unlocked by each prerequisite node."""
    dependents: dict[str, set[str]] = {concept_id: set() for concept_id in concept_ids}
    for child, parents in prerequisites.items():
        if child not in concept_ids:
            continue
        for parent in parents:
            if parent in concept_ids and parent != child:
                dependents[parent].add(child)

    memo: dict[str, set[str]] = {}
    visiting: set[str] = set()

    def descendants(node: str) -> set[str]:
        """Collect reachable dependents and reject cycles before prioritization."""
        if node in visiting:
            raise ValueError("dependency graph contains a cycle")
        if node in memo:
            return memo[node]
        visiting.add(node)
        values: set[str] = set()
        for child in dependents[node]:
            values.add(child)
            values.update(descendants(child))
        visiting.remove(node)
        memo[node] = values
        return values

    return {concept_id: len(descendants(concept_id)) for concept_id in concept_ids}


def prioritize_with_dependencies(
    concepts: Iterable[ConceptPriorityInput],
    prerequisites: Mapping[str, Sequence[str]],
    *,
    current_year: int,
) -> list[PriorityDecision]:
    """Order concepts by unit and prerequisites, then rank each eligible layer by learning value.

    Source unit order and accepted prerequisites are hard constraints. Within
    the currently eligible unit, the score combines reviewed historical
    evidence (38%), learner mastery gap (30%), downstream unlock value (17%),
    and difficulty (15%).
    """
    by_id = {concept.concept_id: concept for concept in concepts}
    concept_ids = set(by_id)
    filtered_prerequisites = {
        concept_id: tuple(parent for parent in prerequisites.get(concept_id, ()) if parent in concept_ids)
        for concept_id in concept_ids
    }
    unlock_counts = _descendant_counts(concept_ids, filtered_prerequisites)
    max_unlock = max(unlock_counts.values(), default=0)
    features: dict[str, PriorityDecision] = {}
    for concept_id, concept in by_id.items():
        evidence_score = _evidence_score(concept.evidence, current_year)
        mastery = _clamp(concept.mastery_score if concept.mastery_score is not None else 0.0, 0.0, 100.0)
        mastery_gap = (100 - mastery) / 100
        difficulty_score = _clamp(float(concept.difficulty), 1.0, 5.0) / 5
        unlock_score = unlock_counts[concept_id] / max_unlock if max_unlock else 0.0
        score = 0.38 * evidence_score + 0.30 * mastery_gap + 0.17 * unlock_score + 0.15 * difficulty_score
        evidence_reason = (
            f"{len(concept.evidence)} verified historical questions"
            if concept.evidence
            else "no verified historical evidence"
        )
        features[concept_id] = PriorityDecision(
            concept_id=concept_id,
            score=round(score, 4),
            evidence_score=round(evidence_score, 4),
            mastery_gap=round(mastery_gap * 100, 2),
            difficulty_score=round(difficulty_score, 4),
            unlock_count=unlock_counts[concept_id],
            reasons=(
                evidence_reason,
                f"mastery gap {mastery_gap * 100:.0f}%",
                f"concept difficulty {int(_clamp(float(concept.difficulty), 1.0, 5.0))}/5",
                f"unlocks {unlock_counts[concept_id]} downstream concepts",
                f"priority score {score:.3f} ({ROADMAP_ALGORITHM_VERSION})",
            ),
        )

    remaining = set(concept_ids)
    ordered: list[PriorityDecision] = []
    while remaining:
        dependency_eligible = [
            concept_id
            for concept_id in remaining
            if not (set(filtered_prerequisites[concept_id]) & remaining)
        ]
        if not dependency_eligible:
            raise ValueError("dependency graph contains a cycle")
        
        sequenced: list[int] = []
        for concept_id in remaining:
            unit_sequence = by_id[concept_id].unit_sequence
            if unit_sequence is not None:
                sequenced.append(unit_sequence)
                
        if sequenced:
            first_unit = min(sequenced)
            eligible = [concept_id for concept_id in dependency_eligible if by_id[concept_id].unit_sequence == first_unit]
            if not eligible:
                # A legacy unsequenced prerequisite may legitimately unlock the
                # first source unit; otherwise the reviewed dependency conflicts
                # with the syllabus's hard teaching order.
                eligible = [concept_id for concept_id in dependency_eligible if by_id[concept_id].unit_sequence is None]
            if not eligible:
                raise ValueError("dependency graph conflicts with syllabus unit order")
        else:
            eligible = dependency_eligible
        eligible.sort(
            key=lambda concept_id: (
                -features[concept_id].score,
                by_id[concept_id].source_page or 0,
                (by_id[concept_id].unit_label or "").casefold(),
                by_id[concept_id].name.casefold(),
                concept_id,
            )
        )
        ordered.extend(features[concept_id] for concept_id in eligible)
        remaining.difference_update(eligible)
    return ordered


def prioritize(concepts: list[dict]) -> list[dict]:
    """Preserve the legacy dictionary API using the v2 feature scorer."""
    active = [item for item in concepts if item.get("status") != "completed"]
    completed = [item for item in concepts if item.get("status") == "completed"]
    inputs = [
        ConceptPriorityInput(
            concept_id=str(item.get("id", index)),
            name=str(item.get("name", item.get("id", index))),
            difficulty=int(item.get("difficulty", 1)),
            mastery_score=float(item["score"]) if item.get("score") is not None else None,
        )
        for index, item in enumerate(active)
    ]
    decisions = prioritize_with_dependencies(inputs, {}, current_year=0)
    by_identifier = {str(item.get("id", index)): item for index, item in enumerate(active)}
    return [by_identifier[decision.concept_id] for decision in decisions] + completed
