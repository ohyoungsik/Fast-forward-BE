from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class ServerInfo(Base):
    __tablename__ = "server_info"

    id = Column(Integer, primary_key=True)
    server_name = Column(String(50), unique=True, nullable=False)
    server_role = Column(String(50), nullable=False)
    private_ip = Column(String(50))
    public_ip = Column(String(50))
    created_at = Column(DateTime)
