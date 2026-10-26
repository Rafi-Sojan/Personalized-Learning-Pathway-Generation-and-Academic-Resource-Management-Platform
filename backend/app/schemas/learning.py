from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class Concept(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    course_id: str
    difficulty: int = Field(ge=1, le=5)
    status: str
    prerequisites: list[str] = []


class Resource(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    kind: str
    url: str
    concept_id: str | None = None
    duration_minutes: int = Field(ge=0)
    processing_status: str = "ready"


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
