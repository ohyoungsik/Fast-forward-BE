from datetime import datetime

from sqlalchemy.orm import Session

from app.models.log import Log


def get_log(db: Session):
    return db.query(Log).all()


def create_nginx_log(db: Session, **kwargs) -> Log:
    kwargs.setdefault("create_time", datetime.utcnow())
    log = Log(**kwargs)
    db.add(log)
    db.commit()
    return log