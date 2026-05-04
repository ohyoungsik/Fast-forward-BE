from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from pydantic import ConfigDict

from app.db.base import Base


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    model_config = ConfigDict(from_attributes=True)