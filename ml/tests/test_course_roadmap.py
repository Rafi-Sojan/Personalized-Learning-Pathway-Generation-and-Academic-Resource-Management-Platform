"""Regression coverage for typed activity demand and balanced calendar scheduling."""

from datetime import date

import pytest

from ml.scheduling.course_roadmap import (
    ActivityDemand,
    adjusted_minutes,
    build_concept_demands,
    schedule_activity_demands,
)


def _demand(identifier: str, course_id: str, minutes: int = 30) -> ActivityDemand:
    """Build a compact deterministic demand for calendar tests."""
    return ActivityDemand(
        demand_id=identifier,
        course_id=course_id,
        course_code=course_id.upper(),
        course_title=f"Course {course_id}",
        concept_id=f"concept-{identifier}",
        concept_name=identifier,
        syllabus_version_id="version-1",
        unit_label="I",
        source_page=1,
        assessment_scope="both",
        activity_type="learn",
        modality="lecture",
        minutes=minutes,
        reason="test demand",
    )


def test_programming_mix_preserves_total_and_separates_evidence_kinds() -> None:
    """Create coding activities while reserving Part-A evidence for retrieval practice."""
    demands = build_concept_demands(
        demand_prefix="python",
        course_id="course-1",
        course_code="CI125AIA",
        course_title="Python Programming",
        course_type="programming",
        concept_id="functions",
        concept_name="Functions",
        syllabus_version_id="version-1",
        unit_label="II",
        source_page=12,
        assessment_scope="both",
        base_minutes=120,
        mastery_score=None,
        mode="full_term",
        reason="source ordered",
        main_question_ids=("main-1",),
        quiz_question_ids=("quiz-1",),
    )
    assert sum(item.minutes for item in demands) == 120
    assert [item.activity_type for item in demands] == [
        "learn",
        "code_along",
        "coding_practice",
        "mini_project",
        "retrieval",
    ]
    assert next(item for item in demands if item.activity_type == "retrieval").evidence_question_ids == ("quiz-1",)
    assert all(
        item.evidence_question_ids == ("main-1",)
        for item in demands
        if item.activity_type != "retrieval"
    )


@pytest.mark.parametrize(
    "course_type",
    [
        "generic",
        "theory",
        "numerical_theory",
        "theory_lab",
        "programming",
        "project",
        "cad",
        "language",
        "objective_hss",
        "health_practice",
    ],
)
def test_every_supported_course_type_has_an_exact_activity_allocation(course_type: str) -> None:
    """Keep every reviewed course template non-empty and minute preserving."""
    demands = build_concept_demands(
        demand_prefix=course_type,
        course_id="course-1",
        course_code="TEST101",
        course_title="Template Test",
        course_type=course_type,
        concept_id="concept-1",
        concept_name="Template Concept",
        syllabus_version_id="version-1",
        unit_label="I",
        source_page=1,
        assessment_scope="both",
        base_minutes=180,
        mastery_score=None,
        mode="full_term",
        reason="template regression",
    )
    assert demands
    assert sum(item.minutes for item in demands) == 180
    assert all(item.minutes >= 10 for item in demands)


def test_see_mode_excludes_explicit_cie_only_units() -> None:
    """Respect a reviewed syllabus exclusion instead of inferring SEE coverage."""
    demands = build_concept_demands(
        demand_prefix="cie-only",
        course_id="course-1",
        course_code="HS115YL",
        course_title="Yoga",
        course_type="health_practice",
        concept_id="practice",
        concept_name="Practice",
        syllabus_version_id="version-1",
        unit_label="III",
        source_page=18,
        assessment_scope="cie_only",
        base_minutes=90,
        mastery_score=None,
        mode="see",
        reason="reviewed scope",
    )
    assert demands == []


def test_mastery_adaptation_is_bounded_and_explainable() -> None:
    """Allocate more time to weak mastery and less to strong mastery without reaching zero."""
    assert adjusted_minutes(100, 10, "full_term") == 115
    assert adjusted_minutes(100, 90, "full_term") == 55
    assert adjusted_minutes(20, 100, "revision") == 10


def test_semester_scheduler_interleaves_courses_and_honors_unavailable_days() -> None:
    """Balance selected courses while retaining each course's internal demand order."""
    scheduled = schedule_activity_demands(
        {
            "course-a": [_demand("a1", "course-a"), _demand("a2", "course-a")],
            "course-b": [_demand("b1", "course-b"), _demand("b2", "course-b")],
        },
        start_date=date(2026, 11, 9),
        target_date=date(2026, 11, 11),
        daily_minutes=60,
        unavailable_weekdays=(1,),
    )
    assert [item.course_id for item in scheduled[:2]] == ["course-a", "course-b"]
    assert [item.demand_id for item in scheduled if item.course_id == "course-a"] == ["a1", "a2"]
    assert [item.demand_id for item in scheduled if item.course_id == "course-b"] == ["b1", "b2"]
    assert {item.scheduled_date for item in scheduled} == {date(2026, 11, 9), date(2026, 11, 11)}


def test_scheduler_rejects_an_infeasible_deadline() -> None:
    """Fail explicitly when capacity cannot satisfy all demanded learning time."""
    with pytest.raises(ValueError, match="deadline is infeasible"):
        schedule_activity_demands(
            {"course-a": [_demand("a1", "course-a", 90)]},
            start_date=date(2026, 11, 9),
            target_date=date(2026, 11, 9),
            daily_minutes=60,
        )
