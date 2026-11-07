from app.services.syllabus_service import extract_declared_course_codes, extract_prerequisite_candidates, extract_syllabus_facts, extract_syllabus_topics, select_syllabus_course_section


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
