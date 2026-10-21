from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.integrations.ml_client import map_syllabus

router = APIRouter()


class SyllabusRequest(BaseModel):
    text: str = Field(min_length=3)


@router.post("/analyze")
def analyze_syllabus(payload: SyllabusRequest) -> dict:
    return map_syllabus(payload.text)
