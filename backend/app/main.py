import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy import select, text

from app.api.v1 import router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import Concept, ConceptPrerequisite, Course, Resource, TopicProgress, User


def init_database() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.processed_dir).mkdir(parents=True, exist_ok=True)
    if settings.environment.lower() == "production":
        return
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

configure_logging()
audit_logger = logging.getLogger("audit")

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
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' http://localhost:8000 http://localhost:5173; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'"
    response.headers["X-Request-ID"] = request_id
    audit_logger.info("request_id=%s method=%s path=%s status=%s duration_ms=%.2f", request_id, request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000)
    return response


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "learning-roadmap-api"}


@app.get("/health/ready", tags=["system"])
def readiness() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    status = "ready"
    try:
        Redis.from_url(settings.redis_url, socket_connect_timeout=0.5, socket_timeout=0.5).ping()
    except Exception:
        status = "ready-with-redis-fallback"
    return {"status": status, "service": "learning-roadmap-api"}
