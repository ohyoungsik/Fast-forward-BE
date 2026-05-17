from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import desc

KST = ZoneInfo("Asia/Seoul")
from sqlalchemy.orm import Session

from app.models.security_access_log import SecurityAccessLog


def create_security_access_log(db: Session, **kwargs) -> SecurityAccessLog:
    kwargs.setdefault("collected_at", datetime.now(KST))
    log = SecurityAccessLog(**kwargs)
    db.add(log)
    db.commit()
    return log


def get_security_access_logs(
    db: Session,
    server_name: str | None = None,
    level: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    limit: int = 100,
) -> list[SecurityAccessLog]:
    query = db.query(SecurityAccessLog)

    if server_name:
        query = query.filter(SecurityAccessLog.server_name == server_name)
    if level:
        query = query.filter(SecurityAccessLog.level == level)
    if status:
        query = query.filter(SecurityAccessLog.status == status)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            SecurityAccessLog.message.ilike(kw)
            | SecurityAccessLog.source_ip.ilike(kw)
            | SecurityAccessLog.user_id.ilike(kw)
        )

    return query.order_by(desc(SecurityAccessLog.collected_at)).limit(limit).all()
