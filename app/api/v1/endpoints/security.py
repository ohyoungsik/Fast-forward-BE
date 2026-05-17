from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.infra_repository import get_security_logs
from app.repositories.security_access_log_repository import (
    create_security_access_log,
    get_security_access_logs,
)
from app.schemas.infra import FluentBitRecord, SecurityAccessLogItem, SecurityLogItem
from app.utils.common import resolve_server_name

router = APIRouter()

# HTTP 상태코드 첫 자리로 로그 레벨 결정 (2xx/3xx → INFO, 4xx → WARN, 5xx → ERROR)
_LEVEL_MAP = {"2": "INFO", "3": "INFO", "4": "WARN", "5": "ERROR"}


@router.get("", response_model=list[SecurityLogItem])
def security_logs(
    server_name: str = Query(default=None),
    keyword: str = Query(default=None),
    db: Session = Depends(get_db),
):
    # GET /security/logs?server_name=nginx-fe-server&keyword=404
    # nginx_logs 테이블에서 로그를 조회한 뒤 프론트 표시용 형식으로 변환해 반환
    # keyword는 client_ip / request_path / status_code 부분 일치 검색에 사용
    logs = get_security_logs(db, server_name, keyword)
    result = []
    for log in logs:
        code = str(log.status_code or "")
        level = _LEVEL_MAP.get(code[:1], "INFO")
        # method가 있으면 "GET /path → 200" 형태, 없으면 request_path만 표시
        message = (
            f"{log.method} {log.request_path} → {log.status_code}"
            if log.method
            else log.request_path or ""
        )
        result.append(
            SecurityLogItem(
                id=log.id,
                timestamp=log.create_time.strftime("%Y-%m-%d %H:%M:%S") if log.create_time else "",
                level=level,
                ip=log.client_ip or "",
                status_code=code,
                message=message,
                service="nginx",
            )
        )
    return result


_STATUS_TO_LEVEL = {
    "failed": "WARN",
    "disconnected": "WARN",
    "success": "INFO",
    "session_opened": "INFO",
    "session_closed": "INFO",
    "sudo": "INFO",
}


def _resolve_level(level: str | None, rec_status: str | None) -> str:
    if level:
        return level
    return _STATUS_TO_LEVEL.get(rec_status or "", "INFO")


@router.post("/ingest", status_code=status.HTTP_204_NO_CONTENT)
def ingest_security_logs(
    records: list[FluentBitRecord],
    db: Session = Depends(get_db),
):
    # POST /security/logs/ingest
    # fluent-bit HTTP output 플러그인에서 security_access_logs 레코드를 배치로 수신
    # fluent-bit 설정 예시:
    #   [OUTPUT]
    #       Name  http
    #       Match security.*
    #       Host  <BE_HOST>
    #       Port  8000
    #       URI   /api/v1/security/logs/ingest
    #       Format json
    for rec in records:
        data = rec.model_dump()
        data["level"] = _resolve_level(rec.level, rec.status)
        data["server_name"] = resolve_server_name(data.get("server_name"))
        create_security_access_log(db, **data)


@router.get("/access", response_model=list[SecurityAccessLogItem])
def security_access_logs(
    server_name: str = Query(default=None),
    level: str = Query(default=None),
    status: str = Query(default=None),
    keyword: str = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    # GET /security/logs/access?server_name=public-bastion&level=WARN&limit=100
    # security_access_logs 테이블에서 SSH/sudo/세션 인증 로그 조회
    logs = get_security_access_logs(db, server_name, level, status, keyword, limit)
    return [
        SecurityAccessLogItem(
            id=log.id,
            server_name=log.server_name or "",
            server_role=log.server_role or "",
            log_type=log.log_type,
            level=log.level,
            user_id=log.user_id or "",
            source_ip=log.source_ip or "",
            auth_method=log.auth_method or "",
            status=log.status or "",
            source_path=log.source_path or "",
            message=log.message or "",
            collected_at=log.collected_at.strftime("%Y-%m-%d %H:%M:%S") if log.collected_at else "",
        )
        for log in logs
    ]
