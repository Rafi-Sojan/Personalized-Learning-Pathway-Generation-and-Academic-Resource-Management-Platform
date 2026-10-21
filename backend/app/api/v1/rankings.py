from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_rankings() -> list[dict]:
    return [
        {"rank": 1, "name": "Aarav", "points": 1240},
        {"rank": 2, "name": "Maya", "points": 1110},
        {"rank": 3, "name": "You", "points": 860},
    ]
