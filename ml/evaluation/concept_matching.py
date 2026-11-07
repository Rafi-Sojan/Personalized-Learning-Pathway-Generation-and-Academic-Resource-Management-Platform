"""Offline metrics for computed question-to-concept matching decisions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from ml.concept_mapping.semantic_matcher import ConceptDocument, ConceptMatcher


def _strings(value: object) -> tuple[str, ...]:
    """Convert a JSON value into a tuple of non-empty strings."""
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(item for item in value if isinstance(item, str) and item)
    return ()


def _concepts(value: object) -> list[ConceptDocument]:
    """Validate and convert benchmark concept dictionaries into matcher documents."""
    if not isinstance(value, list):
        raise ValueError("concept_matching.concepts must be a list")
    concepts: list[ConceptDocument] = []
    for row in value:
        if not isinstance(row, Mapping):
            raise ValueError("each concept_matching concept must be an object")
        concept_id, name = row.get("id"), row.get("name")
        if not isinstance(concept_id, str) or not concept_id or not isinstance(name, str) or not name:
            raise ValueError("each concept_matching concept requires string id and name")
        aliases = _strings(row.get("aliases", ()))
        parent_name = row.get("parent_name") if isinstance(row.get("parent_name"), str) else None
        unit_label = row.get("unit_label") if isinstance(row.get("unit_label"), str) else None
        concepts.append(ConceptDocument(concept_id, name, aliases, parent_name, unit_label))
    return concepts


def evaluate_concept_matching(cases: Iterable[Mapping[str, object]]) -> dict[str, float]:
    """Compute selective matching quality and abstention behavior from raw prompts.

    ``expected`` accepts one concept ID, a list of acceptable IDs, or ``null``
    when the correct behavior is to abstain. Optional ``expected_status`` checks
    whether the matcher explained the decision using the intended status.
    """
    total = 0
    expected_mapped = 0
    accepted = 0
    correct_accepted = 0
    correct_overall = 0
    expected_abstentions = 0
    correct_abstentions = 0
    statuses_checked = 0
    statuses_correct = 0
    reciprocal_rank_sum = 0.0

    for case in cases:
        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("concept_matching.prompt must be a non-empty string")
        matcher = ConceptMatcher(_concepts(case.get("concepts")))
        decision = matcher.match(prompt)
        expected = set(_strings(case.get("expected")))
        total += 1
        if expected:
            expected_mapped += 1
            if decision.concept_id in expected:
                correct_overall += 1
            for rank, candidate in enumerate(decision.candidates, start=1):
                if candidate.concept_id in expected:
                    reciprocal_rank_sum += 1 / rank
                    break
        else:
            expected_abstentions += 1
            if decision.concept_id is None:
                correct_abstentions += 1
                correct_overall += 1
        if decision.concept_id is not None:
            accepted += 1
            if decision.concept_id in expected:
                correct_accepted += 1
        expected_status = case.get("expected_status")
        if isinstance(expected_status, str):
            statuses_checked += 1
            statuses_correct += int(decision.status == expected_status)

    precision = correct_accepted / accepted if accepted else 0.0
    recall = correct_accepted / expected_mapped if expected_mapped else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "matcher_accuracy": correct_overall / total if total else 0.0,
        "matcher_precision": precision,
        "matcher_recall": recall,
        "matcher_f1": f1,
        "matcher_coverage": accepted / total if total else 0.0,
        "matcher_abstention_accuracy": correct_abstentions / expected_abstentions if expected_abstentions else 0.0,
        "matcher_status_accuracy": statuses_correct / statuses_checked if statuses_checked else 0.0,
        "matcher_mrr": reciprocal_rank_sum / expected_mapped if expected_mapped else 0.0,
        "matcher_cases": float(total),
    }
