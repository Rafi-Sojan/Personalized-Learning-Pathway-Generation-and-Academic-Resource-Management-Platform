from fastapi import APIRouter, Query

from app.schemas.learning import RoadmapItem
from app.services.roadmap_service import build_roadmap

router = APIRouter()


@router.get("", response_model=list[RoadmapItem])
def get_roadmap(days: int = Query(default=14, ge=1, le=90)) -> list[RoadmapItem]:
    return build_roadmap(days)
