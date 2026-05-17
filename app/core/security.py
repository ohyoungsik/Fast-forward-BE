from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from jose import JWTError, jwt

from app.core.config import settings

KST = ZoneInfo("Asia/Seoul")


def create_access_token(*, username: str, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": username,
        "userId": user_id,
        "type": "access",
        "exp": datetime.now(KST) + expires_delta,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(*, username: str, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES_REFRESH)
    to_encode = {
        "sub": username,
        "userId": user_id,
        "type": "refresh",
        "exp": datetime.now(KST) + expires_delta,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise

