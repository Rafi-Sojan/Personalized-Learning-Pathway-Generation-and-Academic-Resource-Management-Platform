from datetime import date
from pydantic import BaseModel, Field


class Concept(BaseModel):
    id: str
    name: str
    course_id: str
    difficulty: int = Field(ge=1, le=5)
    status: str
    prerequisites: list[str] = []


class Resource(BaseModel):
    id: str
    title: str
    kind: str
    url: str
    concept_id: str | None = None
    duration_minutes: int = Field(ge=0)


class RoadmapItem(BaseModel):
    id: str
    concept_id: str
    concept_name: str
    scheduled_date: date
    minutes: int = Field(gt=0)
    status: str
    reason: str


class ProgressUpdate(BaseModel):
    concept_id: str
    completed: bool
    score: float | None = Field(default=None, ge=0, le=100)


class QuizQuestion(BaseModel):
    id: str
    prompt: str
    options: list[str]
    answer_index: int = Field(ge=0)
