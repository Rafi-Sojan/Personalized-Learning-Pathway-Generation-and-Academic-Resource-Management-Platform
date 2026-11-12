"""API coverage for reviewed course profiles and source-constrained roadmaps."""

from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import (
    Concept,
    Course,
    HistoricalExamQuestion,
    Resource,
    StudyPlan,
    SyllabusRecord,
    SyllabusVersion,
    TopicProgress,
)


client = TestClient(app)


def _register_learner() -> tuple[dict[str, str], str]:
    """Register an isolated learner for ownership-sensitive roadmap tests."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"course-roadmap-{uuid4().hex}@example.com",
            "name": "Course Roadmap Learner",
            "password": "course-roadmap-password",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]["id"]


def _add_profiled_course(
    user_id: str,
    code: str,
    *,
    profile_status: str,
    semester: int = 1,
    with_questions: bool = False,
) -> dict[str, str]:
    """Persist a processed, source-backed two-unit course with reviewable planning metadata."""
    db = SessionLocal()
    try:
        course = Course(
            owner_id=user_id,
            code=code,
            title=f"{code} Programming",
            description="Roadmap regression fixture",
            program_code="AI",
            scheme_year=2025,
            semester=semester,
        )
        db.add(course)
        db.flush()
        resource = Resource(
            course_id=course.id,
            title=f"{code}-syllabus.pdf",
            kind="syllabus_pdf",
            processing_status="processed",
        )
        db.add(resource)
        db.flush()
        version = SyllabusVersion(
            course_id=course.id,
            label=f"{code} syllabus",
            source_resource_id=resource.id,
            roadmap_profile_status=profile_status,
        )
        version.roadmap_profile = {
            "course_codes": [code],
            "course_type": "programming",
            "category": "Professional Core",
            "credit_allocation": {"lecture": 2.0, "tutorial": 0.0, "practical": 1.0},
            "modality_hours": {"lecture": 1.0, "tutorial": 0.0, "practical": 1.0, "experiential": 0.0},
            "units": [
                {"sequence": 1, "label": "I", "title": "Foundations", "hours": 1.0, "source_page": 4, "assessment_scope": "both"},
                {"sequence": 2, "label": "II", "title": "Applications", "hours": 1.0, "source_page": 5, "assessment_scope": "both"},
            ],
            "course_outcomes": ["CO1 Develop programs."],
            "assessment_components": ["quiz", "test"],
            "assessment_format": "unitwise_theory",
            "cie_marks": "50",
            "see_marks": "50",
            "issues": [],
        }
        db.add(version)
        db.flush()
        first = Concept(
            course_id=course.id,
            name="Programming Foundations",
            difficulty=2,
            unit_label="I",
            unit_sequence=1,
            source_page=4,
            syllabus_version_id=version.id,
        )
        second = Concept(
            course_id=course.id,
            name="Programming Applications",
            difficulty=3,
            unit_label="II",
            unit_sequence=2,
            source_page=5,
            syllabus_version_id=version.id,
        )
        db.add_all([first, second])
        db.flush()
        for concept in (first, second):
            db.add(SyllabusRecord(
                syllabus_version_id=version.id,
                source_resource_id=resource.id,
                course_id=course.id,
                record_type="topic",
                source_page=concept.source_page,
                source_text=concept.name,
                normalized_text=concept.name.casefold(),
                unit_label=concept.unit_label,
                confidence=1.0,
                review_status="verified",
                mapped_concept_id=concept.id,
            ))
        main_question_id = ""
        quiz_question_id = ""
        if with_questions:
            main_question = HistoricalExamQuestion(
                course_id=course.id,
                source="SEE 2025",
                exam_year=2025,
                prompt="Develop a program using control flow.",
                concept_id=first.id,
                topic_label=first.name,
                paper_part="B",
                question_kind="main",
                marks=10,
                review_status="verified",
            )
            quiz_question = HistoricalExamQuestion(
                course_id=course.id,
                source="CIE 2025",
                exam_year=2025,
                prompt="Select the valid control-flow statement.",
                concept_id=first.id,
                topic_label=first.name,
                paper_part="A",
                question_kind="quiz",
                marks=1,
                review_status="verified",
            )
            db.add_all([main_question, quiz_question])
            db.flush()
            main_question_id = main_question.id
            quiz_question_id = quiz_question.id
        db.commit()
        return {
            "course_id": course.id,
            "version_id": version.id,
            "first_concept_id": first.id,
            "second_concept_id": second.id,
            "main_question_id": main_question_id,
            "quiz_question_id": quiz_question_id,
        }
    finally:
        db.close()


def test_reviewed_profile_controls_see_scope_activity_types_and_mastery() -> None:
    """Gate persistence on review, separate exam evidence, and feed completion back to mastery."""
    headers, user_id = _register_learner()
    fixture = _add_profiled_course(user_id, "MAP101", profile_status="pending_review", with_questions=True)
    other_headers, _ = _register_learner()
    assert client.get(
        "/api/v1/syllabus/profile",
        headers=other_headers,
        params={"course_id": fixture["course_id"]},
    ).status_code == 404
    assert client.post(
        f"/api/v1/syllabus/profile/{fixture['version_id']}/review",
        headers=other_headers,
        json={"status": "verified"},
    ).status_code == 404
    excluded_weekday = (date.today().weekday() + 3) % 7
    request = {
        "course_id": fixture["course_id"],
        "start_date": date.today().isoformat(),
        "target_date": (date.today() + timedelta(days=2)).isoformat(),
        "daily_minutes": 180,
        "revision_minutes": 30,
        "mode": "see",
        "unavailable_weekdays": [excluded_weekday],
    }
    blocked = client.post("/api/v1/roadmap/generate", headers=headers, json=request)
    assert blocked.status_code == 409
    assert "review and verify" in blocked.json()["detail"].casefold()
    unknown_unit = client.post(
        f"/api/v1/syllabus/profile/{fixture['version_id']}/review",
        headers=headers,
        json={"status": "verified", "unit_hours": {"UNKNOWN": 1}},
    )
    assert unknown_unit.status_code == 422

    reviewed = client.post(
        f"/api/v1/syllabus/profile/{fixture['version_id']}/review",
        headers=headers,
        json={
            "status": "verified",
            "course_type": "programming",
            "lecture_hours": 10,
            "practical_hours": 10,
            "unit_hours": {"II": 2},
            "unit_assessment_scopes": {"II": "cie_only"},
            "review_notes": "Checked against the printed course table and assessment rubric.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "verified"
    assert reviewed.json()["profile"]["units"][1]["hours"] == 2
    assert reviewed.json()["profile"]["units"][1]["assessment_scope"] == "cie_only"

    generated = client.post("/api/v1/roadmap/generate", headers=headers, json=request)
    assert generated.status_code == 201, generated.text
    items = generated.json()["items"]
    assert items
    assert {item["concept_id"] for item in items} == {fixture["first_concept_id"]}
    assert {item["activity_type"] for item in items} == {
        "learn",
        "code_along",
        "coding_practice",
        "mini_project",
        "retrieval",
        "final_revision",
    }
    retrieval = next(item for item in items if item["activity_type"] == "retrieval")
    assert retrieval["evidence_question_ids"] == [fixture["quiz_question_id"]]
    assert all(
        fixture["main_question_id"] in item["evidence_question_ids"]
        for item in items
        if item["activity_type"] != "retrieval"
    )
    active_plan = client.get(
        "/api/v1/roadmap/active",
        headers=headers,
        params={"course_id": fixture["course_id"]},
    )
    assert active_plan.status_code == 200
    assert active_plan.json()["id"] == generated.json()["id"]
    assert active_plan.json()["unavailable_weekdays"] == [excluded_weekday]
    assert [item["id"] for item in active_plan.json()["items"]] == [item["id"] for item in items]

    for item in items[:-1]:
        response = client.patch(
            f"/api/v1/roadmap/items/{item['id']}",
            headers=headers,
            json={"status": "completed"},
        )
        assert response.status_code == 200
    final = client.patch(
        f"/api/v1/roadmap/items/{items[-1]['id']}",
        headers=headers,
        json={"status": "completed", "mastery_score": 88},
    )
    assert final.status_code == 200
    invalid_mastery = client.patch(
        f"/api/v1/roadmap/items/{items[0]['id']}",
        headers=headers,
        json={"status": "planned", "mastery_score": 50},
    )
    assert invalid_mastery.status_code == 422
    reopened = client.patch(
        f"/api/v1/roadmap/items/{items[0]['id']}",
        headers=headers,
        json={"status": "planned"},
    )
    assert reopened.status_code == 200
    db = SessionLocal()
    try:
        progress = db.scalar(select(TopicProgress).where(
            TopicProgress.user_id == user_id,
            TopicProgress.concept_id == fixture["first_concept_id"],
        ))
        assert progress is not None
        assert progress.completed is False
        assert progress.score == 88
        concept = db.get(
            Concept,
            fixture["first_concept_id"],
        )
        assert concept is not None
        assert concept.status == "in_progress"

    finally:
        db.close()
    restored = client.patch(
        f"/api/v1/roadmap/items/{items[0]['id']}",
        headers=headers,
        json={"status": "completed"},
    )
    assert restored.status_code == 200


def test_semester_generation_balances_explicit_same_scope_courses() -> None:
    """Persist one semester plan only for explicitly selected courses sharing academic scope."""
    headers, user_id = _register_learner()
    first = _add_profiled_course(user_id, "SEM101", profile_status="verified")
    second = _add_profiled_course(user_id, "SEM102", profile_status="verified")
    generated = client.post(
        "/api/v1/roadmap/semester/generate",
        headers=headers,
        json={
            "course_ids": [first["course_id"], second["course_id"]],
            "start_date": date.today().isoformat(),
            "target_date": date.today().isoformat(),
            "daily_minutes": 300,
            "revision_minutes": 0,
            "mode": "full_term",
            "unavailable_weekdays": [],
        },
    )
    assert generated.status_code == 201, generated.text
    plan = generated.json()
    assert plan["scope_type"] == "semester"
    assert plan["course_id"] is None
    assert (plan["program_code"], plan["scheme_year"], plan["semester"]) == ("AI", 2025, 1)
    assert {item["course_id"] for item in plan["items"]} == {first["course_id"], second["course_id"]}
    assert plan["items"][0]["course_id"] != plan["items"][1]["course_id"]
    for course_id in (first["course_id"], second["course_id"]):
        unit_labels = [item["unit_label"] for item in plan["items"] if item["course_id"] == course_id]
        assert max(index for index, label in enumerate(unit_labels) if label == "I") < min(
            index for index, label in enumerate(unit_labels) if label == "II"
        )
    active_plan = client.get("/api/v1/roadmap/active", headers=headers)
    assert active_plan.status_code == 200
    assert active_plan.json()["id"] == plan["id"]
    history = client.get(
        "/api/v1/roadmap/history",
        headers=headers,
        params={"course_id": first["course_id"]},
    )
    assert history.status_code == 200
    assert any(item["plan_id"] == plan["id"] for item in history.json())
    db = SessionLocal()
    try:
        stored = db.get(StudyPlan, plan["id"])
        assert stored is not None
        assert stored.scope_type == "semester"
        assert stored.algorithm_version == "rvce-activity-roadmap-v3"
    finally:
        db.close()


def test_semester_generation_rejects_mixed_academic_scope() -> None:
    """Require the learner to resolve cross-semester selections instead of guessing options."""
    headers, user_id = _register_learner()
    first = _add_profiled_course(user_id, "SCOPE1", profile_status="verified", semester=1)
    second = _add_profiled_course(user_id, "SCOPE2", profile_status="verified", semester=2)
    response = client.post(
        "/api/v1/roadmap/semester/generate",
        headers=headers,
        json={
            "course_ids": [first["course_id"], second["course_id"]],
            "target_date": (date.today() + timedelta(days=2)).isoformat(),
            "daily_minutes": 300,
            "revision_minutes": 0,
        },
    )
    assert response.status_code == 422
    assert "one branch, scheme, and semester" in response.json()["detail"]
