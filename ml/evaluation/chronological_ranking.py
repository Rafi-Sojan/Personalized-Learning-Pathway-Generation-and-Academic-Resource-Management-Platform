"""Leakage-safe year-forward evaluation for historical question frequency rankings."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping

from ml.evaluation.ranking_metrics import hit_rate, ndcg


def evaluate_chronological_frequency(
    records: Iterable[Mapping[str, object]],
    *,
    year_key: str = "year",
    concept_key: str = "concept_id",
    k: int = 5,
) -> dict[str, object]:
    """Rank topics using only earlier years and measure recall against each next year.

    Every evaluation year is held out in turn. Questions from that year never
    contribute to their own ranking. Unmapped records and malformed years are
    ignored so the metric represents evidence tied to a known syllabus concept.
    """
    by_year: dict[int, list[str]] = {}
    for row in records:
        if "review_status" in row and row.get("review_status") != "verified":
            continue
        raw_year = row.get(year_key)
        raw_concept = row.get(concept_key)
        try:
            year = int(raw_year)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if isinstance(raw_concept, str) and raw_concept.strip():
            by_year.setdefault(year, []).append(raw_concept.strip())

    years = sorted(by_year)
    evaluations: list[dict[str, float | int]] = []
    for held_out_year in years[1:]:
        historical = Counter(
            concept
            for year in years
            if year < held_out_year
            for concept in by_year[year]
        )
        ranked = [concept for concept, _ in sorted(historical.items(), key=lambda pair: (-pair[1], pair[0]))]
        relevant = set(by_year[held_out_year])
        evaluations.append({
            "year": held_out_year,
            "history_years": sum(year < held_out_year for year in years),
            "hit_rate_at_k": hit_rate(ranked, relevant, k),
            "ndcg_at_k": ndcg(ranked, relevant, k),
        })

    count = len(evaluations)
    return {
        "evaluation_years": count,
        "k": k,
        "mean_hit_rate_at_k": sum(item["hit_rate_at_k"] for item in evaluations) / count if count else 0.0,
        "mean_ndcg_at_k": sum(item["ndcg_at_k"] for item in evaluations) / count if count else 0.0,
        "by_year": evaluations,
        "method": "expanding_window_frequency",
    }
