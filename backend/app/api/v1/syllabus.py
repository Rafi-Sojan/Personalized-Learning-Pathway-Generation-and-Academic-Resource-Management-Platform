from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.integrations.ml_client import map_syllabus
from app.core.security import get_current_user
from app.models import User

router = APIRouter()


class SyllabusRequest(BaseModel):
    text: str = Field(min_length=3, max_length=200_000)


@router.post("/analyze")
def analyze_syllabus(payload: SyllabusRequest, _: User = Depends(get_current_user)) -> dict:
    """Classify syllabus text and return candidate topic-to-concept matches."""
    return map_syllabus(payload.text)
