from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.v1 import router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import Concept, ConceptPrerequisite, Course, Resource, TopicProgress, User
from app.core.security import hash_password
from sqlalchemy import select


def init_database() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.processed_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == "demo@example.com"))
        if user is None:
            user = User(email="demo@example.com", name="Demo Student", password_hash=hash_password("demo-password"))
            db.add(user)
            db.flush()
        course = db.scalar(select(Course).where(Course.owner_id == user.id, Course.code == "CS101"))
        if course is None:
            course = Course(owner_id=user.id, code="CS101", title="Python Foundations", description="Core programming and problem solving.")
            db.add(course)
            db.flush()
            db.add_all([
                Concept(id="variables", course_id=course.id, name="Variables and Types", difficulty=1, status="completed"),
                Concept(id="control-flow", course_id=course.id, name="Control Flow", difficulty=2, status="in_progress"),
                Concept(id="functions", course_id=course.id, name="Functions", difficulty=2, status="not_started"),
            ])
            db.add(ConceptPrerequisite(concept_id="control-flow", prerequisite_id="variables"))
            db.add(ConceptPrerequisite(concept_id="functions", prerequisite_id="control-flow"))
            db.add(TopicProgress(user_id=user.id, concept_id="variables", completed=True, score=100))
            db.add(Resource(course_id=course.id, concept_id="control-flow", title="Python control flow guide", kind="article", url="https://docs.python.org/3/tutorial/controlflow.html", duration_minutes=25))
        db.commit()
    finally:
        db.close()


init_database()

app = FastAPI(title=settings.app_name, version="0.1.0", description="Learning roadmap API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router, prefix=settings.api_prefix)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "learning-roadmap-api"}
