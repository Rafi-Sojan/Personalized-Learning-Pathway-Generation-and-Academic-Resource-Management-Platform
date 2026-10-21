from ml.graph.dependency_graph import topological_order
from ml.scheduling.roadmap_scheduler import schedule


def test_graph_order() -> None:
    ordered = topological_order({"functions": ["control-flow"], "control-flow": ["variables"], "variables": []})
    assert ordered == ["variables", "control-flow", "functions"]


def test_schedule() -> None:
    assert schedule([{"id": "a", "difficulty": 1}])[0]["minutes"] > 0
