from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class LogSchema(BaseModel):
    id: int
    # str 대신 Optional[str] = None 을 사용하여 null 허용
    client_ip: Optional[str] = None
    method: Optional[str] = None
    request_path: Optional[str] = None
    status_code: Optional[str] = None
    create_time: Optional[datetime] = None  # 이전 에러 해결책 포함
    message: Optional[str] = None
    # client_ip: str
    # method: str
    # request_path: str
    # status_code: str
    # create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class LogListResponse(BaseModel):
    payload: List[LogSchema]