from sqlalchemy import BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class SecurityAccessLog(Base):
    __tablename__ = "security_access_logs"

    id = Column(BigInteger, primary_key=True)
    server_name = Column(String(50))
    server_role = Column(String(50))
    log_type = Column(String(30), nullable=False)
    level = Column(String(10), nullable=False)
    user_id = Column(String(100))
    source_ip = Column(String(50))
    auth_method = Column(String(30))
    status = Column(String(50))
    source_path = Column(Text)
    message = Column(Text)
    parsed_data = Column(JSONB)
    collected_at = Column(DateTime)
