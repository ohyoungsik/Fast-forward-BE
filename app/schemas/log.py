from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class LogSchema(BaseModel):
    id: int
    log_type: Optional[str] = None
    server_name: Optional[str] = None
    client_ip: Optional[str] = None
    method: Optional[str] = None
    request_path: Optional[str] = None
    status_code: Optional[str] = None
    level: Optional[str] = None
    message: Optional[str] = None
    create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LogListResponse(BaseModel):
    payload: List[LogSchema]


class NginxIngestRecord(BaseModel):
    """fluent-bit HTTP output 플러그인이 전송하는 nginx 로그 레코드 한 건.

    access 로그: log_type='access', client_ip / method / request_path / status_code 사용
    error  로그: log_type='error',  level / message 사용
    """
    model_config = ConfigDict(extra="allow")

    log_type: str                          # 'access' | 'error'
    server_name: Optional[str] = None
    client_ip: Optional[str] = None
    method: Optional[str] = None
    request_path: Optional[str] = None
    status_code: Optional[str] = None
    level: Optional[str] = None
    message: Optional[str] = None
    create_time: Optional[datetime] = None
    log: Optional[str] = None    # fluent-bit 원본 로그 라인
    date: Optional[float] = None  # fluent-bit Unix timestamp (저장 안 함)