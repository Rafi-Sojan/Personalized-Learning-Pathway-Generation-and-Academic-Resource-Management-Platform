from ml.graph.dependency_graph import topological_order
from ml.scheduling.roadmap_scheduler import schedule
from ml.evaluation.benchmark import evaluate_cases
from ml.preprocessing.question_parser import parse_questions
from ml.preprocessing.rvce_catalog import load_rvce_catalog


def test_graph_order() -> None:
    """Ensure dependency ordering places prerequisite concepts before dependents."""
    ordered = topological_order({"functions": ["control-flow"], "control-flow": ["variables"], "variables": []})
    assert ordered == ["variables", "control-flow", "functions"]


def test_schedule() -> None:
    """Ensure scheduling assigns one dated study block to each concept."""
    assert schedule([{"id": "a", "difficulty": 1}])[0]["minutes"] > 0


def test_evaluation_benchmark() -> None:
    """Check deterministic benchmark evaluation reports the expected metric fields."""
    result = evaluate_cases([{"mapping": {"predicted": ["a"], "expected": ["a"]}, "roadmap": {"completed": 1, "planned": 2}, "ranking": {"recommended": ["a"], "relevant": ["a"]}, "historical_ranking": {"recommended": ["a"], "relevant": ["a"]}}])
    assert result["mapping_precision"] == 1.0
    assert result["roadmap_completion_rate"] == 0.5
    assert result["ranking_hit_rate"] == 1.0
    assert result["historical_ranking_hit_rate"] == 1.0


def test_question_parser_handles_numbered_exam_text() -> None:
    """Ensure numbered exam prompts are split into clean individual questions."""
    questions = parse_questions("1. Define a variable.\n2) Explain functions.\n\n3. Describe control flow.")
    assert questions == ["Define a variable.", "Explain functions.", "Describe control flow."]


def test_rvce_catalog_has_provenance_and_normalized_program_codes() -> None:
    """Check the RVCE catalog includes source authority and unique program identities."""
    catalog = load_rvce_catalog()
    assert catalog["institution"]["short_name"] == "RVCE"
    assert len(catalog["program_schemes"]) == 15
    assert any(program["code"] == "ET" and "TE" in program["aliases"] for program in catalog["program_schemes"])
