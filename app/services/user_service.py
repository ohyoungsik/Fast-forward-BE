from sqlalchemy.orm import Session

from app.repositories import user_repository
from app.schemas.user import UserCreate, UserRead
from app.utils.common import get_password_hash


def create_user(db: Session, payload: UserCreate) -> UserRead:
    existing = user_repository.get_user_by_email(db, payload.email)
    if existing is not None:
        raise ValueError("Email already registered")
    hashed_password = get_password_hash(payload.password)
    user = user_repository.create_user(db, email=payload.email, hashed_password=hashed_password)
    return UserRead.model_validate(user)

