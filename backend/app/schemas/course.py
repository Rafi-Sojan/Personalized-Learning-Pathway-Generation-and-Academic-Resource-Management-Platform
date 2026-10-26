from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class Course(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    title: str
    description: str
    progress: float = Field(ge=0, le=100)
    concept_count: int = Field(ge=0)


class CourseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    title: str = Field(min_length=2)
    description: str = ""


class SyllabusVersionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    effective_from: date | None = None


class SyllabusVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    course_id: str
    label: str
    effective_from: date | None = None
