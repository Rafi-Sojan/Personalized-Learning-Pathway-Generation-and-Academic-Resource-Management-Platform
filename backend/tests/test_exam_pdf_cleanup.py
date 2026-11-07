"""Historical-paper object-storage cleanup regression coverage."""

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.v1 import exams
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models import Resource


client = TestClient(app)


def test_duplicate_pdf_import_removes_uncommitted_private_object(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the original paper but delete the second object when every parsed row is duplicate."""
    email = f"paper-{uuid4().hex}@example.com"
    registration = client.post("/api/v1/auth/register", json={"email": email, "name": "Paper Learner", "password": "paper-password"})
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    course = client.post("/api/v1/courses", headers=headers, json={"code": "PAPER1", "title": "Paper Course", "description": ""})
    assert course.status_code == 201

    def fake_reader(*_args, **_kwargs):
        """Return one deterministic text page without parsing the synthetic PDF bytes."""
        page = SimpleNamespace(extract_text=lambda: "PART B\n1. Explain deterministic finite automata in detail. (10 marks)")
        return SimpleNamespace(is_encrypted=False, pages=[page])

    monkeypatch.setattr(exams, "PdfReader", fake_reader)
    form = {"source": "CIE duplicate fixture", "exam_year": "2026", "assessment_type": "test", "question_format": "long", "part_a_is_quiz": "true"}
    files = {"file": ("cie.pdf", b"%PDF-1.7 synthetic", "application/pdf")}
    first = client.post("/api/v1/exams/import-pdf", headers=headers, params={"course_id": course.json()["id"]}, data=form, files=files)
    assert first.status_code == 201, first.text
    before = set(Path(settings.upload_dir).glob("exam-*.pdf"))
    assert len(before) == 1

    duplicate = client.post("/api/v1/exams/import-pdf", headers=headers, params={"course_id": course.json()["id"]}, data=form, files=files)
    assert duplicate.status_code == 409
    after = set(Path(settings.upload_dir).glob("exam-*.pdf"))
    assert after == before
    db = SessionLocal()
    try:
        assert db.scalar(select(func.count()).select_from(Resource).where(Resource.course_id == course.json()["id"], Resource.kind == "historical_exam_pdf")) == 1
    finally:
        db.close()
