from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ServerItem(BaseModel):
    server_name: str
    server_role: str

    model_config = {"from_attributes": True}


class MetricsLatestResponse(BaseModel):
    server_name: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_rx: float
    network_tx: float
    created_at: Optional[datetime]


class MetricsHistoryPoint(BaseModel):
    time: str
    cpu: float
    memory: float
    disk: float


class SecurityLogItem(BaseModel):
    id: int
    timestamp: str
    level: str
    ip: str
    status_code: str
    message: str
    service: str = "nginx"
