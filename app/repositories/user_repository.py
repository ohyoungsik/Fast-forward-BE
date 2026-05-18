from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.user import User

KST = ZoneInfo("Asia/Seoul")
_MAX_FAILURES = 5
_LOCK_MINUTES = 5


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, *, name: str, username: str, email: str, password_hash: str) -> User:
    user = User(name=name, username=username, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def record_failed_login(db: Session, user: User) -> User:
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= _MAX_FAILURES:
        user.locked_until = datetime.now(KST) + timedelta(minutes=_LOCK_MINUTES)
    db.commit()
    db.refresh(user)
    return user


def reset_login_attempts(db: Session, user: User) -> None:
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()

