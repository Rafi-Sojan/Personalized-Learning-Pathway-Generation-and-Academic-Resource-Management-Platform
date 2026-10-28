from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RvceSyllabusCourseCreate(BaseModel):
    program_code: str = Field(min_length=2, max_length=20)
    scheme_year: int = Field(ge=2016, le=2100)
    semester: int = Field(ge=1, le=8)
    course_code: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=2, max_length=240)
    credits: float = Field(gt=0, le=20)
    category: str = Field(default="", max_length=80)
    contact_hours: float | None = Field(default=None, ge=0, le=100)
    prerequisites: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    source_url: HttpUrl
    source_checksum: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    verification_status: str = Field(default="pending_review", pattern="^(pending_review|academic_verified|rejected)$")


class RvceSyllabusCourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    program_code: str
    scheme_year: int
    semester: int
    course_code: str
    title: str
    credits: float
    category: str
    contact_hours: float | None
    prerequisites: list[str]
    outcomes: list[str]
    source_url: str
    source_checksum: str
    verification_status: str
    created_at: datetime
