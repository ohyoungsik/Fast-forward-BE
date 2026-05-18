import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.repositories.log_repository import create_nginx_log, get_log, get_nginx_logs_filtered
from app.schemas.infra import AppLogItem
from app.schemas.log import LogListResponse, NginxIngestRecord
from app.utils.common import resolve_server_name

router = APIRouter()

_CODE_TO_LEVEL = {"2": "INFO", "3": "INFO", "4": "WARN", "5": "ERROR"}


@router.get("", response_model=LogListResponse, summary="Logs")
async def get_logs(db: Session = Depends(get_db)) -> dict:
    data = get_log(db)
    return {"payload": data}


@router.get("/nginx", response_model=list[AppLogItem])
def get_nginx_logs(
    log_type: str = Query(default=None, description="'access' 또는 'error'"),
    keyword: str = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    # GET /logs/nginx?log_type=access&keyword=404&limit=100
    # nginx_logs 테이블에서 access/error 로그를 필터링해 반환
    logs = get_nginx_logs_filtered(db, log_type, keyword, limit)
    return [
        AppLogItem(
            id=log.id,
            server_name=log.server_name or "",
            log_type=log.log_type or "",
            level=log.level or "INFO",
            client_ip=log.client_ip or "",
            method=log.method or "",
            path=log.request_path or "",
            status_code=log.status_code or "",
            response_time_ms=None,
            message=log.message or "",
            collected_at=log.create_time.strftime("%Y-%m-%d %H:%M:%S") if log.create_time else "",
        )
        for log in logs
    ]


@router.post("/ingest", status_code=status.HTTP_204_NO_CONTENT)
def ingest_nginx_logs(
    records: list[NginxIngestRecord],
    db: Session = Depends(get_db),
):
    # POST /logs/ingest
    # fluent-bit HTTP output 플러그인에서 nginx access/error 로그를 배치로 수신
    # fluent-bit 필드 매핑: remote→client_ip, path→request_path, code→status_code
    for rec in records:
        try:
            level = rec.level or _CODE_TO_LEVEL.get((rec.code or "")[:1], "INFO")
            message = rec.message or f"[{level}] {rec.method} {rec.path} → {rec.code} | {rec.remote}"
            data = {
                "log_type":     rec.log_type,
                "server_name":  resolve_server_name(rec.server_name),
                "client_ip":    rec.remote,
                "method":       rec.method,
                "request_path": rec.path,
                "status_code":  rec.code,
                "level":        level,
                "message":      message,
                "create_time":  rec.create_time,
            }
            create_nginx_log(db, **data)
        except Exception as e:
            db.rollback()
            logger.error("nginx log insert 실패: %s | record: %s", e, rec.model_dump())
