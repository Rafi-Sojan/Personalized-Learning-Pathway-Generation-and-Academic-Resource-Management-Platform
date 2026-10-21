from fastapi import Header

from app.core.security import get_user_id_from_token


def current_user(authorization: str | None = Header(default=None)) -> str:
    token = authorization.removeprefix("Bearer ") if authorization else None
    return get_user_id_from_token(token)
