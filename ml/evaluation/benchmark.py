from __future__ import annotations

from collections.abc import Iterable

from ml.evaluation.mapping_metrics import f1_score, precision, recall
from ml.evaluation.ranking_metrics import hit_rate, ndcg
from ml.evaluation.roadmap_metrics import completion_rate


def evaluate_cases(cases: Iterable[dict]) -> dict[str, float]:
    """Evaluate a JSON-compatible benchmark set with deterministic metrics."""
    case_list = list(cases)
    mapping_scores: list[float] = []
    mapping_recall_scores: list[float] = []
    mapping_f1_scores: list[float] = []
    roadmap_scores: list[float] = []
    ranking_scores: list[float] = []
    ranking_ndcg_scores: list[float] = []
    historical_ranking_scores: list[float] = []
    historical_ranking_ndcg_scores: list[float] = []
    for case in case_list:
        mapping = case.get("mapping")
        if mapping:
            predicted = set(mapping.get("predicted", []))
            expected = set(mapping.get("expected", []))
            mapping_scores.append(precision(predicted, expected))
            mapping_recall_scores.append(recall(predicted, expected))
            mapping_f1_scores.append(f1_score(predicted, expected))
        roadmap = case.get("roadmap")
        if roadmap:
            roadmap_scores.append(completion_rate(int(roadmap.get("completed", 0)), int(roadmap.get("planned", 0))))
        ranking = case.get("ranking")
        if ranking:
            recommended = list(ranking.get("recommended", []))
            relevant = set(ranking.get("relevant", []))
            k = int(ranking.get("k", 5))
            ranking_scores.append(hit_rate(recommended, relevant, k))
            ranking_ndcg_scores.append(ndcg(recommended, relevant, k))
        historical = case.get("historical_ranking")
        if historical:
            recommended = list(historical.get("recommended", []))
            relevant = set(historical.get("relevant", []))
            k = int(historical.get("k", 5))
            historical_ranking_scores.append(hit_rate(recommended, relevant, k))
            historical_ranking_ndcg_scores.append(ndcg(recommended, relevant, k))
    return {
        "mapping_precision": sum(mapping_scores) / len(mapping_scores) if mapping_scores else 0.0,
        "mapping_recall": sum(mapping_recall_scores) / len(mapping_recall_scores) if mapping_recall_scores else 0.0,
        "mapping_f1": sum(mapping_f1_scores) / len(mapping_f1_scores) if mapping_f1_scores else 0.0,
        "roadmap_completion_rate": sum(roadmap_scores) / len(roadmap_scores) if roadmap_scores else 0.0,
        "ranking_hit_rate": sum(ranking_scores) / len(ranking_scores) if ranking_scores else 0.0,
        "ranking_ndcg": sum(ranking_ndcg_scores) / len(ranking_ndcg_scores) if ranking_ndcg_scores else 0.0,
        "historical_ranking_hit_rate": sum(historical_ranking_scores) / len(historical_ranking_scores) if historical_ranking_scores else 0.0,
        "historical_ranking_ndcg": sum(historical_ranking_ndcg_scores) / len(historical_ranking_ndcg_scores) if historical_ranking_ndcg_scores else 0.0,
        "cases": float(len(case_list)),
    }
