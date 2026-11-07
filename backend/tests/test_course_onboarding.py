"""API coverage for learner-created branch subjects and syllabus attachment status."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _learner_headers() -> dict[str, str]:
    """Register an isolated learner and return an authenticated request header."""
    suffix = uuid4().hex
    response = client.post("/api/v1/auth/register", json={"email": f"scope-{suffix}@example.com", "name": "Scope Learner", "password": "scope-password"})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_learner_can_create_a_branch_scoped_subject_and_attach_a_syllabus() -> None:
    """Create an RVCE-scoped personal subject, reject duplicates, and expose upload status."""
    headers = _learner_headers()
    payload = {
        "program_code": "AIML",
        "scheme_year": 2022,
        "semester": 5,
        "code": "AI253IA",
        "title": "Deep Learning",
        "description": "Personal workspace pending academic catalog review.",
    }
    created = client.post("/api/v1/courses", headers=headers, json=payload)
    assert created.status_code == 201, created.text
    course = created.json()
    assert course["program_code"] == "AI"
    assert course["origin"] == "personal"
    assert course["syllabus_source_count"] == 0
    assert course["syllabus_status"] == "not_uploaded"

    duplicate = client.post("/api/v1/courses", headers=headers, json=payload)
    assert duplicate.status_code == 409

    uploaded = client.post(
        "/api/v1/syllabus/sources/upload",
        headers=headers,
        params={"course_id": course["id"]},
        files={"file": ("AI253IA-syllabus.pdf", b"%PDF-1.4\n% onboarding fixture", "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    refreshed = client.get("/api/v1/courses", headers=headers).json()
    current = next(item for item in refreshed if item["id"] == course["id"])
    assert current["syllabus_source_count"] == 1
    assert current["syllabus_status"] == "uploaded"


def test_personal_subject_rejects_an_unsupported_branch_scheme() -> None:
    """Prevent self-declared course scope from inventing unsupported RVCE scheme metadata."""
    response = client.post("/api/v1/courses", headers=_learner_headers(), json={
        "program_code": "AI",
        "scheme_year": 2025,
        "semester": 5,
        "code": "AI500",
        "title": "Unsupported Scope",
    })
    assert response.status_code == 422
    assert "not catalogued" in response.json()["detail"]
