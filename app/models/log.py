from sqlalchemy import Column, Integer, String, DateTime, Text
from pydantic import BaseModel, ConfigDict
from app.db.base import Base

class Log(Base):
    __tablename__ = "nginx_logs"
    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(String(10), nullable=True)      # 'access' | 'error'
    server_name = Column(String(50), nullable=True)
    client_ip = Column(String, nullable=True)
    method = Column(String, nullable=True)
    request_path = Column(String, nullable=True)
    status_code = Column(String, nullable=True)
    level = Column(String(10), nullable=True)          # error 로그용
    message = Column(Text, nullable=True)              # error 로그용
    create_time = Column(DateTime, nullable=True)

    model_config = ConfigDict(from_attributes=True)