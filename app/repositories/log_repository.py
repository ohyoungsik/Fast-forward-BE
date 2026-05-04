from sqlalchemy.orm import Session

from app.models.log import Log


def get_log(db: Session):
    logdata = db.query(Log).all()
    return logdata