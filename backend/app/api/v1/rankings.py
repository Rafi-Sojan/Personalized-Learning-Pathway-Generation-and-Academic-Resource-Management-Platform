from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models import User

router = APIRouter()


@router.get("")
def get_rankings(_: User = Depends(get_current_user)) -> list[dict]:
    return [
        {"rank": 1, "name": "Aarav", "points": 1240},
        {"rank": 2, "name": "Maya", "points": 1110},
        {"rank": 3, "name": "You", "points": 860},
    ]
