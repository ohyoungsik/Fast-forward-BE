from datetime import datetime, timedelta, timezone

from pydantic import ConfigDict
from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.db.base import Base

_KST = timezone(timedelta(hours=9))


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_KST), nullable=False)
    failed_login_count = Column(Integer, default=0, nullable=False, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)

    model_config = ConfigDict(from_attributes=True)