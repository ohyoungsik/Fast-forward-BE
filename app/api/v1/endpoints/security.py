from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.infra_repository import get_security_logs
from app.schemas.infra import SecurityLogItem

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
