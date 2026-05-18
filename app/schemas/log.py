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

    access 로그: log_type='nginx_access', remote/path/code 필드로 전달
    error  로그: log_type='nginx_error',  level/message 사용
    """
    model_config = ConfigDict(extra="ignore")

    log_type: str
    server_name: Optional[str] = None
    method: Optional[str] = None
    level: Optional[str] = None
    message: Optional[str] = None
    create_time: Optional[datetime] = None
    # fluent-bit access 로그 실제 필드명
    remote: Optional[str] = None       # client_ip
    path: Optional[str] = None         # request_path
    code: Optional[str] = None         # status_code