from ml.graph.dependency_graph import topological_order
from ml.scheduling.roadmap_scheduler import schedule
from ml.evaluation.benchmark import evaluate_cases
from ml.preprocessing.question_parser import parse_questions


def test_graph_order() -> None:
    ordered = topological_order({"functions": ["control-flow"], "control-flow": ["variables"], "variables": []})
    assert ordered == ["variables", "control-flow", "functions"]


def test_schedule() -> None:
    assert schedule([{"id": "a", "difficulty": 1}])[0]["minutes"] > 0


def test_evaluation_benchmark() -> None:
    result = evaluate_cases([{"mapping": {"predicted": ["a"], "expected": ["a"]}, "roadmap": {"completed": 1, "planned": 2}, "ranking": {"recommended": ["a"], "relevant": ["a"]}, "historical_ranking": {"recommended": ["a"], "relevant": ["a"]}}])
    assert result["mapping_precision"] == 1.0
    assert result["roadmap_completion_rate"] == 0.5
    assert result["ranking_hit_rate"] == 1.0
    assert result["historical_ranking_hit_rate"] == 1.0


def test_question_parser_handles_numbered_exam_text() -> None:
    questions = parse_questions("1. Define a variable.\n2) Explain functions.\n\n3. Describe control flow.")
    assert questions == ["Define a variable.", "Explain functions.", "Describe control flow."]
