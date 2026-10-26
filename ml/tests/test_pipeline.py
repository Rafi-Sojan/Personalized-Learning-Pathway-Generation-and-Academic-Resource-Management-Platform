from ml.graph.dependency_graph import topological_order
from ml.scheduling.roadmap_scheduler import schedule
from ml.evaluation.benchmark import evaluate_cases


def test_graph_order() -> None:
    ordered = topological_order({"functions": ["control-flow"], "control-flow": ["variables"], "variables": []})
    assert ordered == ["variables", "control-flow", "functions"]


def test_schedule() -> None:
    assert schedule([{"id": "a", "difficulty": 1}])[0]["minutes"] > 0


def test_evaluation_benchmark() -> None:
    result = evaluate_cases([{"mapping": {"predicted": ["a"], "expected": ["a"]}, "roadmap": {"completed": 1, "planned": 2}, "ranking": {"recommended": ["a"], "relevant": ["a"]}}])
    assert result["mapping_precision"] == 1.0
    assert result["roadmap_completion_rate"] == 0.5
    assert result["ranking_hit_rate"] == 1.0
