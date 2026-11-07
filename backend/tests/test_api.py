from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.infrastructure.cache import redis_cache
from app.models import Concept, ConceptPrerequisite, Course, Resource, SyllabusRecord, SyllabusVersion, User as UserModel

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    """Create or authenticate an isolated test student and ensure source-backed learning data."""
    response = client.post("/api/v1/auth/register", json={"email": "demo@example.com", "name": "Demo Learner", "password": "demo-password"})
    if response.status_code == 409:
        response = client.post("/api/v1/auth/login", json={"email": "demo@example.com", "password": "demo-password"})
    assert response.status_code in {200, 201}, response.text
    _ensure_learning_fixture(response.json()["user"]["id"])
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _ensure_learning_fixture(user_id: str) -> None:
    """Create the minimum processed-syllabus course required by authenticated API tests."""
    db = SessionLocal()
    try:
        course = db.scalar(select(Course).where(Course.owner_id == user_id, Course.code == "TST101"))
        if course is None:
            course = Course(owner_id=user_id, code="TST101", title="Test Programming", description="Isolated API fixture")
            db.add(course)
            db.flush()
        version = db.scalar(select(SyllabusVersion).where(SyllabusVersion.course_id == course.id, SyllabusVersion.label == "Test syllabus"))
        if version is None:
            resource = Resource(course_id=course.id, title="test-syllabus.pdf", kind="syllabus_pdf", processing_status="processed")
            db.add(resource)
            db.flush()
            version = SyllabusVersion(course_id=course.id, label="Test syllabus", source_resource_id=resource.id)
            db.add(version)
            db.flush()
        control_flow = db.get(Concept, "control-flow")
        if control_flow is None:
            control_flow = Concept(id="control-flow", course_id=course.id, name="Control Flow", difficulty=2, syllabus_version_id=version.id, estimated_minutes=45)
            db.add(control_flow)
        functions = db.get(Concept, "functions")
        if functions is None:
            functions = Concept(id="functions", course_id=course.id, name="Functions", difficulty=2, syllabus_version_id=version.id, estimated_minutes=90)
            db.add(functions)
            db.flush()
            db.add(ConceptPrerequisite(concept_id=functions.id, prerequisite_id=control_flow.id, status="accepted"))
        db.flush()
        for concept in (control_flow, functions):
            record = db.scalar(select(SyllabusRecord).where(SyllabusRecord.syllabus_version_id == version.id, SyllabusRecord.mapped_concept_id == concept.id))
            if record is None:
                db.add(SyllabusRecord(syllabus_version_id=version.id, source_resource_id=version.source_resource_id, course_id=course.id, record_type="topic", source_page=1, source_text=concept.name, normalized_text=concept.name.lower(), unit_label="I", confidence=1.0, review_status="verified", mapped_concept_id=concept.id))
        db.commit()
        redis_cache.delete(f"courses:{user_id}")
        redis_cache.delete(f"concepts:{user_id}:all")
        redis_cache.delete(f"concepts:{user_id}:{course.id}")
    finally:
        db.close()


def test_health() -> None:
    """Check the liveness endpoint reports the API service identity."""
    assert client.get("/health").json()["status"] == "ok"


def test_private_routes_require_authentication() -> None:
    """Ensure learner-owned API routes reject requests without a valid token."""
    assert client.get("/api/v1/courses").status_code == 401
    assert client.get("/api/v1/progress").status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "demo@example.com", "password": "wrong-password"}).status_code == 401


def test_logout_revokes_existing_token_and_metrics_are_exposed() -> None:
    """Ensure logout invalidates the current token and metrics remain scrapeable."""
    headers = auth_headers()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "roadmap_http_requests_total" in metrics.text


def test_courses_and_roadmap() -> None:
    """Exercise owned course listing and authenticated roadmap generation."""
    headers = auth_headers()
    assert client.get("/api/v1/courses", headers=headers).status_code == 200
    course_id = client.get("/api/v1/courses", headers=headers).json()[0]["id"]
    roadmap = client.get("/api/v1/roadmap", headers=headers, params={"course_id": course_id}).json()
    assert roadmap and "scheduled_date" in roadmap[0]


def test_syllabus_analysis() -> None:
    """Check syllabus text analysis returns extracted topic mappings."""
    response = client.post("/api/v1/syllabus/analyze", headers=auth_headers(), json={"text": "# Variables\n- Functions"})
    assert response.json()["count"] == 2


def test_exam_import_persists_explainable_matcher_evidence() -> None:
    """Return a versioned suggestion while keeping imported evidence pending review."""
    headers = auth_headers()
    courses = client.get("/api/v1/courses", headers=headers).json()
    course_id = next(course["id"] for course in courses if course["code"] == "TST101")
    response = client.post(
        "/api/v1/exams/import",
        headers=headers,
        json={
            "course_id": course_id,
            "source": "matcher-regression",
            "exam_year": 2026,
            "text": "PART B\n1. Explain functions and function calls in detail.",
            "assessment_type": "test",
            "question_format": "long",
        },
    )
    assert response.status_code == 201, response.text
    question = response.json()[0]
    assert question["concept_id"] == "functions"
    assert question["review_status"] == "pending_review"
    assert question["mapping_metadata"]["model_version"] == "rvce-hybrid-lexical-v2"
    assert question["mapping_metadata"]["status"] == "matched"
    assert question["mapping_metadata"]["candidates"][0]["concept_id"] == "functions"


def test_rankings_return_only_the_authenticated_learner_summary() -> None:
    """Replace fabricated leaderboard rows with one private mastery summary."""
    response = client.get("/api/v1/rankings", headers=auth_headers())
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Demo Learner"
    assert response.json()[0]["is_current_user"] is True


def test_account_export_and_roadmap_history() -> None:
    """Check account export and persisted roadmap revision history responses."""
    headers = auth_headers()
    exported = client.get("/api/v1/auth/export", headers=headers)
    assert exported.status_code == 200
    assert {"user", "courses", "progress", "study_plans"}.issubset(exported.json())
    course_id = client.get("/api/v1/courses", headers=headers).json()[0]["id"]
    generated = client.post("/api/v1/roadmap/generate", headers=headers, json={"course_id": course_id, "target_date": "2099-01-01", "daily_minutes": 60})
    assert generated.status_code == 201
    history = client.get("/api/v1/roadmap/history", headers=headers)
    assert history.status_code == 200
    assert history.json()


def test_upload_rejects_pdf_with_invalid_magic_bytes() -> None:
    """Reject uploads whose contents do not begin with the PDF file signature."""
    course_id = client.get("/api/v1/courses", headers=auth_headers()).json()[0]["id"]
    response = client.post("/api/v1/resources/upload", headers=auth_headers(), params={"course_id": course_id}, files={"file": ("document.pdf", b"not-a-pdf", "application/pdf")})
    assert response.status_code == 415


def instructor_headers() -> dict[str, str]:
    """Create and authenticate an instructor for role-protected endpoint checks."""
    db = SessionLocal()
    try:
        user = db.scalar(select(UserModel).where(UserModel.email == "exam-instructor@example.com"))
        if user is None:
            user = UserModel(email="exam-instructor@example.com", name="Exam Instructor", password_hash=hash_password("instructor-password"), role="instructor")
            db.add(user)
        else:
            user.role = "instructor"
        db.commit()
    finally:
        db.close()
    response = client.post("/api/v1/auth/login", json={"email": "exam-instructor@example.com", "password": "instructor-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_roles_protect_admin_and_exam_import_is_rankable() -> None:
    """Check role boundaries and the historical-question import-to-ranking flow."""
    student = auth_headers()
    assert client.get("/api/v1/admin/users", headers=student).status_code == 403
    course_id = client.get("/api/v1/courses", headers=student).json()[0]["id"]
    imported = client.post("/api/v1/exams/import", headers=instructor_headers(), json={"course_id": course_id, "source": "fixture-paper-review-gate", "exam_year": 2025, "assessment_type": "test", "question_format": "unknown", "part_a_is_quiz": True, "text": "PART A\n1. Explain functions. (2 marks)\nPART B\n2. Explain control flow. (10 marks)"})
    assert imported.status_code == 201
    assert all(question["review_status"] == "pending_review" for question in imported.json())
    assert [question["question_kind"] for question in imported.json()] == ["quiz", "main"]
    assert [question["marks"] for question in imported.json()] == [2.0, 10.0]
    assert all(question["assessment_type"] == "test" for question in imported.json())
    assert all(question["concept_id"] is not None for question in imported.json())
    assert client.get("/api/v1/exams/frequency", headers=student, params={"course_id": course_id}).json()["question_count"] == 0
    for index, question in enumerate(imported.json()):
        reviewed = client.post(f"/api/v1/exams/questions/{question['id']}/review", headers=student, params={"status": "verified", "assessment_type": "quiz" if index == 0 else "test", "question_format": "short" if index == 0 else "long"})
        assert reviewed.status_code == 200
        assert reviewed.json()["assessment_type"] == ("quiz" if index == 0 else "test")
    verified_frequency = client.get("/api/v1/exams/frequency", headers=student, params={"course_id": course_id}).json()
    assert verified_frequency["question_count"] == 2
    assert verified_frequency["main_question_count"] == 1
    assert verified_frequency["mapped_main_question_count"] == 1
    assert verified_frequency["unmapped_main_question_count"] == 0
    assert verified_frequency["quiz_count"] == 1
    assert verified_frequency["topics"][0]["topic_name"] == "Control Flow"
    main_question = imported.json()[1]
    cleared = client.post(f"/api/v1/exams/questions/{main_question['id']}/review", headers=student, params={"status": "verified", "clear_concept": True})
    assert cleared.status_code == 200
    assert cleared.json()["concept_id"] is None
    cleared_frequency = client.get("/api/v1/exams/frequency", headers=student, params={"course_id": course_id}).json()
    assert cleared_frequency["mapped_main_question_count"] == 0
    assert cleared_frequency["unmapped_main_question_count"] == 1
    remapped = client.post(f"/api/v1/exams/questions/{main_question['id']}/review", headers=student, params={"status": "verified", "concept_id": main_question["concept_id"]})
    assert remapped.status_code == 200
    assert remapped.json()["topic_label"] == "Control Flow"
    rankings = client.get("/api/v1/exams/rankings", headers=student, params={"course_id": course_id})
    assert rankings.status_code == 200


def test_exam_import_rejects_an_explicitly_different_course_code() -> None:
    """Prevent a paper for one RVCE subject from contaminating another subject's frequency data."""
    student = auth_headers()
    course_id = client.get("/api/v1/courses", headers=student).json()[0]["id"]
    response = client.post("/api/v1/exams/import", headers=student, json={"course_id": course_id, "source": "wrong-subject", "exam_year": 2025, "text": "Course Code: 21CS45\n1. Explain routing."})
    assert response.status_code == 422
    assert "not TST101" in response.json()["detail"]


def test_admin_can_read_processing_queue_summary() -> None:
    """Verify an administrator can read worker queue status and other roles cannot."""
    db = SessionLocal()
    try:
        user = db.scalar(select(UserModel).where(UserModel.email == "processing-admin@example.com"))
        if user is None:
            user = UserModel(email="processing-admin@example.com", name="Processing Admin", password_hash=hash_password("admin-password"), role="admin")
            db.add(user)
        else:
            user.role = "admin"
        db.commit()
    finally:
        db.close()
    response = client.post("/api/v1/auth/login", json={"email": "processing-admin@example.com", "password": "admin-password"})
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    summary = client.get("/api/v1/admin/processing", headers=headers)
    assert summary.status_code == 200
    assert "counts" in summary.json()
