"""Regression coverage for the explainable v2 matching and prioritization engine."""

import pytest

from ml.concept_mapping.concept_identity import source_concept_identity, unique_name_keys
from ml.concept_mapping.mapping_validator import validate_mapping
from ml.concept_mapping.semantic_matcher import ConceptDocument, ConceptMatcher, MATCHER_VERSION, MatcherConfig
from ml.concept_mapping.topic_classifier import classify
from ml.evaluation.concept_matching import evaluate_concept_matching
from ml.graph.concept_prioritizer import ConceptPriorityInput, QuestionEvidence, prioritize_with_dependencies
from ml.graph.dependency_graph import topological_order
from ml.graph.syllabus_crosswalk import crosswalk
from ml.preprocessing.pdf_extractor import extract_text


def test_matcher_prefers_specific_phrase_over_generic_parent() -> None:
    """Use corpus rarity and full phrase evidence to select the precise topic."""
    matcher = ConceptMatcher([
        ConceptDocument("routing", "Routing"),
        ConceptDocument("distance-vector", "Distance Vector Routing"),
        ConceptDocument("link-state", "Link State Routing"),
    ])
    decision = matcher.match("Analyze distance vector routing and its convergence problem.")
    assert decision.status == "matched"
    assert decision.concept_id == "distance-vector"
    assert decision.model_version == MATCHER_VERSION
    assert decision.candidates[0].evidence[0] == "exact syllabus phrase"


def test_matcher_expands_acronyms_and_abstains_on_multi_topic_question() -> None:
    """Recognize derived acronyms but avoid choosing between two equally supported topics."""
    matcher = ConceptMatcher([
        ConceptDocument("cnn", "Convolutional Neural Networks"),
        ConceptDocument("rnn", "Recurrent Neural Networks"),
    ])
    assert matcher.match("Explain CNN feature maps.").concept_id == "cnn"
    ambiguous = matcher.match("Compare CNN and RNN architectures.")
    assert ambiguous.status == "ambiguous"
    assert ambiguous.concept_id is None
    assert {item.concept_id for item in ambiguous.candidates[:2]} == {"cnn", "rnn"}


def test_matcher_uses_parent_context_for_repeated_labels() -> None:
    """Separate same-named concepts when their printed parent context is present."""
    matcher = ConceptMatcher([
        ConceptDocument("database", "Normalization", parent_name="Relational Database Design"),
        ConceptDocument("machine-learning", "Normalization", parent_name="Machine Learning Preprocessing"),
    ])
    assert matcher.match("Explain database normalization up to third normal form.").concept_id == "database"
    assert matcher.match("Explain normalization.").status == "ambiguous"


def test_matcher_recovers_minor_ocr_damage_but_rejects_unrelated_text() -> None:
    """Use character evidence for OCR errors without forcing an unrelated mapping."""
    matcher = ConceptMatcher([
        ConceptDocument("dijkstra", "Dijkstra Algorithm"),
        ConceptDocument("bellman-ford", "Bellman Ford Algorithm"),
    ])
    assert matcher.match("Explain the Djikstra algoritm.").concept_id == "dijkstra"
    unrelated = matcher.match("Discuss transport-layer congestion control.")
    assert unrelated.concept_id is None
    assert unrelated.status in {"low_confidence", "no_evidence"}


def test_matcher_exact_phrases_require_token_boundaries() -> None:
    """Prevent short technical labels from matching inside unrelated words."""
    matcher = ConceptMatcher([
        ConceptDocument("os", "OS"),
        ConceptDocument("dbms", "Database Management Systems"),
    ])
    decision = matcher.match("Discuss cost estimation techniques.")
    assert decision.concept_id is None
    assert decision.status in {"low_confidence", "no_evidence"}
    assert all("exact syllabus phrase" not in candidate.evidence for candidate in decision.candidates)


def test_matcher_bounds_untrusted_prompt_scoring() -> None:
    """Ignore evidence beyond the configured scoring window instead of doing unbounded work."""
    matcher = ConceptMatcher(
        [ConceptDocument("os", "Operating Systems")],
        MatcherConfig(max_prompt_tokens=8),
    )
    assert matcher.match("operating systems " + "padding " * 20).concept_id == "os"
    outside_window = matcher.match("padding " * 8 + " operating systems")
    assert outside_window.concept_id is None


def test_source_identity_preserves_same_label_in_different_hierarchies() -> None:
    """Prevent repeated syllabus labels from collapsing across units or parents."""
    first = source_concept_identity("Applications", "Unit I", "Graphs")
    second = source_concept_identity("Applications", "Unit IV", "Neural Networks")
    assert first != second
    assert unique_name_keys(["Routing", "Applications", "Applications"]) == {"routing"}


def test_priority_engine_respects_prerequisites_and_rewards_unlock_value() -> None:
    """Keep hard dependencies while favoring a foundation that unlocks more work."""
    concepts = [
        ConceptPriorityInput("foundation", "Foundation", difficulty=2, mastery_score=20),
        ConceptPriorityInput("isolated", "Isolated", difficulty=2, mastery_score=20),
        ConceptPriorityInput("child-a", "Child A", difficulty=3, evidence=(QuestionEvidence(2026, 10),)),
        ConceptPriorityInput("child-b", "Child B", difficulty=3),
    ]
    decisions = prioritize_with_dependencies(
        concepts,
        {"child-a": ["foundation"], "child-b": ["foundation"]},
        current_year=2026,
    )
    assert decisions[0].concept_id == "foundation"
    assert decisions[0].unlock_count == 2
    assert next(index for index, item in enumerate(decisions) if item.concept_id == "child-a") > 0


def test_priority_engine_rejects_cycles() -> None:
    """Fail closed when accepted prerequisite edges form a directed cycle."""
    concepts = [ConceptPriorityInput("a", "A"), ConceptPriorityInput("b", "B")]
    with pytest.raises(ValueError, match="cycle"):
        prioritize_with_dependencies(concepts, {"a": ["b"], "b": ["a"]}, current_year=2026)


def test_matching_evaluator_computes_predictions_from_prompts() -> None:
    """Measure the engine itself instead of accepting pre-filled predictions."""
    result = evaluate_concept_matching([
        {
            "prompt": "Explain CNN architecture.",
            "concepts": [
                {"id": "cnn", "name": "Convolutional Neural Networks"},
                {"id": "rnn", "name": "Recurrent Neural Networks"},
            ],
            "expected": "cnn",
            "expected_status": "matched",
        },
        {
            "prompt": "Compare CNN and RNN.",
            "concepts": [
                {"id": "cnn", "name": "Convolutional Neural Networks"},
                {"id": "rnn", "name": "Recurrent Neural Networks"},
            ],
            "expected": None,
            "expected_status": "ambiguous",
        },
    ])
    assert result["matcher_accuracy"] == 1.0
    assert result["matcher_precision"] == 1.0
    assert result["matcher_abstention_accuracy"] == 1.0


def test_classifier_requires_a_course_taxonomy() -> None:
    """Avoid applying a fabricated global subject taxonomy across RVCE courses."""
    assert classify("Explain distance vector routing").status == "no_taxonomy"
    prediction = classify(
        "Explain distance vector routing convergence.",
        {"computer-networks": ["distance vector routing"], "databases": ["normal forms"]},
    )
    assert prediction.label == "computer-networks"
    assert prediction.status == "matched"


def test_crosswalk_and_validator_fail_closed_on_ambiguous_or_invalid_rows() -> None:
    """Generate one conservative match and report malformed mapping relationships."""
    assert crosswalk(["Distance Vector Routing"], ["Routing", "Distance Vector Routing"])["Distance Vector Routing"] == ["Distance Vector Routing"]
    errors = validate_mapping(
        {"Routing": ["Routing", "Unknown", "Unknown"]},
        valid_targets={"Distance Vector Routing"},
    )
    assert any("self mapping" in error for error in errors)
    assert any("duplicate targets" in error for error in errors)
    assert any("unknown targets" in error for error in errors)


def test_dependency_order_is_stable_and_rejects_self_cycles() -> None:
    """Produce deterministic independent-node ordering and reject invalid edges."""
    assert topological_order({"b": [], "a": [], "c": ["a"]}) == ["a", "b", "c"]
    with pytest.raises(ValueError, match="self-cycle"):
        topological_order({"a": ["a"]})


def test_plain_text_extraction_is_bounded(tmp_path) -> None:
    """Apply the same character ceiling to offline text fixtures as to PDFs."""
    source = tmp_path / "syllabus.txt"
    source.write_text("abcdefghij", encoding="utf-8")
    assert extract_text(source, max_chars=5) == "abcde"
