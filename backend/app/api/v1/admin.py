from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_roles
from app.db.session import get_db
from app.models import Resource, User
from app.schemas.auth import ManagedUserCreate, User as UserResponse
from app.services.audit import record_event

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
def list_users(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[UserResponse]:
    return [UserResponse.model_validate(user) for user in db.scalars(select(User).order_by(User.created_at)).all()]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_managed_user(payload: ManagedUserCreate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> UserResponse:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    record_event(db, "managed_user_created", current_user.id, metadata={"email": email, "role": payload.role})
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/processing")
def processing_status(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict[str, object]:
    """Expose bounded document-worker state to authorized operators."""
    counts = {
        status: count
        for status, count in db.execute(
            select(Resource.processing_status, func.count(Resource.id)).group_by(Resource.processing_status)
        ).all()
    }
    oldest = db.scalar(select(func.min(Resource.processing_started_at)).where(Resource.processing_status == "processing"))
    return {"counts": counts, "oldest_processing_at": oldest.isoformat() if oldest else None}
