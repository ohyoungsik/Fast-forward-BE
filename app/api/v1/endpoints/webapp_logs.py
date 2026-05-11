from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.app_log_repository import get_webapp_logs
from app.schemas.infra import AppLogItem

router = APIRouter()


@router.get("", response_model=list[AppLogItem])
def webapp_logs(
    log_type: str = Query(default=None),
    keyword: str = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    # GET /logs/webapp?log_type=fastapi_error&keyword=500&limit=100
    # app_logs 테이블에서 Web Application 로그 조회 후 프론트 표시용으로 변환
    logs = get_webapp_logs(db, log_type, keyword, limit)
    return [
        AppLogItem(
            id=log.id,
            server_name=log.server_name or "",
            log_type=log.log_type,
            level=log.level,
            client_ip=log.client_ip or "",
            method=log.method or "",
            path=log.path or "",
            status_code=log.status_code or "",
            response_time_ms=log.response_time_ms,
            message=log.message or "",
            collected_at=log.collected_at.strftime("%Y-%m-%d %H:%M:%S") if log.collected_at else "",
        )
        for log in logs
    ]
