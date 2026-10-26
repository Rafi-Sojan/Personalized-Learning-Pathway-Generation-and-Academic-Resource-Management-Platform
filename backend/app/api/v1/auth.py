from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.models import User as UserModel
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, User
from app.infrastructure.rate_limiter import enforce_rate_limit, login_limiter
from fastapi import Request

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    enforce_rate_limit(request, login_limiter)
    user = db.scalar(select(UserModel).where(UserModel.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return LoginResponse(access_token=create_access_token(user.id), user=User.model_validate(user))


@router.post("/register", response_model=LoginResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    enforce_rate_limit(request, login_limiter)
    email = str(payload.email).lower()
    if db.scalar(select(UserModel).where(UserModel.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = UserModel(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return LoginResponse(access_token=create_access_token(user.id), user=User.model_validate(user))


@router.get("/me", response_model=User)
def me(current_user: UserModel = Depends(get_current_user)) -> User:
    return User.model_validate(current_user)
