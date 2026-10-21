from fastapi import APIRouter

from app.core.security import create_demo_token
from app.schemas.auth import LoginRequest, LoginResponse, User

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = User(id="demo-user", email=payload.email, name=payload.email.split("@")[0].title())
    return LoginResponse(access_token=create_demo_token(user.id), user=user)
