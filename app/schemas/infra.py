from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


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


class FluentBitRecord(BaseModel):
    """fluent-bit HTTP output 플러그인이 전송하는 레코드 한 건"""
    model_config = ConfigDict(extra="ignore")

    server_name: Optional[str] = None
    server_role: Optional[str] = None
    log_type: str
    level: Optional[str] = None
    user_id: Optional[str] = None
    source_ip: Optional[str] = None
    auth_method: Optional[str] = None
    status: Optional[str] = None
    source_path: Optional[str] = None
    message: Optional[str] = None
    parsed_data: Optional[dict] = None
    log: Optional[str] = None    # fluent-bit이 전송하는 auth.log 원문
    date: Optional[float] = None  # fluent-bit Unix timestamp (저장 안 함)


class SecurityAccessLogItem(BaseModel):
    id: int
    server_name: Optional[str] = None
    server_role: Optional[str] = None
    log_type: str
    level: str
    user_id: Optional[str] = None
    source_ip: Optional[str] = None
    auth_method: Optional[str] = None
    status: Optional[str] = None
    source_path: Optional[str] = None
    message: Optional[str] = None
    collected_at: str

    model_config = {"from_attributes": True}


class AppLogItem(BaseModel):
    id: int
    server_name: Optional[str] = None
    log_type: str
    level: str
    client_ip: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[str] = None
    response_time_ms: Optional[int] = None
    message: Optional[str] = None
    collected_at: str
