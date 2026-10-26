from __future__ import annotations

from collections.abc import Iterable

from ml.evaluation.mapping_metrics import precision
from ml.evaluation.ranking_metrics import hit_rate
from ml.evaluation.roadmap_metrics import completion_rate


def evaluate_cases(cases: Iterable[dict]) -> dict[str, float]:
    """Evaluate a JSON-compatible benchmark set with deterministic metrics."""
    case_list = list(cases)
    mapping_scores: list[float] = []
    roadmap_scores: list[float] = []
    ranking_scores: list[float] = []
    for case in case_list:
        mapping = case.get("mapping")
        if mapping:
            mapping_scores.append(precision(set(mapping.get("predicted", [])), set(mapping.get("expected", []))))
        roadmap = case.get("roadmap")
        if roadmap:
            roadmap_scores.append(completion_rate(int(roadmap.get("completed", 0)), int(roadmap.get("planned", 0))))
        ranking = case.get("ranking")
        if ranking:
            ranking_scores.append(hit_rate(list(ranking.get("recommended", [])), set(ranking.get("relevant", [])), int(ranking.get("k", 5))))
    return {
        "mapping_precision": sum(mapping_scores) / len(mapping_scores) if mapping_scores else 0.0,
        "roadmap_completion_rate": sum(roadmap_scores) / len(roadmap_scores) if roadmap_scores else 0.0,
        "ranking_hit_rate": sum(ranking_scores) / len(ranking_scores) if ranking_scores else 0.0,
        "cases": float(len(case_list)),
    }
