from datetime import date, datetime, timezone
import json
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def new_id() -> str:
    """Generate a UUID string for a persisted model identifier."""
    return str(uuid4())


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(32), default="student")
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("owner_id", "program_code", "scheme_year", "semester", "code", name="uq_course_owner_academic_scope"),
        UniqueConstraint("owner_id", "catalog_course_id", name="uq_course_owner_catalog_record"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    code: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    program_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    scheme_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    origin: Mapped[str] = mapped_column(String(24), default="personal", index=True)
    catalog_course_id: Mapped[Optional[str]] = mapped_column(ForeignKey("rvce_syllabus_courses.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SyllabusVersion(Base):
    __tablename__ = "syllabus_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    source_resource_id: Mapped[Optional[str]] = mapped_column(ForeignKey("academic_resources.id"), nullable=True)
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    roadmap_profile_json: Mapped[str] = mapped_column(Text, default="{}")
    roadmap_profile_status: Mapped[str] = mapped_column(String(24), default="pending_review", index=True)
    roadmap_profile_review_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @property
    def roadmap_profile(self) -> dict[str, object]:
        """Expose the reviewed course-planning profile as a defensive JSON object."""
        try:
            value = json.loads(self.roadmap_profile_json or "{}")
        except (TypeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    @roadmap_profile.setter
    def roadmap_profile(self, value: dict[str, object]) -> None:
        """Persist a deterministic profile without storing source-document prose twice."""
        self.roadmap_profile_json = json.dumps(value, sort_keys=True, separators=(",", ":"))


class SyllabusRecord(Base):
    """Store one extracted syllabus fact with its original text and document provenance."""
    __tablename__ = "syllabus_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    syllabus_version_id: Mapped[str] = mapped_column(ForeignKey("syllabus_versions.id"), index=True)
    source_resource_id: Mapped[str] = mapped_column(ForeignKey("academic_resources.id"), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(24), default="topic", index=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(String(500))
    unit_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    parent_label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    review_status: Mapped[str] = mapped_column(String(24), default="pending_review", index=True)
    mapped_concept_id: Mapped[Optional[str]] = mapped_column(ForeignKey("concepts.id"), nullable=True, index=True)


class RvceSyllabusCourse(Base):
    __tablename__ = "rvce_syllabus_courses"
    __table_args__ = (UniqueConstraint("program_code", "scheme_year", "semester", "course_code", name="uq_rvce_syllabus_course_identity"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    program_code: Mapped[str] = mapped_column(String(20), index=True)
    scheme_year: Mapped[int] = mapped_column(Integer, index=True)
    semester: Mapped[int] = mapped_column(Integer, index=True)
    course_code: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(240))
    credits: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(80), default="")
    contact_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prerequisites_json: Mapped[str] = mapped_column(Text, default="[]")
    outcomes_json: Mapped[str] = mapped_column(Text, default="[]")
    source_url: Mapped[str] = mapped_column(String(1000))
    source_checksum: Mapped[str] = mapped_column(String(64))
    source_filename: Mapped[str] = mapped_column(String(500), default="")
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(24), default="pending_review", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="not_started")
    unit_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    unit_sequence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    syllabus_version_id: Mapped[Optional[str]] = mapped_column(ForeignKey("syllabus_versions.id"), index=True, nullable=True)
    parent_concept_id: Mapped[Optional[str]] = mapped_column(ForeignKey("concepts.id"), nullable=True, index=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class ConceptPrerequisite(Base):
    __tablename__ = "concept_prerequisites"
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    prerequisite_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), default="accepted", index=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, default="")


class Resource(Base):
    __tablename__ = "academic_resources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    course_id: Mapped[Optional[str]] = mapped_column(ForeignKey("courses.id"), index=True, nullable=True)
    concept_id: Mapped[Optional[str]] = mapped_column(ForeignKey("concepts.id"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    kind: Mapped[str] = mapped_column(String(32))
    url: Mapped[str] = mapped_column(String(1000), default="")
    storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    processed_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    processing_status: Mapped[str] = mapped_column(String(32), default="ready")
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_next_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ResourceConceptMapping(Base):
    __tablename__ = "resource_concept_mappings"
    __table_args__ = (UniqueConstraint("resource_id", "concept_id", name="uq_resource_concept_mapping"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    resource_id: Mapped[str] = mapped_column(ForeignKey("academic_resources.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="proposed")
    source: Mapped[str] = mapped_column(String(32), default="manual")
    reviewed_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HistoricalExamQuestion(Base):
    __tablename__ = "historical_exam_questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"), index=True)
    source: Mapped[str] = mapped_column(String(240))
    source_document: Mapped[str] = mapped_column(String(500), default="")
    source_resource_id: Mapped[Optional[str]] = mapped_column(ForeignKey("academic_resources.id"), nullable=True, index=True)
    exam_year: Mapped[int] = mapped_column(Integer, index=True)
    prompt: Mapped[str] = mapped_column(Text)
    concept_id: Mapped[Optional[str]] = mapped_column(ForeignKey("concepts.id"), index=True, nullable=True)
    topic_label: Mapped[str] = mapped_column(String(120), default="general")
    difficulty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    paper_part: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    question_kind: Mapped[str] = mapped_column(String(20), default="main", index=True)
    question_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    subpart: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assessment_type: Mapped[str] = mapped_column(String(24), default="unknown", index=True)
    question_format: Mapped[str] = mapped_column(String(24), default="unknown")
    mapping_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mapping_metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    review_status: Mapped[str] = mapped_column(String(24), default="pending_review", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @property
    def mapping_metadata(self) -> dict[str, object]:
        """Expose bounded matcher evidence as parsed JSON for API serialization."""
        try:
            value = json.loads(self.mapping_metadata_json or "{}")
        except (TypeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    @mapping_metadata.setter
    def mapping_metadata(self, value: dict[str, object]) -> None:
        """Persist matcher evidence deterministically without duplicating prompt text."""
        self.mapping_metadata_json = json.dumps(value, sort_keys=True, separators=(",", ":"))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class TopicProgress(Base):
    __tablename__ = "topic_progress"
    __table_args__ = (UniqueConstraint("user_id", "concept_id", name="uq_progress_user_concept"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_studied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    answer_index: Mapped[int] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class StudyPlan(Base):
    __tablename__ = "study_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[Optional[str]] = mapped_column(ForeignKey("courses.id"), index=True, nullable=True)
    scope_type: Mapped[str] = mapped_column(String(24), default="course", index=True)
    mode: Mapped[str] = mapped_column(String(24), default="full_term")
    start_date: Mapped[date] = mapped_column(Date, default=date.today)
    target_date: Mapped[date] = mapped_column(Date)
    daily_minutes: Mapped[int] = mapped_column(Integer)
    revision_minutes: Mapped[int] = mapped_column(Integer, default=30)
    unavailable_weekdays_json: Mapped[str] = mapped_column(Text, default="[]")
    program_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    scheme_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="heuristic-v1")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @property
    def unavailable_weekdays(self) -> list[int]:
        """Return unique stored weekday exclusions after rejecting malformed JSON values."""
        try:
            value = json.loads(self.unavailable_weekdays_json or "[]")
        except (TypeError, json.JSONDecodeError):
            return []
        if not isinstance(value, list):
            return []
        return list(dict.fromkeys(item for item in value if isinstance(item, int) and 0 <= item <= 6))

    @unavailable_weekdays.setter
    def unavailable_weekdays(self, value: list[int]) -> None:
        """Persist validated weekday exclusions in deterministic order for plan restoration."""
        bounded = {item for item in value if isinstance(item, int) and 0 <= item <= 6}
        self.unavailable_weekdays_json = json.dumps(sorted(bounded), separators=(",", ":"))


class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(ForeignKey("study_plans.id"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"), index=True)
    syllabus_version_id: Mapped[Optional[str]] = mapped_column(ForeignKey("syllabus_versions.id"), nullable=True)
    scheduled_date: Mapped[date] = mapped_column(Date)
    minutes: Mapped[int] = mapped_column(Integer)
    sequence: Mapped[int] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String(32), default="learn")
    modality: Mapped[str] = mapped_column(String(32), default="self_study")
    unit_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assessment_scope: Mapped[str] = mapped_column(String(24), default="both")
    evidence_question_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(32), default="planned")
    explanation: Mapped[str] = mapped_column(Text, default="")

    @property
    def evidence_question_ids(self) -> list[str]:
        """Return only string identifiers from the stored supporting-question list."""
        try:
            value = json.loads(self.evidence_question_ids_json or "[]")
        except (TypeError, json.JSONDecodeError):
            return []
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    @evidence_question_ids.setter
    def evidence_question_ids(self, value: list[str]) -> None:
        """Persist supporting question identifiers in stable order for account export and UI links."""
        self.evidence_question_ids_json = json.dumps(list(dict.fromkeys(value)), separators=(",", ":"))


class StudyPlanRevision(Base):
    __tablename__ = "study_plan_revisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(ForeignKey("study_plans.id"), index=True)
    revision_number: Mapped[int] = mapped_column(Integer)
    event: Mapped[str] = mapped_column(String(32), default="generated")
    snapshot: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
