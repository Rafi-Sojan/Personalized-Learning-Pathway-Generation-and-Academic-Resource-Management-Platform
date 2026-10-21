from fastapi import APIRouter, Query

from app.schemas.learning import Resource
from app.services.resource_service import list_resources

router = APIRouter()


@router.get("", response_model=list[Resource])
def get_resources(concept_id: str | None = Query(default=None)) -> list[Resource]:
    return list_resources(concept_id)
