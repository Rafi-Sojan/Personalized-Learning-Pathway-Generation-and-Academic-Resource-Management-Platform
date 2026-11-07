from ml.graph.dependency_graph import topological_order
from ml.scheduling.roadmap_scheduler import schedule
from ml.evaluation.benchmark import evaluate_cases
from ml.concept_mapping.semantic_matcher import topic_similarity
from ml.preprocessing.question_parser import parse_question_records, parse_questions
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


def test_question_parser_retains_page_number_subpart_marks_and_part() -> None:
    """Keep source coordinates and printed question metadata for later human review."""
    text = "PART A\n[[PAGE 2]]\n1. Define a variable. (2 marks)\nPART B\n[[PAGE 4]]\n2(a) Explain control flow. [10 marks]"
    records = parse_question_records(text, part_a_is_quiz=True)
    assert [(row.question_number, row.subpart, row.marks, row.source_page) for row in records] == [("1", None, 2.0, 2), ("2", "a", 10.0, 4)]
    assert [row.question_kind for row in records] == ["quiz", "main"]
    assert [row.question_kind for row in parse_question_records(text)] == ["main", "main"]


def test_question_parser_excludes_solutions_and_handles_rvce_table_numbering() -> None:
    """Parse mixed CIE/SEE numbering while excluding answer-scheme continuation pages."""
    text = """[[PAGE 1]]
CIE 2 : Question Paper
Sl.no. Part A Marks BT CO
1 What is routing? 02 L1 CO1
Part B
1a Explain shortest paths. 08 L2 CO1
[[PAGE 2]]
Scheme and Solution
1 Routing is path selection. 02
[[PAGE 3]]
1a This answer continues on another page.
[[PAGE 4]]
IV Semester B. E. Examinations Oct-2025
Instructions to candidates:
1. Answer all questions from Part A.
PART-A
1 1.1 Define a protocol. 01
PART-B
2 a Explain reliable delivery. 08
b Compare two approaches. 08
"""
    records = parse_question_records(text, part_a_is_quiz=True)
    assert [(row.source_page, row.question_number, row.subpart) for row in records] == [(1, "1", None), (1, "1", "a"), (4, "1.1", None), (4, "2", "a"), (4, "2", "b")]
    assert [row.question_kind for row in records] == ["quiz", "main", "quiz", "main", "main"]
    assert [row.assessment_type for row in records] == ["test", "test", "see", "see", "see"]
    assert [row.marks for row in records] == [2.0, 8.0, 1.0, 8.0, 8.0]


def test_topic_similarity_rewards_complete_concept_matches() -> None:
    """Prefer a specific syllabus phrase over generic words in an exam prompt."""
    prompt = "Analyze the distance vector routing protocol and its convergence problem."
    assert topic_similarity(prompt, "Distance Vector Routing") > topic_similarity(prompt, "Routing")


def test_rvce_catalog_has_provenance_and_normalized_program_codes() -> None:
    """Check the RVCE catalog includes source authority and unique program identities."""
    catalog = load_rvce_catalog()
    assert catalog["institution"]["short_name"] == "RVCE"
    assert len(catalog["program_schemes"]) == 15
    assert any(program["code"] == "ET" and "TE" in program["aliases"] for program in catalog["program_schemes"])
