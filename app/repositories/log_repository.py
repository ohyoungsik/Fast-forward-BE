from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import desc
from sqlalchemy.orm import Session

KST = ZoneInfo("Asia/Seoul")

from app.models.log import Log


def get_log(db: Session):
    return db.query(Log).all()


def get_nginx_logs_filtered(
    db: Session,
    log_type: str | None = None,
    keyword: str | None = None,
    limit: int = 200,
) -> list[Log]:
    query = db.query(Log)

    if log_type:
        query = query.filter(Log.log_type == log_type)

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            Log.client_ip.ilike(kw)
            | Log.request_path.ilike(kw)
            | Log.status_code.ilike(kw)
            | Log.message.ilike(kw)
        )

    return query.order_by(desc(Log.create_time)).limit(limit).all()


def create_nginx_log(db: Session, **kwargs) -> Log:
    kwargs.setdefault("create_time", datetime.now(KST))
    log = Log(**kwargs)
    db.add(log)
    db.commit()
    return log