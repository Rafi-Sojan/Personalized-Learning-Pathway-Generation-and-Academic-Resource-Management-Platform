from app.integrations.scoring_client import score_concept


def test_scoring_prioritizes_learning_gap() -> None:
    assert score_concept(2, 0) > score_concept(2, 80)
