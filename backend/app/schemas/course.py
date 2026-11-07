from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Course(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    title: str
    description: str
    progress: float = Field(ge=0, le=100)
    concept_count: int = Field(ge=0)
    program_code: str | None = None
    scheme_year: int | None = None
    semester: int | None = None
    origin: str = "personal"
    catalog_course_id: str | None = None
    syllabus_source_count: int = Field(default=0, ge=0)
    syllabus_status: str = "not_uploaded"


class CourseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    code: str = Field(min_length=2, max_length=20)
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    program_code: str | None = Field(default=None, min_length=2, max_length=20)
    scheme_year: int | None = Field(default=None, ge=2016, le=2100)
    semester: int | None = Field(default=None, ge=1, le=8)

    @model_validator(mode="after")
    def require_complete_academic_scope(self) -> "CourseCreate":
        """Require branch, scheme, and semester together while preserving legacy unscoped clients."""
        scope = (self.program_code, self.scheme_year, self.semester)
        if any(value is not None for value in scope) and not all(value is not None for value in scope):
            raise ValueError("program_code, scheme_year, and semester must be supplied together")
        return self


class SyllabusVersionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    effective_from: date | None = None


class SyllabusVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    course_id: str
    label: str
    effective_from: date | None = None
