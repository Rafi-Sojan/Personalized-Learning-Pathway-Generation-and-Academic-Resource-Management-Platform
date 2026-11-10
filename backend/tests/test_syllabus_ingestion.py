import pytest

from app.services.syllabus_service import (
    extract_course_profile,
    extract_declared_course_codes,
    extract_prerequisite_candidates,
    extract_syllabus_facts,
    extract_syllabus_topics,
    select_syllabus_course_section,
)


def test_syllabus_topic_extraction_retains_unit_and_page() -> None:
    """Keep syllabus topic wording and its printed page/unit for source review."""
    topics = extract_syllabus_topics("[[PAGE 7]]\nUNIT III\n1. Linear regression")
    assert len(topics) == 1
    assert topics[0].name == "Linear regression"
    assert topics[0].unit_label == "III"
    assert topics[0].source_page == 7


def test_rvce_2022_inline_unit_and_colon_subtopics() -> None:
    """Parse RVCE 2022 inline unit-hour headings and wrapped comma topic lists."""
    text = "[[PAGE 21]]\nUnit-I 09 Hrs.\nIntroduction:\nData Structure, Classifications of Data Structures\nPointers:\nPointer Declaration, Address of Operator\nUnit � II 09 Hrs.\nStacks and Queues:"
    topics = extract_syllabus_topics(text)
    assert topics[0].name == "Introduction"
    assert topics[0].unit_label == "I"
    assert topics[0].unit_hours == 9
    assert topics[1].name == "Data Structure"
    assert topics[1].record_type == "subtopic"
    assert topics[1].parent_label == "Introduction"
    assert topics[-1].unit_label == "II"


def test_labeled_syllabus_facts_remain_distinct_from_map_topics() -> None:
    """Retain outcomes and assessment policy as facts rather than concept nodes."""
    facts = extract_syllabus_facts("[[PAGE 2]]\nCourse Outcomes: CO1 Apply algorithms\nCIE assessment: Quiz and descriptive test")
    assert [(fact.record_type, fact.source_page) for fact in facts] == [("outcome", 2), ("assessment", 2)]


def test_prerequisite_candidates_require_explicit_syllabus_language() -> None:
    """Avoid proposing topic dependencies from adjacent syllabus topics alone."""
    candidates = extract_prerequisite_candidates("[[PAGE 8]]\nBayesian Networks requires Probability")
    assert len(candidates) == 1
    assert candidates[0].concept_name == "Bayesian Networks"
    assert candidates[0].prerequisite_name == "Probability"
    assert candidates[0].source_page == 8
    assert extract_prerequisite_candidates("[[PAGE 8]]\nProbability, Bayesian Networks") == []


def test_combined_scheme_is_scoped_to_the_selected_course_code() -> None:
    """Prevent one course map from absorbing units from adjacent RVCE subjects."""
    text = "[[PAGE 4]]\nCourse Code: AI233AI CIE: 100\nUnit-I 09 Hrs.\nData Structures\nCourse Code: AI234AI CIE: 100\nUnit-I 09 Hrs.\nCyber Physical Systems"
    selected = select_syllabus_course_section(text, "AI234AI")
    assert selected is not None
    topics = extract_syllabus_topics(selected)
    assert any(topic.name == "Cyber Physical Systems" for topic in topics)
    assert all(topic.name != "Data Structures" for topic in topics)
    assert select_syllabus_course_section(text, "AI235AT") == ""


def test_combined_scheme_accepts_wrapped_alias_course_codes() -> None:
    """Select a shared first-year course section through either printed alias."""
    text = """[[PAGE 4]]
Course
Code: CI125AIA / AI125AIA
Unit-I 09 Hrs.
Python Fundamentals
Course Code: MA211TA
Unit-I 09 Hrs.
Calculus
"""
    selected = select_syllabus_course_section(text, "AI125AIA")
    assert selected is not None
    assert "Python Fundamentals" in selected
    assert "Calculus" not in selected


def test_wrapped_unit_prose_becomes_a_heading_and_child_hierarchy() -> None:
    """Keep bold-style colon headings separate from wrapped comma-delimited subtopics."""
    text = """[[PAGE 16]]
Course Code: AI253IA CIE: 100
Unit-I 09 Hrs.
Neural Networks: Models of neurons, Network architectures. Learning Processes:
Supervised learning, Unsupervised learning
Unit-II 09 Hrs.
Convolutional Networks: Padding, Strides, Training: Loss functions, Regularization, Example: CNN classifier
Course Outcomes: CO1 Apply neural models
RUBRIC FOR SEMESTER END EXAMINATION
PART A 20 MARKS
"""
    topics = extract_syllabus_topics(text)
    assert [topic.name for topic in topics if topic.record_type == "topic"] == ["Neural Networks", "Learning Processes", "Convolutional Networks"]
    assert any(topic.name == "Training" and topic.parent_label == "Convolutional Networks" for topic in topics)
    assert any(topic.name == "CNN classifier" and topic.parent_label == "Convolutional Networks" for topic in topics)
    assert all(topic.name != "Example" for topic in topics)
    assert all("MARKS" not in topic.name.upper() and not topic.name.startswith("CO1") for topic in topics)


def test_declared_course_code_detection_uses_institutional_code_shapes() -> None:
    """Detect printed RVCE identities without mistaking IPv6 or CO labels for course codes."""
    text = "Course Code : AI253IA\nComputer Networks(21CS45)\nIPv6\nCO1"
    assert extract_declared_course_codes(text) == {"AI253IA", "21CS45"}


def test_course_profile_retains_aliases_modalities_units_and_cie_scope() -> None:
    """Extract reviewable planning facts without collapsing alias codes or assessment scope."""
    text = """[[PAGE 11]]
Course Code: CI125AIA / AI125AIA
Category: Professional Core
Credits L:T:P: 2:0:1
Total Hours: 30L + 30P + 30EL
CIE: 50 Marks SEE: 50 Marks
CIE Assessment: Quiz and tests
Unit-I Python Fundamentals 09 Hrs.
Variables and control flow
Unit-II Applied Python (For CIE Only) 06 Hrs.
Functions and files
PART B
Course Outcomes:
CO1 Develop Python programs for engineering problems.
"""
    profile = extract_course_profile(text, "CI125AIA", "Python Programming")
    assert set(profile.course_codes) == {"AI125AIA", "CI125AIA"}
    assert profile.course_type == "programming"
    assert profile.category == "Professional Core"
    assert profile.credit_allocation == {"lecture": 2.0, "tutorial": 0.0, "practical": 1.0}
    assert profile.modality_hours == {"lecture": 30.0, "tutorial": 0.0, "practical": 30.0, "experiential": 30.0}
    assert [(unit.sequence, unit.label, unit.assessment_scope) for unit in profile.units] == [
        (1, "I", "both"),
        (2, "II", "cie_only"),
    ]
    assert profile.assessment_format == "unitwise_theory"
    assert {"quiz", "test"}.issubset(profile.assessment_components)
    assert profile.cie_marks == "50"
    assert profile.see_marks == "50"
    assert profile.course_outcomes == ("CO1 Develop Python programs for engineering problems.",)


def test_course_profile_flags_workload_that_needs_academic_review() -> None:
    """Keep source inconsistencies visible instead of silently normalizing the syllabus book."""
    text = """Course Code: HS115YL
Credits L:T:P: 2:0:1
Total Hours: 30P
Unit-I Foundations 09 Hrs.
Unit-II Practice 09 Hrs.
Unit-III Demonstration 09 Hrs.
"""
    profile = extract_course_profile(text, "HS115YL", "Yoga")
    assert profile.course_type == "health_practice"
    assert any("does not reconcile" in issue for issue in profile.issues)
    assert any("unusually low" in issue for issue in profile.issues)


def test_topic_extraction_assigns_monotonic_unit_sequence() -> None:
    """Provide a machine-safe source order even when printed labels use mixed styles."""
    topics = extract_syllabus_topics("UNIT I 09 Hrs.\nBasics\nMODULE 2 06 Hrs.\nApplications")
    assert [(topic.name, topic.unit_sequence) for topic in topics] == [("Basics", 1), ("Applications", 2)]


@pytest.mark.parametrize(
    ("code", "title", "extra", "expected"),
    [
        ("MA211TA", "Engineering Mathematics", "", "numerical_theory"),
        ("HS115YL", "Yoga", "", "health_practice"),
        ("CI125AIA", "Python Programming", "", "programming"),
        ("ME115EG", "Computer Aided Engineering Graphics", "", "cad"),
        ("HS115EN", "Communicative English", "", "language"),
        ("HS115IC", "Indian Constitution", "", "objective_hss"),
        ("ID115IL", "Idea Lab", "", "project"),
        ("PH115TP", "Engineering Physics", "Credits L:T:P: 2:0:1", "theory_lab"),
        ("HS115HU", "Humanities", "", "theory"),
    ],
)
def test_course_profile_classifies_supported_rvce_activity_models(
    code: str,
    title: str,
    extra: str,
    expected: str,
) -> None:
    """Route explicit RVCE title/code/practical evidence to the supported activity template."""
    profile = extract_course_profile(f"Course Code: {code}\n{extra}\nUnit-I Foundations 09 Hrs.", code, title)
    assert profile.course_type == expected
