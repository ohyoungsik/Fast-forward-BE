from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text

from app.db.base import Base


class AppLog(Base):
    __tablename__ = "app_logs"

    id = Column(BigInteger, primary_key=True)
    server_name = Column(String(50))
    log_type = Column(String(30), nullable=False)
    level = Column(String(10), nullable=False)
    client_ip = Column(String(50))
    method = Column(String(10))
    path = Column(Text)
    status_code = Column(String(10))
    response_time_ms = Column(Integer)
    message = Column(Text)
    collected_at = Column(DateTime)
