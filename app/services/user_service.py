from sqlalchemy.orm import Session

from app.repositories import user_repository
from app.schemas.user import UserCreate, UserRead
from app.utils.common import get_password_hash


def create_user(db: Session, payload: UserCreate) -> UserRead:
    existing_email = user_repository.get_user_by_email(db, payload.email)
    if existing_email is not None:
        raise ValueError("Email already registered")
    existing_username = user_repository.get_user_by_username(db, payload.username)
    if existing_username is not None:
        raise ValueError("Username already registered")
    hashed_password = get_password_hash(payload.password)
    user = user_repository.create_user(
        db,
        name=payload.name,
        username=payload.username,
        email=payload.email,
        password_hash=hashed_password,
    )
    return UserRead.model_validate(user)

