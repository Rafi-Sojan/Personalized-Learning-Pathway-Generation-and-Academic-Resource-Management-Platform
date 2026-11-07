from ml.evaluation.chronological_ranking import evaluate_chronological_frequency


def test_chronological_frequency_never_uses_held_out_year() -> None:
    """Use only earlier paper years when ranking concepts for each held-out year."""
    result = evaluate_chronological_frequency([
        {"year": 2022, "concept_id": "graphs"},
        {"year": 2022, "concept_id": "graphs"},
        {"year": 2023, "concept_id": "trees"},
        {"year": 2024, "concept_id": "graphs"},
        {"year": 2024, "concept_id": "trees"},
        {"year": 2024, "concept_id": None},
        {"year": 2024, "concept_id": "unreviewed", "review_status": "pending_review"},
    ], k=2)
    assert result["evaluation_years"] == 2
    assert result["by_year"] == [
        {"year": 2023, "history_years": 1, "hit_rate_at_k": 0.0, "ndcg_at_k": 0.0},
        {"year": 2024, "history_years": 2, "hit_rate_at_k": 1.0, "ndcg_at_k": 1.0},
    ]
