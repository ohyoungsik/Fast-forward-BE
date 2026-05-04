from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def create_refresh_token(
    db: Session,
    *,
    user_id: int,
    refresh_token: str,
    expires_at: datetime,
) -> RefreshToken:
    rt = RefreshToken(
        user_id=user_id,
        refresh_token=refresh_token,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def get_refresh_token(db: Session, *, refresh_token: str) -> Optional[RefreshToken]:
    return db.query(RefreshToken).filter(RefreshToken.refresh_token == refresh_token).first()


def revoke_refresh_token(db: Session, *, refresh_token: str) -> bool:
    rt = get_refresh_token(db, refresh_token=refresh_token)
    if rt is None:
        return False
    if not rt.revoked:
        rt.revoked = True
        db.add(rt)
        db.commit()
        db.refresh(rt)
    return True

