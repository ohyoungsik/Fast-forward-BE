from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel, ConfigDict
from app.db.base import Base

class Log(Base):	
    __tablename__ = "nginx_logs"
    id = Column(Integer, primary_key=True, index=True)
    client_ip = Column(String, nullable=True)
    method = Column(String, nullable=True)
    request_path = Column(String, nullable=True)
    status_code = Column(String, nullable=True)
    create_time = Column(DateTime, nullable=True)

    model_config = ConfigDict(from_attributes=True)