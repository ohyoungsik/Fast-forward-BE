from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String

from app.db.base import Base


class ServerMetrics(Base):
    __tablename__ = "server_metrics"

    id = Column(BigInteger, primary_key=True)
    server_id = Column(Integer, ForeignKey("server_info.id"), nullable=False)
    metric_type = Column(String(30), nullable=False)
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20))
    collected_at = Column(DateTime)
