from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


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
    concept_id: str
    concept_name: str
    scheduled_date: date
    minutes: int = Field(gt=0)
    status: str
    reason: str
    evidence_question_ids: list[str] = []


class RoadmapRequest(BaseModel):
    course_id: str
    target_date: date
    daily_minutes: int = Field(gt=0, le=1440)
    revision_minutes: int = Field(default=30, ge=0, le=480)


class StudyPlanResponse(BaseModel):
    id: str
    course_id: str
    target_date: date
    daily_minutes: int
    items: list[RoadmapItem]


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
