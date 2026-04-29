from sqlalchemy.orm import Session

from app.models.log import Log


def get_log(db: Session):
    logdata = db.query(Log).all()
    print(' get _Log repo ', logdata)
    return logdata