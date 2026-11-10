from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Concept(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    course_id: str
    difficulty: int = Field(ge=1, le=5)
    status: str
    prerequisites: list[str] = []
    suggested_prerequisites: list[str] = []
    unit_label: str | None = None
    unit_sequence: int | None = None
    source_page: int | None = None
    syllabus_version_id: str | None = None
    parent_concept_id: str | None = None
    estimated_minutes: int | None = None
    review_status: str | None = None


class Resource(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    kind: str
    url: str
    concept_id: str | None = None
    duration_minutes: int = Field(ge=0)
    processing_status: str = "ready"
    processing_attempts: int = Field(default=0, ge=0)
    processing_error: str | None = None
    processed_at: datetime | None = None


class HistoricalExamQuestionCreate(BaseModel):
    course_id: str
    source: str = Field(min_length=1, max_length=240)
    exam_year: int = Field(ge=1900, le=2100)
    prompt: str = Field(min_length=5, max_length=20000)
    concept_id: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    paper_part: str | None = Field(default=None, max_length=20)
    question_kind: str = Field(default="main", pattern="^(quiz|main)$")
    assessment_type: str = Field(default="unknown", pattern="^(quiz|test|see|assignment|lab|practice|unknown)$")
    question_format: str = Field(default="unknown", pattern="^(objective|short|long|numerical|coding|practical|unknown)$")
    marks: float | None = Field(default=None, ge=0, le=1000)


class HistoricalExamImportRequest(BaseModel):
    course_id: str
    source: str = Field(min_length=1, max_length=240)
    exam_year: int = Field(ge=1900, le=2100)
    text: str = Field(min_length=5, max_length=500000)
    assessment_type: str = Field(default="unknown", pattern="^(quiz|test|see|assignment|lab|practice|unknown)$")
    question_format: str = Field(default="unknown", pattern="^(objective|short|long|numerical|coding|practical|unknown)$")
    part_a_is_quiz: bool = False


class HistoricalExamQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    course_id: str
    source: str
    exam_year: int
    prompt: str
    concept_id: str | None
    topic_label: str
    difficulty: int | None = None
    paper_part: str | None = None
    question_kind: str = "main"
    question_number: str | None = None
    subpart: str | None = None
    marks: float | None = None
    source_page: int | None = None
    source_document: str = ""
    source_resource_id: str | None = None
    assessment_type: str = "unknown"
    question_format: str = "unknown"
    mapping_confidence: float | None = None
    mapping_metadata: dict[str, object] = Field(default_factory=dict)
    review_status: str = "pending_review"


class HistoricalExamRanking(BaseModel):
    concept_id: str
    concept_name: str
    question_count: int
    average_difficulty: float | None
    score: float


class ResourceMappingRequest(BaseModel):
    concept_id: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: str = Field(default="proposed", pattern="^(proposed|accepted|rejected)$")
    source: str = Field(default="manual", max_length=32)


class ResourceMappingResponse(BaseModel):
    id: str
    resource_id: str
    concept_id: str
    confidence: float | None
    status: str
    source: str
    reviewed_by: str | None


class RoadmapItem(BaseModel):
    id: str
    course_id: str
    course_code: str
    course_title: str
    concept_id: str
    concept_name: str
    scheduled_date: date
    minutes: int = Field(gt=0)
    status: str
    reason: str
    activity_type: str = "learn"
    modality: str = "self_study"
    unit_label: str | None = None
    source_page: int | None = None
    assessment_scope: str = "both"
    syllabus_version_id: str | None = None
    evidence_question_ids: list[str] = Field(default_factory=list)


class RoadmapRequest(BaseModel):
    course_id: str
    start_date: date | None = None
    target_date: date
    daily_minutes: int = Field(gt=0, le=1440)
    revision_minutes: int = Field(default=30, ge=0, le=1440)
    mode: Literal["full_term", "cie", "see", "revision"] = "full_term"
    unavailable_weekdays: list[int] = Field(default_factory=list, max_length=7)

    @field_validator("unavailable_weekdays")
    @classmethod
    def validate_unavailable_weekdays(cls, value: list[int]) -> list[int]:
        """Require unique Python weekday numbers so capacity is deterministic."""
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("unavailable_weekdays must contain values from 0 through 6")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_date_range(self) -> "RoadmapRequest":
        """Reject an explicit start date after the requested target."""
        if self.start_date is not None and self.start_date > self.target_date:
            raise ValueError("start_date must not be after target_date")
        return self


class SemesterRoadmapRequest(BaseModel):
    course_ids: list[str] = Field(min_length=1, max_length=16)
    start_date: date | None = None
    target_date: date
    daily_minutes: int = Field(gt=0, le=1440)
    revision_minutes: int = Field(default=90, ge=0, le=1440)
    mode: Literal["full_term", "cie", "see", "revision"] = "full_term"
    unavailable_weekdays: list[int] = Field(default_factory=list, max_length=7)

    @field_validator("course_ids")
    @classmethod
    def validate_course_ids(cls, value: list[str]) -> list[str]:
        """Reject duplicate subject selections before ownership and scope checks."""
        unique = list(dict.fromkeys(value))
        if len(unique) != len(value):
            raise ValueError("course_ids must not contain duplicates")
        return unique

    @field_validator("unavailable_weekdays")
    @classmethod
    def validate_semester_weekdays(cls, value: list[int]) -> list[int]:
        """Validate weekday exclusions for semester-wide capacity calculations."""
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("unavailable_weekdays must contain values from 0 through 6")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_semester_date_range(self) -> "SemesterRoadmapRequest":
        """Reject an explicit semester-plan start date after its deadline."""
        if self.start_date is not None and self.start_date > self.target_date:
            raise ValueError("start_date must not be after target_date")
        return self


class StudyPlanResponse(BaseModel):
    id: str
    scope_type: str = "course"
    mode: str = "full_term"
    course_id: str | None = None
    program_code: str | None = None
    scheme_year: int | None = None
    semester: int | None = None
    start_date: date
    target_date: date
    daily_minutes: int
    revision_minutes: int = 0
    unavailable_weekdays: list[int] = Field(default_factory=list)
    items: list[RoadmapItem]


class RoadmapItemUpdate(BaseModel):
    status: Literal["planned", "completed", "skipped"]
    mastery_score: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_mastery_status(self) -> "RoadmapItemUpdate":
        """Accept mastery evidence only with a completed learning session."""
        if self.mastery_score is not None and self.status != "completed":
            raise ValueError("mastery_score may be supplied only when status is completed")
        return self


class StudyPlanRevisionResponse(BaseModel):
    id: str
    plan_id: str
    revision_number: int
    event: str
    created_at: str


class ProgressUpdate(BaseModel):
    concept_id: str
    completed: bool
    score: float | None = Field(default=None, ge=0, le=100)


class QuizQuestion(BaseModel):
    id: str
    prompt: str
    options: list[str]
    answer_index: int = Field(ge=0)


class QuizAttemptRequest(BaseModel):
    answer_index: int = Field(ge=0)


class QuizAttemptResponse(BaseModel):
    attempt_id: str
    correct: bool
    score: float
