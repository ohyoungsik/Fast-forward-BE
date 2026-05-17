from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.app_log import AppLog

# 웹로그 m
def get_webapp_logs(
    db: Session,
    log_type: str | None,
    keyword: str | None,
    limit: int = 100,
) -> list[AppLog]:
    # app_logs 테이블에서 Web Application 로그 조회
    # log_type 필터: nginx_access / nginx_error / fastapi_error (없으면 전체)
    query = db.query(AppLog)

    if log_type:
        query = query.filter(AppLog.log_type == log_type)

    # keyword는 path, client_ip, status_code, message에 부분 일치 검색
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            AppLog.path.ilike(kw)
            | AppLog.client_ip.ilike(kw)
            | AppLog.status_code.ilike(kw)
            | AppLog.message.ilike(kw)
        )

    return query.order_by(desc(AppLog.collected_at)).limit(limit).all()


def create_app_log(db: Session, **kwargs) -> AppLog:
    # FastAPI 미들웨어 또는 Fluent Bit ingest에서 로그 한 건 저장
    kwargs.setdefault("collected_at", datetime.now(KST))
    log = AppLog(**kwargs)
    db.add(log)
    db.commit()
    return log
