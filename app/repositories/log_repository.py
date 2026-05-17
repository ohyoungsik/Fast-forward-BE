from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

KST = ZoneInfo("Asia/Seoul")

from app.models.log import Log


def get_log(db: Session):
    return db.query(Log).all()


def create_nginx_log(db: Session, **kwargs) -> Log:
    kwargs.setdefault("create_time", datetime.now(KST))
    log = Log(**kwargs)
    db.add(log)
    db.commit()
    return log