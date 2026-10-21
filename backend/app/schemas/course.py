from pydantic import BaseModel, Field


class Course(BaseModel):
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
