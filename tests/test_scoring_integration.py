from app.integrations.scoring_client import rank_concepts, score_concept


def test_scoring_prioritizes_learning_gap() -> None:
    """Verify the native scoring process prioritizes the larger learning gap."""
    assert score_concept(2, 0) > score_concept(2, 80)


def test_python_scoring_fallback_matches_native_readiness_contract() -> None:
    """Verify unavailable prerequisites reduce and reorder fallback priority like C++."""
    ready_score = score_concept(2, 0, prerequisite_ready=True)
    blocked_score = score_concept(2, 0, prerequisite_ready=False)
    assert blocked_score == ready_score * 0.25
    ranked = rank_concepts([
        {"id": "blocked", "difficulty": 5, "progress": 0, "prerequisite_ready": False},
        {"id": "ready", "difficulty": 2, "progress": 0, "prerequisite_ready": True},
    ])
    assert [item["id"] for item in ranked] == ["ready", "blocked"]
